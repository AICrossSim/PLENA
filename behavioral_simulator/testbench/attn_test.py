
# This test is about the prefilling stage of the flash attention process.

import sys
import math
import torch

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from compiler.asm_templates import flash_attn_asm, preload_act_asm, reset_reg_asm, preload_addr_reg_asm
from create_sim_env import create_sim_env
from aria_lm_ops.models.llama import flash_attn2_gemv
from sim_env_utils import create_mem_for_sim


if __name__ == "__main__":
    # Currently single batch test
    # NOTE: h_qkv must be 64 (= HLEN) to ensure HBM 64-byte alignment
    # With h_qkv=64, k_head_index * h_qkv = 0, 64, 128, ... are all 64-aligned
    batch_size = 1
    s_q = 64
    s_kv = 64
    num_q_heads = 4   # Reduced to keep test size manageable with h_qkv=64
    num_kv_heads = 1  # Single KV head for simplicity
    h_qkv = 16        # Must equal HLEN for HBM alignment
    hidden_size = h_qkv * num_q_heads  # 64 * 4 = 256
    mlen = 64
    vlen = 64
    blen = 4
    qk_scale = 1.0 / math.sqrt(h_qkv)
    real_data_ratio = (8*8 + 8) / (8 * 8)
    fp_preload = [0.0, qk_scale, -float("inf")]

    # Set device - use CPU for consistent testing
    device = torch.device("cpu")
    print(f"Using device: {device}")
    print(f"Flash Attention Config:")
    print(f"  batch_size={batch_size}, s_q={s_q}, s_kv={s_kv}")
    print(f"  num_q_heads={num_q_heads}, num_kv_heads={num_kv_heads}, h_qkv={h_qkv}")
    print(f"  hidden_size={hidden_size}, qk_scale={qk_scale:.6f}")
    print(f"  fp_preload: {fp_preload}")

    torch.manual_seed(42)
    # in shape of b, s, h, d
    q = torch.randn(batch_size, s_q, num_q_heads, h_qkv, dtype=torch.bfloat16, device=device)
    k = torch.randn(batch_size, s_kv, num_kv_heads, h_qkv, dtype=torch.bfloat16, device=device)
    v = torch.randn(batch_size, s_kv, num_kv_heads, h_qkv, dtype=torch.bfloat16, device=device)

    # Set print options to avoid "..." truncation for high-dimensional tensors
    torch.set_printoptions(edgeitems=20, threshold=20000, linewidth=200)

    input_tensor = {
        "q": q.reshape(batch_size, -1),
        "k": k.reshape(batch_size, -1),
        "v": v.reshape(batch_size, -1)
    }

    print(f"\nTensor shapes:")
    print(f"  q: {q.shape} -> reshaped: {q.reshape(batch_size, -1).shape}")
    print(f"  k: {k.shape} -> reshaped: {k.reshape(batch_size, -1).shape}")
    print(f"  v: {v.shape} -> reshaped: {v.reshape(batch_size, -1).shape}")

    # Compute golden output
    print("\nComputing golden output...")
    original_output = flash_attn2_gemv(
        q,
        k,
        v,
        qk_scale=qk_scale,
        s_q=s_q,
        s_kv=s_kv,
        h_qkv=h_qkv,
        num_q_heads=num_q_heads,
        num_kv_heads=num_kv_heads,
        Bc=mlen,
        Br=mlen
    )

    # Reshape output for golden comparison: (batch, s_q, num_heads, h_qkv) -> (batch * s_q, hidden_size)
    original_output_flat = original_output.reshape(batch_size * s_q, hidden_size)
    print(f"  original_output shape: {original_output.shape}")
    print(f"  original_output_flat shape: {original_output_flat.shape}")

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": original_output_flat
    }

    gen_assembly_code = "; FlashAttn Test Generation \n"
    gen_assembly_code += f"; Config: batch={batch_size}, s_q={s_q}, s_kv={s_kv}, hq={num_q_heads}, hkv={num_kv_heads}, d={h_qkv}\n"

    # Calculate HBM offsets for K and V
    # Layout in HBM: [Q | K | V]
    q_hbm_size = int(s_q * num_q_heads * h_qkv * batch_size * real_data_ratio)
    k_hbm_size = int(s_kv * num_kv_heads * h_qkv * batch_size * real_data_ratio)
    k_hbm_offset = q_hbm_size
    v_hbm_offset = q_hbm_size + k_hbm_size

    print(f"\nHBM Layout:")
    print(f"  Q: 0 - {q_hbm_size} (size: {q_hbm_size})")
    print(f"  K: {k_hbm_offset} - {k_hbm_offset + k_hbm_size} (size: {k_hbm_size})")
    print(f"  V: {v_hbm_offset} (size: {k_hbm_size})")

    # Set the K, V addr offset registers
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1, 2],
        available_registers=[1, 2],
        addr_reg_val=[k_hbm_offset, v_hbm_offset]
    )

    # Gen Activation Preload Q
    gen_assembly_code += preload_act_asm(
        vlen=mlen,
        preload_len=4,
        batch=batch_size,
        hidden_size=h_qkv * num_q_heads * s_q,
        alive_registers=[1, 2, 3, 4, 5],
        act_vram_offset=0,
        activation_offset_reg=0
    )

    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1, 2, 3, 4, 5]
    )

    # Start the flash attention process
    gen_assembly_code += flash_attn_asm(
        mlen=mlen,
        blen=blen,
        batch=batch_size,
        hq=num_q_heads,
        hkv=num_kv_heads,
        d=h_qkv,
        q_len=s_q,
        kv_len=s_kv,
        alive_registers_int=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        alive_registers_fp=[1, 2, 3, 4, 5, 6, 7],
        vector_sram_base_address=0,
        fp_sram_start_address=3,
        k_base_hbm_offset_reg=1,
        v_base_hbm_offset_reg=2
    )

    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    create_mem_for_sim(data_size=256, mode="behave_sim", asm=None, data=None, specified_data_order=["q", "k", "v"])

    import json
    # Calculate VRAM memory layout to find O_old base address (matching flash_attn_asm.py)
    q_index_2_kv_index_ratio = num_q_heads // num_kv_heads
    q_base_address = 0  # vector_sram_base_address
    s_base_address = q_base_address + num_q_heads * num_kv_heads * s_q
    pv_base_address = s_base_address + mlen * mlen * q_index_2_kv_index_ratio
    o_old_base_address = pv_base_address + mlen * mlen * q_index_2_kv_index_ratio

    # Output is stored at o_old_base_address
    result_vram_offset = o_old_base_address
    effective_batch = batch_size * s_q
    result_start_row = result_vram_offset // vlen
    num_result_rows = (effective_batch * hidden_size) // vlen

    comparison_params = {
        "start_row_idx": result_start_row,
        "num_rows": num_result_rows,
        "num_batches": effective_batch,
        "elements_per_batch": hidden_size,
        "row_dim": vlen,
        "use_stride_mode": True
    }
    build_dir = Path(__file__).parent / "build"
    with open(build_dir / "comparison_params.json", "w") as f:
        json.dump(comparison_params, f, indent=2)

    print("\n" + "=" * 60)
    print("VRAM Memory Layout:")
    print(f"  Q Base Address: {q_base_address}")
    print(f"  S Base Address: {s_base_address}")
    print(f"  PV Base Address: {pv_base_address}")
    print(f"  O_Old Base Address: {o_old_base_address}")
    print("=" * 60)
    print("Finished generating assembly code")
    print(f"Result location: row {result_start_row}, {num_result_rows} rows")
    print(f"Comparison params: {comparison_params}")
    print("=" * 60)
