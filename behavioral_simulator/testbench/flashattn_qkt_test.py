"""QKT multiplication test for flashattn.qkt module.

Tests the qkt_multiply function with M_BTMM.
Configuration: h_qkv=16, num_q_heads=16, num_kv_heads=4, seq_len=64, batch=1

Key constraints:
- h_qkv must equal hardware HLEN (16) for correct M_BTMM operation
- M_BTMM processes MLEN//HLEN = 64//16 = 4 Q heads in parallel per KV head
- HBM stride alignment: num_kv_heads * h_qkv >= 64 (so num_kv_heads >= 4 with h_qkv=16)
- With num_kv_heads=4, h_qkv=16: stride = 64, which is 64-byte aligned
"""

import sys
import json
import torch

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from compiler.asm_templates import preload_act_asm, reset_reg_asm, preload_addr_reg_asm
from compiler.asm_templates.flashattn import qkt_multiply, reset_kv_prefetch
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim


if __name__ == "__main__":
    # Multi-head test configuration
    batch_size = 1
    s_q = 64
    s_kv = 64
    num_q_heads = 16
    num_kv_heads = 4
    h_qkv = 16
    mlen = 64
    vlen = 64
    real_data_ratio = (8*8 + 8) / (8 * 8)

    q_index_2_kv_index_ratio = num_q_heads // num_kv_heads

    device = torch.device("cpu")
    print(f"flashattn.qkt Multi-Head QKT Test Config:")
    print(f"  batch_size={batch_size}, s_q={s_q}, s_kv={s_kv}")
    print(f"  num_q_heads={num_q_heads}, num_kv_heads={num_kv_heads}, h_qkv={h_qkv}")
    print(f"  q_index_2_kv_index_ratio={q_index_2_kv_index_ratio}")

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

    # Compute golden QKT output for all head combinations
    golden_qkt_list = []
    for kv_head in range(num_kv_heads):
        for q_head_offset in range(q_index_2_kv_index_ratio):
            q_head = kv_head * q_index_2_kv_index_ratio + q_head_offset
            q_2d = q[0, :, q_head, :]
            k_2d = k[0, :, kv_head, :]
            qkt = torch.matmul(q_2d, k_2d.T)
            golden_qkt_list.append(qkt)
            print(f"  Q head {q_head} x K head {kv_head} -> QKT shape: {qkt.shape}")

    golden_qkt_all = torch.stack(golden_qkt_list, dim=0)
    print(f"\nGolden QKT all heads shape: {golden_qkt_all.shape}")

    # Memory layout in VSRAM
    q_base_address = 0
    q_total_size = s_q * num_q_heads * h_qkv
    s_base_address = q_base_address + q_total_size

    print(f"\nVSRAM Layout:")
    print(f"  Q Base: {q_base_address}")
    print(f"  Q Total Size: {q_total_size}")
    print(f"  S Base (QKT result): {s_base_address}")

    # HBM layout
    q_hbm_size = int(s_q * num_q_heads * h_qkv * batch_size * real_data_ratio)
    k_hbm_offset = q_hbm_size

    print(f"\nHBM Layout:")
    print(f"  Q: 0 - {q_hbm_size}")
    print(f"  K: {k_hbm_offset}")

    # Generate assembly
    gen_assembly_code = "; flashattn.qkt Multi-Head QKT Test \n"

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

    test_kv_head = 0
    q_head_start = test_kv_head * q_index_2_kv_index_ratio
    q_head_end = q_head_start + q_index_2_kv_index_ratio - 1
    gen_assembly_code += f"; === KV head {test_kv_head} (Q heads {q_head_start}-{q_head_end}) ===\n"

    q_base_for_kv_head = q_base_address + test_kv_head * q_index_2_kv_index_ratio * h_qkv
    q_row_stride = (num_q_heads * h_qkv) // mlen

    gen_assembly_code += qkt_multiply(
        d=h_qkv,
        mlen=mlen,
        alive_registers=[1, 2],
        q_base_address=q_base_for_kv_head,
        k_base_hbm_offset_reg=1,
        q_head_index=0,
        k_head_index=test_kv_head,
        s_base_address=s_base_address,
        q_row_stride=q_row_stride,
    )

    gen_assembly_code += reset_reg_asm(alive_registers=[1, 2])

    num_test_heads = q_index_2_kv_index_ratio
    golden_qkt_test = golden_qkt_all[:num_test_heads]

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": golden_qkt_test.reshape(-1).unsqueeze(0)
    }

    print(f"\nGolden QKT test shape: {golden_qkt_test.shape}")
    print(f"Golden output flattened shape: {golden_qkt_test.reshape(-1).shape}")

    fp_preload = [0.0, 1.0, -float("inf")]
    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    create_mem_for_sim(data_size=256, mode="behave_sim", asm=None, data=None, specified_data_order=["q", "k"])

    result_start_row = s_base_address // vlen
    num_result_rows = (num_test_heads * mlen * mlen) // vlen

    comparison_params = {
        "start_row_idx": result_start_row,
        "num_rows": num_result_rows,
        "num_batches": 1,
        "elements_per_batch": num_test_heads * mlen * mlen,
        "row_dim": vlen,
        "use_stride_mode": False
    }
    build_dir = Path(__file__).parent / "build"
    with open(build_dir / "comparison_params.json", "w") as f:
        json.dump(comparison_params, f, indent=2)

    print(f"\nResult location: row {result_start_row}, {num_result_rows} rows")
    print(f"Comparison params: {comparison_params}")
    print("=" * 60)
