#!/usr/bin/env python3
"""Test script for RMS norm simulator tool."""

import sys
from pathlib import Path

# Add paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "kernel_agents"))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))
sys.path.insert(0, str(PROJECT_ROOT / "behavioral_simulator" / "testbench"))

from anthropic_agent.tools.simulator import run_simulator

# Example RMS norm assembly (placeholder - agent should generate real one)
# This is a minimal example showing the expected structure
RMS_NORM_ASM = """
; RMS Norm Kernel
; batch=4, hidden=128, vlen=64
; Activation at VRAM address 0 (preloaded)
; FP SRAM[1] = epsilon, FP SRAM[2] = 1/hidden_dim

; Load constants
S_LD_FP f1, gp0, 1              ; f1 = epsilon (1e-6)
S_LD_FP f2, gp0, 2              ; f2 = 1/hidden_dim (1/128)

; Initialize registers
S_ADDI_INT gp1, gp0, 0          ; act_addr = 0
S_ADDI_INT gp2, gp0, 512        ; scratchpad = batch * hidden = 4 * 128

; TODO: Agent should generate the full RMS norm algorithm:
; For each batch:
;   1. V_MUL_VV to compute x^2
;   2. V_RED_SUM to sum squared values
;   3. S_MUL_FP to compute mean (sum * 1/hidden_dim)
;   4. S_ADD_FP to add epsilon
;   5. S_SQRT_FP to compute sqrt
;   6. S_RECI_FP to compute 1/rms
;   7. V_MUL_VF to normalize (x * 1/rms) in-place
"""

def main():
    print("=" * 60)
    print("Testing RMS Norm Simulator Tool")
    print("=" * 60)

    result = run_simulator(
        assembly_code=RMS_NORM_ASM,
        layer_type='rms_norm',
        hidden_size=128,
        batch_size=4,
        seq_len=1
    )

    print(f"\nSuccess: {result['success']}")
    print(f"Latency: {result.get('latency_ns')} ns")
    print(f"MSE: {result.get('mse')}")
    print(f"Match Rate: {result.get('match_rate')}")
    print(f"Instruction Count: {result.get('instruction_count')}")

    if result.get('errors'):
        print(f"\nErrors:")
        for err in result['errors']:
            print(f"  - {err}")

    if result.get('test_config'):
        print(f"\nTest Config:")
        for k, v in result['test_config'].items():
            print(f"  {k}: {v}")

    # Low match_rate is expected with placeholder assembly
    if result.get('match_rate') is not None and result['match_rate'] < 0.95:
        print(f"\nNote: Low match rate ({result['match_rate']:.2%}) - assembly doesn't implement full RMS norm")
        print("Target match_rate should be > 95% for RMS norm")

if __name__ == "__main__":
    main()
