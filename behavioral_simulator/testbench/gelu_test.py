import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import argparse
import torch
from torch import nn
from compiler.asm_templates import preload_act_asm, reset_reg_asm, gelu_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim
from quant.quantizer.hardware_quantizer.mxfp import _mx_fp_quantize_hardware


def quantize_to_mxfp(tensor):
    """
    Quantize tensor to MXFP format matching hardware (E4M3 with 8-bit scale per block of 8).
    Returns the dequantized tensor (what hardware sees after HBM->VRAM load).
    """
    orig_shape = tensor.shape
    bm_x, _, _, _ = _mx_fp_quantize_hardware(
        tensor, width=8, exponent_width=4, exponent_bias_width=8, block_size=[8]
    )
    return bm_x.reshape(orig_shape)


def gelu_with_bf16_intermediates(x):
    """
    GELU using sigmoid approximation matching hardware implementation.
    GELU(x) ≈ x * sigmoid(1.702 * x) with BF16 storage after each operation.
    """
    x_f32 = x.float()

    # Step 1: 1.702 * x
    step1 = (1.702 * x_f32).to(torch.bfloat16)
    # Step 2: -1.702 * x
    step2 = (-step1.float()).to(torch.bfloat16)
    # Step 3: exp(-1.702 * x)
    step3 = torch.exp(step2.float()).to(torch.bfloat16)
    # Step 4: 1 + exp(-1.702 * x)
    step4 = (1.0 + step3.float()).to(torch.bfloat16)
    # Step 5: 1 / (1 + exp(-1.702 * x)) = sigmoid(1.702 * x)
    step5 = (1.0 / step4.float()).to(torch.bfloat16)
    # Step 6: x * sigmoid(1.702 * x)
    return (x_f32 * step5.float()).to(torch.bfloat16)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GELU test for behavioral simulator")
    parser.add_argument("--n", type=int, default=None, help="Total elements (batch * hidden)")
    parser.add_argument("--hidden", type=int, default=None, help="Hidden size")
    parser.add_argument("--config", type=str, default="C1",
                        choices=["C1", "C2", "C3", "C4", "C5"],
                        help="PLENA workload config")
    args = parser.parse_args()

    # GELU workload configurations: (n, hidden_size)
    GELU_CONFIGS = {
        "C1": (256, 64),
        "C2": (512, 128),
        "C3": (1024, 256),
        "C4": (2048, 512),
        "C5": (4096, 1024),
    }

    if args.n is not None and args.hidden is not None:
        n_total = args.n
        hidden_size = args.hidden
        print(f"Using custom config: n={n_total}, hidden={hidden_size}")
    else:
        n_total, hidden_size = GELU_CONFIGS[args.config]
        print(f"Using PLENA config {args.config}: n={n_total}, hidden={hidden_size}")

    batch_size = n_total // hidden_size
    assert batch_size * hidden_size == n_total
    vlen = 64

    # FP SRAM layout: [0]=0.0, [1]=1.0, [2]=1.702 (for GELU sigmoid approximation)
    fp_preload = [0.0, 1.0, 1.702]

    torch.manual_seed(42)
    act_tensor = torch.randn(batch_size, hidden_size, dtype=torch.bfloat16)

    print("Input tensor shape:", act_tensor.shape)
    print("Input tensor (first 8 values):", act_tensor[0, :8])

    # Quantize input to MXFP to match hardware precision
    act_mxfp = quantize_to_mxfp(act_tensor).to(act_tensor.dtype)

    # Compute golden using hardware's sigmoid approximation with BF16 intermediates
    original_output = gelu_with_bf16_intermediates(act_mxfp)

    print("Output tensor (first 8 values):", original_output[0, :8])

    input_tensor = {
        "act_tensor": act_mxfp,  # Use MXFP-quantized input to match simulator
    }

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": original_output
    }

    gen_assembly_code = "; GELU Test Generation\n"

    # Reset registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1, 2, 3]
    )

    # Preload activations
    gen_assembly_code += preload_act_asm(
        vlen=vlen,
        preload_len=batch_size,
        batch=batch_size,
        hidden_size=hidden_size,
        alive_registers=[1, 2, 3, 4, 5],
        act_vram_offset=0,
        activation_offset_reg=0,
        stride_size=hidden_size
    )

    # Reset registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1, 2, 3, 4]
    )

    # GELU computation
    gen_assembly_code += gelu_asm(
        const_one_fp_address=1,
        const_1702_fp_address=2,
        alive_registers=[1, 2, 3, 4, 5],
        activation_base_address=0,
        scratchpad_base_address=hidden_size * batch_size,
        vlen=vlen,
        batch_size=batch_size,
        hidden_dim=hidden_size
    )

    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    create_mem_for_sim(data_size=256, mode="behave_sim", asm="gelu", data=None, specified_data_order=["act_tensor"])

    # Save comparison parameters for view_mem.py
    import json
    result_vram_offset = 0  # In-place computation
    result_start_row = result_vram_offset // vlen
    num_result_rows = (batch_size * hidden_size) // vlen
    comparison_params = {
        "start_row_idx": result_start_row,
        "num_rows": num_result_rows,
        "num_batches": batch_size,
        "elements_per_batch": hidden_size
    }
    build_dir = Path(__file__).parent / "build"
    with open(build_dir / "comparison_params.json", "w") as f:
        json.dump(comparison_params, f, indent=2)

    print("================================================")
    print("Finished generating GELU test assembly code")
    print(f"Result location: row {result_start_row}, {num_result_rows} rows")
    print(f"Comparison params: {comparison_params}")
    print("================================================")
