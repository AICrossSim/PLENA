import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
import torch.nn as nn
import torch.nn.functional as F
from compiler.asm_templates import projection_asm, preload_act_asm, reset_reg_asm, preload_addr_reg_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim


class CausalConv3d(nn.Conv3d):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._padding = (
            self.padding[2], self.padding[2],
            self.padding[1], self.padding[1],
            2 * self.padding[0], 0
        )
        self.padding = (0, 0, 0)

    def forward(self, x, cache_x=None):
        padding = list(self._padding)
        x = F.pad(x, padding)
        return super().forward(x)


def im2col_3d(input_tensor, kernel_size, stride=1, dilation=1):
    B, C_in, T, H, W = input_tensor.shape
    
    if isinstance(kernel_size, int):
        kernel_size = (kernel_size, kernel_size, kernel_size)
    if isinstance(stride, int):
        stride = (stride, stride, stride)
    if isinstance(dilation, int):
        dilation = (dilation, dilation, dilation)
    
    K_t, K_h, K_w = kernel_size
    S_t, S_h, S_w = stride
    D_t, D_h, D_w = dilation
    
    K_t_eff = D_t * (K_t - 1) + 1
    K_h_eff = D_h * (K_h - 1) + 1
    K_w_eff = D_w * (K_w - 1) + 1
    
    T_out = (T - K_t_eff) // S_t + 1
    H_out = (H - K_h_eff) // S_h + 1
    W_out = (W - K_w_eff) // S_w + 1
    
    patches = input_tensor.unfold(2, K_t_eff, S_t)
    patches = patches.unfold(3, K_h_eff, S_h)
    patches = patches.unfold(4, K_w_eff, S_w)
    
    if D_t > 1 or D_h > 1 or D_w > 1:
        patches = patches[:, :, :, :, :, ::D_t, ::D_h, ::D_w]
    
    patches = patches.contiguous().view(B, C_in, T_out, H_out, W_out, K_t * K_h * K_w)
    patches = patches.permute(0, 1, 5, 2, 3, 4)
    patches = patches.contiguous().view(B, C_in * K_t * K_h * K_w, T_out * H_out * W_out)
    
    return patches, (T_out, H_out, W_out)


def conv3d_as_gemm(input_tensor, weight, kernel_size, stride=1, dilation=1):
    B, C_in, T, H, W = input_tensor.shape
    C_out = weight.shape[0]
    
    if isinstance(kernel_size, int):
        kernel_size = (kernel_size, kernel_size, kernel_size)
    
    col, (T_out, H_out, W_out) = im2col_3d(input_tensor, kernel_size, stride, dilation)
    weight_reshaped = weight.view(C_out, -1)
    
    output = torch.zeros(B, C_out, T_out * H_out * W_out)
    for b in range(B):
        output[b] = weight_reshaped @ col[b]
    
    output = output.view(B, C_out, T_out, H_out, W_out)
    
    return output, col, weight_reshaped


