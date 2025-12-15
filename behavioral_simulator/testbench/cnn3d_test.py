import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import nn
import torch.nn.functional as F
from compiler.asm_templates import projection_asm, preload_act_asm, reset_reg_asm, preload_addr_reg_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim


def pad64(x):
    return ((x + 63) // 64) * 64


def im2col_3d(input_tensor, kernel_size, stride=1, padding=0):
    """
    3D im2col: 将3D卷积转换为矩阵乘法
    
    Args:
        input_tensor: (batch, Cin, D, H, W)
        kernel_size: (kD, kH, kW) 或 int
        stride: (sD, sH, sW) 或 int
        padding: (pD, pH, pW) 或 int
    
    Returns:
        col: (batch, Cin * kD * kH * kW, D_out * H_out * W_out)
    """
    if isinstance(kernel_size, int):
        kernel_size = (kernel_size, kernel_size, kernel_size)
    if isinstance(stride, int):
        stride = (stride, stride, stride)
    if isinstance(padding, int):
        padding = (padding, padding, padding)
    
    batch, Cin, D, H, W = input_tensor.shape
    kD, kH, kW = kernel_size
    sD, sH, sW = stride
    pD, pH, pW = padding
    
    # 添加padding
    if any(p > 0 for p in padding):
        input_tensor = F.pad(input_tensor, (pW, pW, pH, pH, pD, pD))
    
    _, _, D_padded, H_padded, W_padded = input_tensor.shape
    
    # 计算输出尺寸
    D_out = (D_padded - kD) // sD + 1
    H_out = (H_padded - kH) // sH + 1
    W_out = (W_padded - kW) // sW + 1
    
    # 使用unfold展开
    # unfold顺序: D -> H -> W
    col = input_tensor.unfold(2, kD, sD)  # (batch, Cin, D_out, H, W, kD)
    col = col.unfold(3, kH, sH)            # (batch, Cin, D_out, H_out, W, kD, kH)
    col = col.unfold(4, kW, sW)            # (batch, Cin, D_out, H_out, W_out, kD, kH, kW)
    
    # 重排为 (batch, Cin * kD * kH * kW, D_out * H_out * W_out)
    col = col.permute(0, 1, 5, 6, 7, 2, 3, 4).contiguous()
    col = col.view(batch, Cin * kD * kH * kW, D_out * H_out * W_out)
    
    return col, (D_out, H_out, W_out)


def col2im_3d_output(col_output, batch, Cout, D_out, H_out, W_out):
    """
    将矩阵乘法输出转回3D特征图格式
    
    Args:
        col_output: (batch, Cout, D_out * H_out * W_out)
    
    Returns:
        output: (batch, Cout, D_out, H_out, W_out)
    """
    return col_output.view(batch, Cout, D_out, H_out, W_out)


def prepare_conv3d_weights(weight):
    """
    准备3D卷积权重用于矩阵乘法
    
    Args:
        weight: (Cout, Cin, kD, kH, kW)
    
    Returns:
        weight_matrix: (Cin * kD * kH * kW, Cout)
    """
    Cout, Cin, kD, kH, kW = weight.shape
    # 展平为 (Cout, Cin * kD * kH * kW)
    weight_flat = weight.view(Cout, -1)
    # 转置为 (Cin * kD * kH * kW, Cout) 以匹配 im2col 输出
    return weight_flat.t()


if __name__ == "__main__":
    # =============================================
    # 3D CNN 参数配置
    # =============================================
    # 输入参数
    batch_size = 1
    Cin = 1          # 输入通道数
    D, H, W = 4, 4, 4  # 输入空间维度
    
    # 卷积参数
    Cout = 2        # 输出通道数
    kD, kH, kW = 3, 3, 3  # 卷积核大小
    stride = 1
    padding = 1
    
    real_data_ratio = (8*8 + 8) / (8 * 8)
    
    torch.manual_seed(42)

    # =============================================
    # 使用PyTorch原生3D卷积作为参考
    # =============================================
    input_tensor = torch.randn(batch_size, Cin, D, H, W)
    conv3d_layer = nn.Conv3d(Cin, Cout, (kD, kH, kW), stride=stride, padding=padding, bias=False)
    
    original_output = conv3d_layer(input_tensor)
    print("=" * 60)
    print("3D CNN Test Configuration")
    print("=" * 60)
    print(f"Input shape: ({batch_size}, {Cin}, {D}, {H}, {W})")
    print(f"Kernel size: ({kD}, {kH}, {kW})")
    print(f"Stride: {stride}, Padding: {padding}")
    print(f"Output channels: {Cout}")
    print(f"Original output shape: {original_output.shape}")
    
    # =============================================
    # im2col 转换
    # =============================================
    # 对输入进行im2col
    col, (D_out, H_out, W_out) = im2col_3d(input_tensor, (kD, kH, kW), stride, padding)
    print(f"\nAfter im2col:")
    print(f"  col shape: {col.shape}")  # (batch, Cin*kD*kH*kW, D_out*H_out*W_out)
    print(f"  Output spatial dims: D_out={D_out}, H_out={H_out}, W_out={W_out}")
    
    # 准备权重矩阵
    weight_matrix = prepare_conv3d_weights(conv3d_layer.weight.data)
    print(f"  Weight matrix shape: {weight_matrix.shape}")  # (Cin*kD*kH*kW, Cout)
    assert weight_matrix.shape == (Cin * kD * kH * kW, Cout)
    
    # =============================================
    # 验证im2col正确性 (CPU矩阵乘法)
    # =============================================
    # 对每个batch进行矩阵乘法: col[b] @ weight_matrix
    # col[b]: (Cin*kD*kH*kW, D_out*H_out*W_out).T @ (Cin*kD*kH*kW, Cout)
    # 即: (D_out*H_out*W_out, Cin*kD*kH*kW) @ (Cin*kD*kH*kW, Cout) = (D_out*H_out*W_out, Cout)
    
    col_output_list = []
    for b in range(batch_size):
        # col[b]: (Cin*kD*kH*kW, D_out*H_out*W_out)
        # 需要转置为 (D_out*H_out*W_out, Cin*kD*kH*kW)
        col_b = col[b].t()  # (D_out*H_out*W_out, Cin*kD*kH*kW)
        out_b = col_b @ weight_matrix  # (D_out*H_out*W_out, Cout)
        col_output_list.append(out_b)
    
    col_output = torch.stack(col_output_list, dim=0)  # (batch, D_out*H_out*W_out, Cout)
    col_output = col_output.permute(0, 2, 1)  # (batch, Cout, D_out*H_out*W_out)
    
    # 转回3D格式
    reconstructed_output = col2im_3d_output(col_output, batch_size, Cout, D_out, H_out, W_out)
    
    # 验证
    diff = (original_output - reconstructed_output).abs().max()
    print(f"\nVerification (CPU im2col vs PyTorch Conv3d):")
    print(f"  Max absolute difference: {diff.item():.2e}")
    assert diff < 1e-5, "im2col verification failed!"
    print("  ✓ im2col verification passed!")
    
    # =============================================
    # 准备硬件模拟器的数据
    # =============================================
    # 矩阵乘法维度:
    # 激活矩阵: (batch * D_out * H_out * W_out, Cin * kD * kH * kW)
    # 权重矩阵: (Cin * kD * kH * kW, Cout)
    # 输出矩阵: (batch * D_out * H_out * W_out, Cout)
    
    # 将所有batch的col拼接
    # col: (batch, Cin*kD*kH*kW, D_out*H_out*W_out)
    # 转换为: (batch * D_out*H_out*W_out, Cin*kD*kH*kW)
    
    spatial_size = D_out * H_out * W_out
    in_features = Cin * kD * kH * kW
    out_features = Cout
    total_batch = batch_size * spatial_size
    
    # 重组激活矩阵
    act_tensor = col.permute(0, 2, 1).contiguous()  # (batch, D_out*H_out*W_out, Cin*kD*kH*kW)
    act_tensor = act_tensor.view(total_batch, in_features)  # (batch*spatial, in_features)
    
    print(f"\nMatrix multiplication dimensions:")
    print(f"  Activation: ({total_batch}, {in_features})")
    print(f"  Weights: ({in_features}, {out_features})")
    print(f"  Output: ({total_batch}, {out_features})")
    
    # =============================================
    # Padding to satisfy hardware requirements
    # =============================================
    batch_pad = total_batch  # 不对batch维度padding
    in_pad = pad64(in_features)
    out_pad = pad64(out_features)
    
    fp_preload = [0.0, 1e-6, 1 / in_pad]
    
    print("batch_pad:", batch_pad)
    print("in_pad:", in_pad)
    print("out_pad:", out_pad)
    
    # Pad weights
    # weight_matrix: (in_features, out_features)
    # W_pad 需要是 (in_pad, out_pad) 给模拟器用
    # 但计算 golden output 时需要 (in_pad, out_pad)

    W_pad = torch.zeros(out_pad, in_pad, dtype=weight_matrix.dtype)
    W_pad[:out_features, :in_features] = weight_matrix.t()  # weight_matrix 已经是 (in, out)

    W_pad = W_pad.t()  # 转置为 (in_pad, out_pad)
    # Pad activations
    act_tensor_pad = torch.zeros(batch_pad, in_pad, dtype=act_tensor.dtype)
    act_tensor_pad[:total_batch, :in_features] = act_tensor

    # 直接用padded矩阵计算期望输出
    # act_tensor_pad: (batch_pad, in_pad)
    # W_pad: (in_pad, out_pad)
    # original_output_pad = act_tensor_pad @ W_pad  # (batch_pad, out_pad)

    # W_pad 已经是 (in_pad, out_pad)，不需要再转置了
    # assert original_output_pad.shape == (batch_pad, out_pad)
    
    # original_output_pad = torch.zeros(batch_pad, out_pad, dtype=original_output.dtype)
    # original_output_pad[:total_batch, :out_features] = original_output.view(-1, out_features)
    
    # 直接用 padded 矩阵乘法结果作为 golden
    original_output_pad = act_tensor_pad @ W_pad  # (batch_pad, out_pad)
    
    # Transpose for simulator (expects in, out)
    # W_pad = W_pad.t()  # (in_pad, out_pad)
    
    assert W_pad.shape == (in_pad, out_pad)
    assert act_tensor_pad.shape == (batch_pad, in_pad)
    
    print(f"\nPadded dimensions:")
    print(f"  Padded act shape: {act_tensor_pad.shape}")
    print(f"  Padded weight shape: {W_pad.shape}")
    
    
    # 验证 padded 矩阵乘法
    cpu_result_pad = act_tensor_pad @ W_pad  # (batch_pad, out_pad)

    # 提取有效部分
    cpu_result = cpu_result_pad[:total_batch, :out_features]

    # 与 golden 比较
    original_output_flat = original_output.permute(0, 2, 3, 4, 1).contiguous().view(-1, out_features)
    diff = (cpu_result - original_output_flat).abs().max()
    diff2 = (cpu_result_pad - original_output_pad).abs().max()
    print(f"CPU padded matmul vs golden diff: {diff.item():.2e}")
    print(f"CPU full padded matmul vs padded golden diff: {diff2.item():.2e}")
    
    assert diff < 1e-5, "Padded matmul verification failed!"
    assert diff2 < 1e-5, "Full padded matmul verification failed!"
    # sys.exit(0)
    
    
    # =============================================
    # 构建模拟器输入
    # =============================================
    input_tensor_sim = {
        "act_tensor": act_tensor_pad,
        "weights": W_pad,
    }
    
    golden_result = {
        "input_tensor": input_tensor_sim,
        "original_output": original_output_pad,
    }
    
    print("original_output_pad shape:", original_output_pad.shape)
    print("original_output_pad is:\n", original_output_pad)
    # sys.exit(0)
    
    # =============================================
    # HBM Layout
    # =============================================
    def align64(x): 
        return ((x + 63) // 64) * 64
    
    act_hbm_size = int(in_pad * batch_pad * real_data_ratio)
    weight_bytes = W_pad.numel()
    
    act_hbm_size = align64(act_hbm_size)
    weight_hbm_size = align64(weight_bytes)
    
    weight_hbm_offset = act_hbm_size
    weight_hbm_end = int((in_pad * batch_pad + in_pad * out_pad) * real_data_ratio)
    
    # =============================================
    # 构建汇编代码
    # =============================================
    gen_assembly_code = "; 3D CNN Test (im2col + matmul)\n"
    gen_assembly_code += f"; ORIGINAL INPUT: ({batch_size}, {Cin}, {D}, {H}, {W})\n"
    gen_assembly_code += f"; KERNEL: ({Cout}, {Cin}, {kD}, {kH}, {kW})\n"
    gen_assembly_code += f"; OUTPUT: ({batch_size}, {Cout}, {D_out}, {H_out}, {W_out})\n"
    gen_assembly_code += f"; MATMUL: ({total_batch},{in_features}) @ ({in_features},{out_features})\n"
    gen_assembly_code += f"; PADDED: ({batch_pad},{in_pad}) @ ({in_pad},{out_pad})\n\n"
    
    # Set HBM weight pointer
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1, 2],
        available_registers=[1, 2],
        addr_reg_val=[weight_hbm_offset, weight_hbm_end],
    )
    
    gen_assembly_code += reset_reg_asm([1, 2, 3])
    
    # Preload activation
    gen_assembly_code += preload_act_asm(
        vlen=64,
        preload_len=4,
        batch=batch_pad,
        hidden_size=in_pad,
        alive_registers=[1, 2, 3, 4, 5],
        act_vram_offset=0,
        activation_offset_reg=0,
        stride_size=in_pad,
    )
    
    gen_assembly_code += reset_reg_asm([1, 2, 3, 4])
    
    # Result buffer offset
    result_vram_offset = in_pad * batch_pad
    
    # Projection kernel
    gen_assembly_code += projection_asm(
        mlen=64,
        blen=4,
        batch=batch_pad,
        hidden_size=in_pad,
        out_features=out_pad,
        alive_registers=[1, 2, 3, 4, 5],
        w_base_hbm_offset_reg=1,
        activation_base_address=0,
        result_base_address=result_vram_offset,
        rope_enabled=False,
    )
    
    # sys.exit(0)
    
    # =============================================
    # 创建模拟环境
    # =============================================
    create_sim_env(input_tensor_sim, gen_assembly_code, golden_result, fp_preload)
    
    total_bytes = act_hbm_size + weight_hbm_size
    create_mem_for_sim(
        data_size=total_bytes,
        mode="behave_sim",
        asm="conv3d",
        data=None,
        specified_data_order=["act_tensor", "weights"],
    )
    
    # =============================================
    # 保存比较参数
    # =============================================
    result_start_row = result_vram_offset // 64
    num_result_rows = (batch_pad * out_pad) // 64
    
    comparison_params = {
        "start_row_idx": result_start_row,
        "num_rows": num_result_rows,
        "num_batches": batch_pad,
        "elements_per_batch": out_pad,
        # 3D CNN specific info for reconstruction
        "conv3d_info": {
            "batch_size": batch_size,
            "Cin": Cin,
            "Cout": Cout,
            "D": D, "H": H, "W": W,
            "D_out": D_out, "H_out": H_out, "W_out": W_out,
            "kD": kD, "kH": kH, "kW": kW,
            "stride": stride,
            "padding": padding,
        }
    }
    
    build_dir = Path(__file__).parent / "build"
    build_dir.mkdir(exist_ok=True)
    
    import json
    with open(build_dir / "comparison_params.json", "w") as f:
        json.dump(comparison_params, f, indent=2)
    
    with open("behavioral_simulator/testbench/conv3d_test.asm", "w") as f:
        f.write(gen_assembly_code)
    
    print("\n" + "=" * 60)
    print(" 3D CNN Assembly ready.")
    print(f" Input: ({batch_size}, {Cin}, {D}, {H}, {W})")
    print(f" Kernel: ({Cout}, {Cin}, {kD}, {kH}, {kW})")
    print(f" Output: ({batch_size}, {Cout}, {D_out}, {H_out}, {W_out})")
    print(f" Padded matmul: ({batch_pad},{in_pad}) @ ({in_pad},{out_pad})")
    print(f" HBM allocated: {total_bytes} bytes")
    print(f" Result rows: {num_result_rows}")
    print("=" * 60)