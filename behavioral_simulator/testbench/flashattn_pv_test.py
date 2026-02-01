"""PV multiplication test for flashattn.pv module.

Tests the computing_pv_code function which computes:
P @ V where P is the softmax attention scores and V is the value matrix.
Output is written in packed format with heads interleaved.
"""

import sys
import json
import math
import torch

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from compiler.asm_templates import preload_act_asm, reset_reg_asm, preload_addr_reg_asm
from compiler.asm_templates.flashattn import (
    qkt_multiply, online_softmax_code, computing_pv_code, reset_kv_prefetch
)
from compiler.asm_templates.reset_reg_asm import reset_fpreg_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim


if __name__ == "__main__":
    # Test configuration
    batch_size = 1
    s_q = 64
    s_kv = 64
    num_q_heads = 4
    num_kv_heads = 1
    h_qkv = 16
    mlen = 64
    vlen = 64
    blen = 4
    qk_scale = 1.0 / math.sqrt(h_qkv)
    real_data_ratio = (8*8 + 8) / (8 * 8)

    q_index_2_kv_index_ratio = num_q_heads // num_kv_heads
    hidden_size = h_qkv * num_q_heads

    device = torch.device("cpu")
    print(f"flashattn.pv Test Config:")
    print(f"  batch_size={batch_size}, s_q={s_q}, s_kv={s_kv}")
    print(f"  num_q_heads={num_q_heads}, num_kv_heads={num_kv_heads}, h_qkv={h_qkv}")
    print(f"  blen={blen}, mlen={mlen}")

    torch.manual_seed(42)
    q = torch.randn(batch_size, s_q, num_q_heads, h_qkv, dtype=torch.bfloat16, device=device)
    k = torch.randn(batch_size, s_kv, num_kv_heads, h_qkv, dtype=torch.bfloat16, device=device)
    v = torch.randn(batch_size, s_kv, num_kv_heads, h_qkv, dtype=torch.bfloat16, device=device)

    print(f"\nTensor shapes:")
    print(f"  Q: {q.shape}")
    print(f"  K: {k.shape}")
    print(f"  V: {v.shape}")

    input_tensor = {
        "q": q.reshape(batch_size, -1),
        "k": k.reshape(batch_size, -1),
        "v": v.reshape(batch_size, -1),
    }

    # Compute golden output: PV = softmax(QK^T * scale) @ V
    # For test, just compute for first head
    test_q_head = 0
    test_kv_head = 0

    q_2d = q[0, :, test_q_head, :]
    k_2d = k[0, :, test_kv_head, :]
    v_2d = v[0, :, test_kv_head, :]

    qkt = torch.matmul(q_2d, k_2d.T)
    s_scaled = qkt * qk_scale
    s_max = s_scaled.max(dim=-1, keepdim=True)[0]
    p = torch.exp(s_scaled - s_max)
    # PV without final normalization
    pv = torch.matmul(p, v_2d)  # (s_q, h_qkv)

    print(f"\nGolden PV shape: {pv.shape}")

    # Memory layout
    q_base_address = 0
    q_total_size = s_q * num_q_heads * h_qkv
    s_base_address = q_base_address + q_total_size
    pv_base_address = s_base_address + mlen * mlen * q_index_2_kv_index_ratio
    o_old_base_address = pv_base_address + mlen * mlen * q_index_2_kv_index_ratio
    fp_sram_start = 3

    print(f"\nVSRAM Layout:")
    print(f"  Q Base: {q_base_address}")
    print(f"  S Base: {s_base_address}")
    print(f"  PV Base: {pv_base_address}")
    print(f"  O_old Base: {o_old_base_address}")

    # HBM layout
    q_hbm_size = int(s_q * num_q_heads * h_qkv * batch_size * real_data_ratio)
    k_hbm_size = int(s_kv * num_kv_heads * h_qkv * batch_size * real_data_ratio)
    k_hbm_offset = q_hbm_size
    v_hbm_offset = q_hbm_size + k_hbm_size

    print(f"\nHBM Layout:")
    print(f"  K offset: {k_hbm_offset}")
    print(f"  V offset: {v_hbm_offset}")

    # Generate assembly
    gen_assembly_code = "; flashattn.pv Test \n"

    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1, 2],
        available_registers=[1, 2],
        addr_reg_val=[k_hbm_offset, v_hbm_offset]
    )

    gen_assembly_code += preload_act_asm(
        vlen=mlen,
        preload_len=4,
        batch=batch_size,
        hidden_size=h_qkv * num_q_heads * s_q,
        alive_registers=[1, 2, 3, 4, 5],
        act_vram_offset=0,
        activation_offset_reg=0
    )

    gen_assembly_code += reset_reg_asm(alive_registers=[1, 2, 3, 4, 5])

    gen_assembly_code += reset_kv_prefetch(
        hkv=num_kv_heads,
        d=h_qkv,
        kv_len=s_kv,
        batch=batch_size,
        alive_registers_int=[1],
    )

    q_base_for_kv_head = q_base_address + test_kv_head * q_index_2_kv_index_ratio * h_qkv
    q_row_stride = (num_q_heads * h_qkv) // mlen

    # QKT
    gen_assembly_code += qkt_multiply(
        d=h_qkv,
        mlen=mlen,
        alive_registers=[1, 2],
        q_base_address=q_base_for_kv_head,
        k_base_hbm_offset_reg=1,
        q_head_index=test_q_head,
        k_head_index=test_kv_head,
        s_base_address=s_base_address,
        q_row_stride=q_row_stride,
    )

    gen_assembly_code += reset_reg_asm(alive_registers=[1, 2])

    # Online softmax
    gen_assembly_code += online_softmax_code(
        mlen=mlen,
        alive_registers_int=[1, 2, 3, 4, 5],
        alive_registers_fp=[1, 2, 3, 4, 5],
        s_address=s_base_address + test_q_head * mlen * mlen,
        m_start_address=fp_sram_start,
        qk_scale_address=1,
    )

    gen_assembly_code += reset_fpreg_asm(alive_registers=[1, 2, 3, 4, 5, 6])
    gen_assembly_code += reset_reg_asm(alive_registers=[1, 2, 3, 4, 5, 6])

    # PV multiplication
    gen_assembly_code += computing_pv_code(
        head_dim=h_qkv,
        q_head_num=num_q_heads,
        blen=blen,
        mlen=mlen,
        vlen=hidden_size,  # VLEN = num_q_heads * h_qkv for packed output
        alive_registers=[1, 2, 3, 4, 5, 6],
        p_base_address=s_base_address,
        v_base_hbm_offset_reg=2,
        q_head_index=test_q_head,
        v_head_index=test_kv_head,
        output_base_address=o_old_base_address,
        head_offset=test_q_head * h_qkv,
    )

    gen_assembly_code += reset_reg_asm(alive_registers=[1, 2, 3, 4, 5, 6])

    # Golden result - PV for the first head, but stored in packed format
    # Each row of output has hidden_size elements, with this head at offset 0
    golden_pv_packed = torch.zeros(s_q, hidden_size, dtype=torch.bfloat16)
    golden_pv_packed[:, test_q_head * h_qkv : (test_q_head + 1) * h_qkv] = pv

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": golden_pv_packed.reshape(-1).unsqueeze(0)
    }

    print(f"\nGolden PV packed shape: {golden_pv_packed.shape}")

    fp_preload = [0.0, qk_scale, -float("inf")]
    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    create_mem_for_sim(data_size=256, mode="behave_sim", asm=None, data=None, specified_data_order=["q", "k", "v"])

    result_start_row = o_old_base_address // vlen
    num_result_rows = (s_q * hidden_size) // vlen

    comparison_params = {
        "start_row_idx": result_start_row,
        "num_rows": num_result_rows,
        "num_batches": s_q,
        "elements_per_batch": hidden_size,
        "row_dim": vlen,
        "use_stride_mode": False
    }
    build_dir = Path(__file__).parent / "build"
    with open(build_dir / "comparison_params.json", "w") as f:
        json.dump(comparison_params, f, indent=2)

    print(f"\nResult location: row {result_start_row}, {num_result_rows} rows")
    print(f"Comparison params: {comparison_params}")
    print("=" * 60)