def align_to(addr, alignment=64):
    """对齐地址到指定边界"""
    return ((addr + alignment - 1) // alignment) * alignment


if __name__ == "__main__":
    
    # ==================== 配置 ====================
    MLEN = 64
    BLEN = 4
    VLEN = 64
    
    # Conv3D 参数
    batch_size = 1
    in_channels = 16
    out_channels = 32
    kernel_size = (3, 3, 3)
    stride_conv = (1, 1, 1)
    T, H, W = 5, 8, 8
    
    K = in_channels * kernel_size[0] * kernel_size[1] * kernel_size[2]  # 432
    
    # ==================== 生成测试数据 ====================
    torch.manual_seed(42)
    
    input_tensor = torch.randn(batch_size, in_channels, T, H, W)
    
    causal_conv = CausalConv3d(
        in_channels=in_channels,
        out_channels=out_channels,
        kernel_size=kernel_size,
        stride=stride_conv,
        padding=(1, 1, 1),
        bias=False
    )
    
    weights = causal_conv.weight.data
    original_output = causal_conv(input_tensor)
    
    # ==================== 转换为 GEMM ====================
    padded_input = F.pad(input_tensor, causal_conv._padding)
    gemm_output, col_matrix, weight_matrix = conv3d_as_gemm(
        padded_input, weights, kernel_size, stride_conv
    )
    
    N = col_matrix.shape[2]
    C_out = out_channels
    
    print(f"K = {K}, C_out = {C_out}, N = {N}")
    
    # ==================== 准备数据 ====================
    test_n = BLEN  # 4
    
    act_full = col_matrix.squeeze(0).t()  # (N, K)
    act_test = act_full[:test_n, :]  # (4, K)
    
    K_padded = ((K + MLEN - 1) // MLEN) * MLEN  # 448
    C_out_padded = ((C_out + MLEN - 1) // MLEN) * MLEN  # 64
    
    act_padded = torch.zeros(test_n, K_padded)
    act_padded[:, :K] = act_test
    
    weight_raw = weight_matrix.t()  # (K, C_out)
    weight_padded = torch.zeros(K_padded, C_out_padded)
    weight_padded[:K, :C_out] = weight_raw
    
    print(f"act_padded shape: {act_padded.shape}")
    print(f"weight_padded shape: {weight_padded.shape}")
    
    expected = act_padded @ weight_padded
    print(f"Expected output shape: {expected.shape}")
    print(f"Expected[0, :8]: {expected[0, :8]}")
    
    input_data = {
        "act_tensor": act_padded,
        "weights": weight_padded,
    }
    
    golden_result = {
        "input_tensor": input_data,
        "original_output": expected
    }
    
    # ==================== 计算 HBM 布局 ====================
    hidden_size = K_padded  # 448
    output_size = C_out_padded  # 64
    batch = test_n  # 4
    
    real_data_ratio = (8*8 + 8) / (8 * 8)  # 1.125
    
    # 计算 activation 在 HBM 中的大小
    act_hbm_size_raw = int(hidden_size * batch * real_data_ratio)
    
    # **关键修复：对齐到 64**
    act_hbm_size = ((act_hbm_size_raw + 63) // 64) * 64
    weight_hbm_offset = act_hbm_size
    
    print(f"\nhidden_size (K_padded): {hidden_size}")
    print(f"output_size (C_out_padded): {output_size}")
    print(f"act_hbm_size_raw: {act_hbm_size_raw}")
    print(f"act_hbm_size (aligned): {act_hbm_size}")
    print(f"weight_hbm_offset: {weight_hbm_offset}")
    
    # ==================== 生成汇编代码 ====================
    gen_asm = "; Conv3D as GEMM Test \n"
    
    # 设置地址寄存器
    gen_asm += "; Preload Addr Reg Generation \n"
    gen_asm += f"S_ADDI_INT gp1, gp0, {weight_hbm_offset} \n"
    gen_asm += "C_SET_ADDR_REG a1, gp0, gp1 \n"
    
    # Reset
    gen_asm += "; Reset Registers \n"
    gen_asm += "S_ADDI_INT gp1, gp0, 0 \n"
    gen_asm += "S_ADDI_INT gp2, gp0, 0 \n"
    gen_asm += "S_ADDI_INT gp3, gp0, 0 \n"
    
    # Preload Activation
    gen_asm += "; Preload Activation \n"
    gen_asm += f"S_ADDI_INT gp1, gp0, {hidden_size * batch} \n"
    gen_asm += "C_SET_SCALE_REG gp1 \n"
    gen_asm += "S_ADDI_INT gp1, gp0, 0 \n"
    gen_asm += "S_ADDI_INT gp3, gp0, 0 \n"
    gen_asm += f"S_ADDI_INT gp2, gp0, {hidden_size} \n"
    gen_asm += "C_SET_STRIDE_REG gp2 \n"
    
    K_tiles = hidden_size // MLEN  # 7
    gen_asm += f"C_LOOP_START gp4, {K_tiles} \n"
    gen_asm += "S_ADDI_INT gp2, gp1, 0 \n"
    gen_asm += "H_PREFETCH_V gp3, gp2, a0, 1, 0 \n"
    gen_asm += f"S_ADDI_INT gp3, gp3, {VLEN * BLEN} \n"
    gen_asm += f"S_ADDI_INT gp1, gp1, {VLEN} \n"
    gen_asm += "C_LOOP_END gp4 \n"
    
    # Reset
    gen_asm += "; Reset Registers \n"
    gen_asm += "S_ADDI_INT gp1, gp0, 0 \n"
    gen_asm += "S_ADDI_INT gp2, gp0, 0 \n"
    gen_asm += "S_ADDI_INT gp3, gp0, 0 \n"
    gen_asm += "S_ADDI_INT gp4, gp0, 0 \n"
    
    # Projection
    gen_asm += "; Projection \n"
    weight_scale = hidden_size * output_size
    gen_asm += f"S_ADDI_INT gp4, gp0, {weight_scale} \n"
    gen_asm += "C_SET_SCALE_REG gp4 \n"
    gen_asm += f"S_ADDI_INT gp4, gp0, {output_size} \n"
    gen_asm += "C_SET_STRIDE_REG gp4 \n"
    gen_asm += "S_ADDI_INT gp4, gp0, 0 \n"
    gen_asm += "S_ADDI_INT gp2, gp0, 0 \n"
    gen_asm += "S_ADDI_INT gp3, gp0, 0 \n"
    
    # 加载 weight tiles
    weight_tile_size = MLEN * MLEN
    hbm_row_stride = MLEN * output_size
    
    for k in range(K_tiles):
        gen_asm += f"H_PREFETCH_M gp2, gp3, a1, 1, 0 \n"
        if k < K_tiles - 1:
            gen_asm += f"S_ADDI_INT gp3, gp3, {hbm_row_stride} \n"
            gen_asm += f"S_ADDI_INT gp2, gp2, {weight_tile_size} \n"
    
    # MM
    gen_asm += "; Matrix Multiply \n"
    gen_asm += "S_ADDI_INT gp2, gp0, 0 \n"
    gen_asm += "S_ADDI_INT gp4, gp0, 0 \n"
    
    for k in range(K_tiles):
        gen_asm += f"M_MM 0, gp2, gp4 \n"
        if k < K_tiles - 1:
            gen_asm += f"S_ADDI_INT gp2, gp2, {weight_tile_size} \n"
            gen_asm += f"S_ADDI_INT gp4, gp4, {VLEN * BLEN} \n"
    
    # Write output
    gen_asm += "; Write Output \n"
    output_offset = hidden_size * batch
    gen_asm += f"S_ADDI_INT gp1, gp0, {output_offset} \n"
    gen_asm += "M_MM_WO 1, gp0, 0 \n"
    
    print("\n========== Assembly ==========")
    print(gen_asm)
    
    # ==================== 保存和仿真 ====================
    fp_preload = [0.0, 1e-6, 1/hidden_size]
    
    with open("conv3d_gemm.asm", "w") as f:
        f.write(gen_asm)
    
    create_sim_env(input_data, gen_asm, golden_result, fp_preload)
    create_mem_for_sim(
        data_size=256,
        mode="behave_sim",
        asm="conv3d_gemm",
        data=None,
        specified_data_order=["act_tensor", "weights"]
    )
    
    print(f"\nExpected output: {expected[0, :8]}")