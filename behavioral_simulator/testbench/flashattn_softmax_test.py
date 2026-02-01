"""Online softmax test for flashattn.online_softmax module.

Tests the online_softmax_code function which computes:
- Row-wise max (m_curr) with running max tracking (m_last)
- Row-wise exp(S - m_curr) = P (softmax probabilities before normalization)
- Running sum l = l_old * exp(m_last - m_curr) + sum(P)
"""

import sys
import json
import math
import torch

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from compiler.asm_templates import preload_act_asm, reset_reg_asm, preload_addr_reg_asm
from compiler.asm_templates.flashattn import qkt_multiply, online_softmax_code, reset_kv_prefetch
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
    qk_scale = 1.0 / math.sqrt(h_qkv)
    real_data_ratio = (8*8 + 8) / (8 * 8)

    q_index_2_kv_index_ratio = num_q_heads // num_kv_heads

    device = torch.device("cpu")
    print(f"flashattn.online_softmax Test Config:")
    print(f"  batch_size={batch_size}, s_q={s_q}, s_kv={s_kv}")
    print(f"  num_q_heads={num_q_heads}, num_kv_heads={num_kv_heads}, h_qkv={h_qkv}")
    print(f"  qk_scale={qk_scale:.6f}")

    torch.manual_seed(42)
    q = torch.randn(batch_size, s_q, num_q_heads, h_qkv, dtype=torch.bfloat16, device=device)
    k = torch.randn(batch_size, s_kv, num_kv_heads, h_qkv, dtype=torch.bfloat16, device=device)

    print(f"\nTensor shapes:")
    print(f"  Q: {q.shape}")
    print(f"  K: {k.shape}")

    input_tensor = {
        "q": q.reshape(batch_size, -1),
        "k": k.reshape(batch_size, -1),
    }

    # Compute golden output: P = softmax(QK^T * scale) before l normalization
    # For online softmax, we compute exp(S - max(S)) and track running stats
    golden_p_list = []
    for q_head in range(num_q_heads):
        kv_head = q_head // q_index_2_kv_index_ratio
        q_2d = q[0, :, q_head, :]
        k_2d = k[0, :, kv_head, :]
        qkt = torch.matmul(q_2d, k_2d.T)  # (s_q, s_kv)

        # Scale
        s_scaled = qkt * qk_scale

        # Row-wise softmax (before final 1/l normalization, so just exp(S - max))
        s_max = s_scaled.max(dim=-1, keepdim=True)[0]
        p = torch.exp(s_scaled - s_max)
        golden_p_list.append(p)
        print(f"  Q head {q_head} -> P shape: {p.shape}")

    golden_p_all = torch.stack(golden_p_list, dim=0)  # (num_q_heads, s_q, s_kv)
    print(f"\nGolden P all heads shape: {golden_p_all.shape}")

    # Memory layout
    q_base_address = 0
    q_total_size = s_q * num_q_heads * h_qkv
    s_base_address = q_base_address + q_total_size
    fp_sram_start = 3  # After 0=zero, 1=qk_scale, 2=-inf

    print(f"\nVSRAM Layout:")
    print(f"  Q Base: {q_base_address}")
    print(f"  S Base: {s_base_address}")
    print(f"  FP SRAM start: {fp_sram_start}")

    # HBM layout
    q_hbm_size = int(s_q * num_q_heads * h_qkv * batch_size * real_data_ratio)
    k_hbm_offset = q_hbm_size

    # Generate assembly
    gen_assembly_code = "; flashattn.online_softmax Test \n"

    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1],
        available_registers=[1, 2],
        addr_reg_val=[k_hbm_offset]
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

    # Test single head: QKT then softmax
    test_q_head = 0
    test_kv_head = 0
    q_base_for_kv_head = q_base_address + test_kv_head * q_index_2_kv_index_ratio * h_qkv
    q_row_stride = (num_q_heads * h_qkv) // mlen

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

    # Apply online softmax
    gen_assembly_code += online_softmax_code(
        mlen=mlen,
        alive_registers_int=[1, 2, 3, 4, 5],
        alive_registers_fp=[1, 2, 3, 4, 5],
        s_address=s_base_address + test_q_head * mlen * mlen,
        m_start_address=fp_sram_start,
        qk_scale_address=1,
    )

    gen_assembly_code += reset_reg_asm(alive_registers=[1, 2, 3, 4, 5])

    # Golden result - P for the first head
    golden_p_test = golden_p_all[test_q_head]  # (s_q, s_kv)

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": golden_p_test.reshape(-1).unsqueeze(0)
    }

    print(f"\nGolden P test shape: {golden_p_test.shape}")

    fp_preload = [0.0, qk_scale, -float("inf")]
    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    create_mem_for_sim(data_size=256, mode="behave_sim", asm=None, data=None, specified_data_order=["q", "k"])

    result_start_row = s_base_address // vlen
    num_result_rows = (mlen * mlen) // vlen

    comparison_params = {
        "start_row_idx": result_start_row,
        "num_rows": num_result_rows,
        "num_batches": 1,
        "elements_per_batch": mlen * mlen,
        "row_dim": vlen,
        "use_stride_mode": False
    }
    build_dir = Path(__file__).parent / "build"
    with open(build_dir / "comparison_params.json", "w") as f:
        json.dump(comparison_params, f, indent=2)

    print(f"\nResult location: row {result_start_row}, {num_result_rows} rows")
    print(f"Comparison params: {comparison_params}")
    print("=" * 60)
