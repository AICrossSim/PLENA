"""Reset functions test for flashattn.reset module.

Tests reset_fpsram_code, reset_vssram_code, and reset_kv_prefetch functions.
These functions initialize memory regions with specific values.
"""

import sys
import json
import torch
import numpy as np

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from compiler.asm_templates import reset_reg_asm
from compiler.asm_templates.flashattn import (
    reset_fpsram_code, reset_vssram_code, reset_kv_prefetch
)
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim


if __name__ == "__main__":
    # Test configuration
    mlen = 64
    vlen = 64
    num_heads = 4
    h_qkv = 16

    device = torch.device("cpu")
    print(f"flashattn.reset Test Config:")
    print(f"  mlen={mlen}, vlen={vlen}")
    print(f"  num_heads={num_heads}, h_qkv={h_qkv}")

    # Test 1: reset_fpsram_code - initialize m_old with -inf
    print("\n=== Test 1: reset_fpsram_code ===")

    # FP SRAM layout for flash attention:
    # Per head: m_old (mlen), m_res (mlen), l_old (mlen) = 3 * mlen per head
    fp_sram_start = 3  # After 0=zero, 1=qk_scale, 2=-inf

    gen_assembly_code = "; flashattn.reset Test \n"

    # Reset m_old with -inf (address 2 in fp_preload)
    gen_assembly_code += reset_fpsram_code(
        reset_start_address=fp_sram_start,
        per_stride_dim=mlen,
        reset_stride=3 * mlen,
        reset_amount=num_heads,
        reset_val_address=2,  # -inf
        alive_registers_fp=[1],
        alive_registers_int=[1, 2, 3],
    )

    gen_assembly_code += reset_reg_asm(alive_registers=[1, 2, 3])

    # Reset l_old with zeros (address 0 in fp_preload)
    gen_assembly_code += reset_fpsram_code(
        reset_start_address=fp_sram_start + 2 * mlen,
        per_stride_dim=mlen,
        reset_stride=3 * mlen,
        reset_amount=num_heads,
        reset_val_address=0,  # 0.0
        alive_registers_fp=[1],
        alive_registers_int=[1, 2, 3],
    )

    gen_assembly_code += reset_reg_asm(alive_registers=[1, 2, 3])

    print(f"  FP SRAM start: {fp_sram_start}")
    print(f"  m_old positions: {[fp_sram_start + i * 3 * mlen for i in range(num_heads)]}")
    print(f"  l_old positions: {[fp_sram_start + 2 * mlen + i * 3 * mlen for i in range(num_heads)]}")

    # Test 2: reset_vssram_code - initialize O_old with zeros
    print("\n=== Test 2: reset_vssram_code ===")

    o_old_base_address = 1024  # Some test address

    gen_assembly_code += reset_vssram_code(
        reset_start_address=o_old_base_address,
        vect_dim=mlen,
        per_stride_dim=h_qkv,
        reset_stride=num_heads * mlen,
        reset_amount=num_heads,
        alive_registers_int=[1, 2, 3],
    )

    gen_assembly_code += reset_reg_asm(alive_registers=[1, 2, 3])

    print(f"  O_old base address: {o_old_base_address}")

    # Test 3: reset_kv_prefetch - set scale and stride for HBM prefetch
    print("\n=== Test 3: reset_kv_prefetch ===")

    hkv = 1
    kv_len = 64
    batch = 1

    gen_assembly_code += reset_kv_prefetch(
        hkv=hkv,
        d=h_qkv,
        kv_len=kv_len,
        batch=batch,
        alive_registers_int=[1],
    )

    gen_assembly_code += reset_reg_asm(alive_registers=[1])

    print(f"  hkv={hkv}, d={h_qkv}, kv_len={kv_len}, batch={batch}")
    print(f"  scale = hkv * d * kv_len * batch = {hkv * h_qkv * kv_len * batch}")
    print(f"  stride = hkv * d * batch = {hkv * h_qkv * batch}")

    # Create minimal input tensor (reset operations don't need actual data)
    input_tensor = {
        "dummy": torch.zeros(1, 1, dtype=torch.bfloat16),
    }

    # Golden result - we're testing reset operations, so just verify code generates
    # The actual verification would need to check FP SRAM and VSRAM contents
    golden_result = {
        "input_tensor": input_tensor,
        "original_output": torch.zeros(1, 1, dtype=torch.bfloat16)
    }

    fp_preload = [0.0, 1.0, -float("inf")]
    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)

    # For reset tests, we don't need to load actual data
    # Just verify the assembly code generates correctly
    print("\n=== Generated Assembly Code ===")
    print(gen_assembly_code[:500] + "..." if len(gen_assembly_code) > 500 else gen_assembly_code)

    # Write comparison params (minimal for reset test)
    comparison_params = {
        "start_row_idx": 0,
        "num_rows": 1,
        "num_batches": 1,
        "elements_per_batch": 1,
        "row_dim": vlen,
        "use_stride_mode": False,
        "note": "Reset test - verify assembly generation only"
    }
    build_dir = Path(__file__).parent / "build"
    with open(build_dir / "comparison_params.json", "w") as f:
        json.dump(comparison_params, f, indent=2)

    print("\n" + "=" * 60)
    print("Reset functions test complete")
    print("Note: This test verifies assembly code generation.")
    print("Full verification requires running behavioral simulator.")
    print("=" * 60)
