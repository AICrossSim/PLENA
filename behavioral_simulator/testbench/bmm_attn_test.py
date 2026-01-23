"""
Test M_BTMM/M_BMM_WO for QK^T computation with head_dim=HLEN=16.

This test validates the batch matrix multiply instructions for attention
with the correct hardware-matching dimensions:
- head_dim = HLEN = 16
- num_q_heads = MLEN // HLEN = 4 (processed in parallel)
- num_kv_heads = 1 (GQA style)
- seq_len = MLEN = 64
"""

import sys
import math
import torch
import torch.nn.functional as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tools"))

from compiler.asm_templates import preload_act_asm, reset_reg_asm, preload_addr_reg_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim
from quant.quantizer.hardware_quantizer.mxfp import _mx_fp_quantize_hardware

# Hardware parameters
MLEN = 64
HLEN = 16
BLEN = 4
VLEN = 64

# GQA configuration matching M_BMM
batch = 1
seq_len = MLEN  # 64
num_q_heads = MLEN // HLEN  # 4
num_kv_heads = 1
head_dim = HLEN  # 16


def quantize_to_mxfp(tensor):
    """Quantize to MXFP format."""
    orig_shape = tensor.shape
    # Reshape to 2D for quantization
    tensor_2d = tensor.reshape(-1, tensor.shape[-1])
    bm_x, _, _, _ = _mx_fp_quantize_hardware(
        tensor_2d, width=8, exponent_width=4, exponent_bias_width=8, block_size=[8]
    )
    return bm_x.reshape(orig_shape)


def generate_bmm_attn_asm(
    q_base_address: int,
    k_hbm_offset_reg: int,
    s_base_address: int,
    alive_registers: list,
):
    """
    Generate assembly for QK^T using M_BTMM.

    M_BTMM computes: Q @ K^T where
    - Q: [MLEN//HLEN, MLEN, HLEN] = [4, 64, 16] in Vector SRAM
    - K: [HLEN, MLEN] = [16, 64] in Matrix SRAM (loaded from HBM)
    - Output: [MLEN//HLEN, MLEN, MLEN] = [4, 64, 64]
    """
    q_reg = alive_registers[0]
    k_reg = alive_registers[1]
    s_reg = alive_registers[2]

    code = "; QK^T using M_BTMM\n"

    # Load Q base address in Vector SRAM
    code += f"S_ADDI_INT gp{q_reg}, gp0, {q_base_address}\n"

    # Load K from HBM to Matrix SRAM
    # K is [HLEN, MLEN] = [16, 64] for 1 KV head
    code += f"S_ADDI_INT gp{k_reg}, gp0, 0\n"
    code += f"H_PREFETCH_M gp0, gp{k_reg}, a{k_hbm_offset_reg}, 1, 1\n"

    # Perform batch transposed matrix multiply
    # M_BTMM 0, rs1(Q in VSRAM), rs2(K in MSRAM)
    code += f"M_BTMM 0, gp{q_reg}, gp{k_reg}\n"

    # Write output to Vector SRAM
    code += f"S_ADDI_INT gp{s_reg}, gp0, {s_base_address}\n"
    code += f"M_BMM_WO gp{s_reg}, 0\n"

    return code


if __name__ == "__main__":
    print("=" * 60)
    print("M_BTMM/M_BMM_WO Attention Test")
    print("=" * 60)
    print(f"Hardware: MLEN={MLEN}, HLEN={HLEN}, BLEN={BLEN}")
    print(f"Config: batch={batch}, seq_len={seq_len}, num_q_heads={num_q_heads}, "
          f"num_kv_heads={num_kv_heads}, head_dim={head_dim}")

    # Set seed for reproducibility
    torch.manual_seed(42)

    # Generate test data
    # Q: [batch, num_q_heads, seq_len, head_dim] = [1, 4, 64, 16]
    Q_orig = torch.randn(batch, num_q_heads, seq_len, head_dim, dtype=torch.bfloat16)
    # K: [batch, num_kv_heads, seq_len, head_dim] = [1, 1, 64, 16]
    K_orig = torch.randn(batch, num_kv_heads, seq_len, head_dim, dtype=torch.bfloat16)

    # Quantize to MXFP
    Q_mxfp = quantize_to_mxfp(Q_orig).to(torch.bfloat16)
    K_mxfp = quantize_to_mxfp(K_orig).to(torch.bfloat16)

    # Flatten for storage:
    # Q in VSRAM: [num_q_heads, seq_len, head_dim] = [4, 64, 16] -> flatten to [4*64*16] = [4096]
    Q_flat = Q_mxfp.squeeze(0).reshape(-1)  # [4096]
    # K in HBM: [seq_len, head_dim] = [64, 16] for 1 KV head -> [1024]
    K_flat = K_mxfp.squeeze(0).squeeze(0).reshape(-1)  # [1024]

    print(f"\nQ_flat shape: {Q_flat.shape}")  # [4096]
    print(f"K_flat shape: {K_flat.shape}")  # [1024]

    # Compute golden output
    # Expand K to match Q heads for broadcast
    K_expanded = K_mxfp.expand(batch, num_q_heads, seq_len, head_dim)

    # Q @ K^T -> [batch, num_q_heads, seq_len, seq_len] = [1, 4, 64, 64]
    # Note: No scale factor for this test (just raw QK^T)
    scores = torch.matmul(Q_mxfp.float(), K_expanded.float().transpose(-2, -1))
    scores_bf16 = scores.to(torch.bfloat16)

    # Flatten output for comparison
    # Output: [num_q_heads, seq_len, seq_len] = [4, 64, 64]
    output_flat = scores_bf16.squeeze(0).reshape(-1)  # [16384]

    print(f"Output shape: {scores_bf16.shape}")
    print(f"Output_flat shape: {output_flat.shape}")  # [16384]

    # MXFP data ratio
    real_data_ratio = (8*8 + 8) / (8 * 8)  # ~1.125

    # Memory layout:
    # HBM: [Q (4096 elements) | K (1024 elements)]
    q_hbm_size = int(Q_flat.numel() * real_data_ratio)
    k_hbm_offset = q_hbm_size

    print(f"\nMemory layout:")
    print(f"  Q HBM offset: 0")
    print(f"  K HBM offset: {k_hbm_offset}")

    # VRAM layout:
    # [Q (4096) | Scores output (16384)]
    q_vram_offset = 0
    s_vram_offset = Q_flat.numel()  # 4096

    print(f"  Q VRAM offset: {q_vram_offset}")
    print(f"  S VRAM offset: {s_vram_offset}")

    # FP preload (not needed for this simple test)
    fp_preload = [0.0]

    # Prepare input tensors
    input_tensor = {
        "Q": Q_flat.reshape(batch, -1),  # [1, 4096]
        "K": K_flat.reshape(1, -1),  # [1, 1024]
    }

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": output_flat.reshape(1, -1)  # [1, 16384]
    }

    # Generate assembly code
    gen_code = "; M_BTMM Attention Test\n"
    gen_code += f"; Q: [{num_q_heads}, {seq_len}, {head_dim}] in VRAM\n"
    gen_code += f"; K: [{head_dim}, {seq_len}] in HBM -> MSRAM\n"
    gen_code += f"; Output: [{num_q_heads}, {seq_len}, {seq_len}] in VRAM\n\n"

    # Set K HBM address register
    gen_code += preload_addr_reg_asm(
        addr_reg_to_set=[1],
        available_registers=[1, 2],
        addr_reg_val=[k_hbm_offset]
    )

    # Reset registers
    gen_code += reset_reg_asm(alive_registers=[1, 2])

    # Set stride for Q prefetch (hidden_size = num_q_heads * head_dim = 64)
    gen_code += f"; Set stride for Q prefetch\n"
    gen_code += f"S_ADDI_INT gp1, gp0, {num_q_heads * head_dim}\n"
    gen_code += f"C_SET_STRIDE_REG gp1\n"

    # Prefetch Q from HBM to VRAM
    gen_code += f"; Prefetch Q to VRAM\n"
    gen_code += preload_act_asm(
        vlen=VLEN,
        preload_len=BLEN,  # 4 rows at a time
        batch=seq_len,  # 64 rows total
        hidden_size=num_q_heads * head_dim,  # 64 elements per row
        alive_registers=[1, 2, 3, 4, 5],
        act_vram_offset=q_vram_offset,
        activation_offset_reg=0,
        stride_size=num_q_heads * head_dim  # 64
    )

    # Reset registers
    gen_code += reset_reg_asm(alive_registers=[1, 2, 3, 4, 5])

    # Set stride for K prefetch
    gen_code += f"; Set stride for K prefetch\n"
    gen_code += f"S_ADDI_INT gp1, gp0, {head_dim}\n"  # K stride = 16
    gen_code += f"C_SET_STRIDE_REG gp1\n"

    # Generate M_BTMM code
    gen_code += generate_bmm_attn_asm(
        q_base_address=q_vram_offset,
        k_hbm_offset_reg=1,
        s_base_address=s_vram_offset,
        alive_registers=[1, 2, 3]
    )

    print("\n" + "=" * 60)
    print("Generated Assembly:")
    print("=" * 60)
    print(gen_code)

    # Create simulation environment
    create_sim_env(input_tensor, gen_code, golden_result, fp_preload)
    create_mem_for_sim(
        data_size=256,
        mode="behave_sim",
        asm="bmm_attn",
        data=None,
        specified_data_order=["Q", "K"]
    )

    # Save comparison parameters
    import json
    result_start_row = s_vram_offset // VLEN
    num_result_rows = output_flat.numel() // VLEN
    comparison_params = {
        "start_row_idx": result_start_row,
        "num_rows": num_result_rows,
        "num_batches": num_q_heads * seq_len,  # 4 * 64 = 256
        "elements_per_batch": seq_len  # 64
    }
    build_dir = Path(__file__).parent / "build"
    with open(build_dir / "comparison_params.json", "w") as f:
        json.dump(comparison_params, f, indent=2)

    print("\n" + "=" * 60)
    print("Test setup complete!")
    print("=" * 60)
    print(f"Result location: row {result_start_row}, {num_result_rows} rows")
    print(f"To run: cd .. && cargo run --release -- --opcode ... --hbm ...")
