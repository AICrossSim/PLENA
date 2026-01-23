import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import argparse
import torch
from torch import Tensor, nn
from compiler.asm_templates import batched_matmul_asm, preload_addr_reg_asm, reset_reg_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim
from quant.quantizer.hardware_quantizer.mxfp import _mx_fp_quantize_hardware
from config_utils import update_plena_config


def quantize_to_mxfp(tensor):
    """
    Quantize tensor to MXFP format matching hardware (E4M3 with 8-bit scale per block of 8).
    """
    orig_shape = tensor.shape
    tensor_2d = tensor.reshape(-1, tensor.shape[-1])
    bm_x, _, _, _ = _mx_fp_quantize_hardware(
        tensor_2d, width=8, exponent_width=4, exponent_bias_width=8, block_size=[8]
    )
    return bm_x.reshape(orig_shape)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BatchMatMul test for behavioral simulator")
    parser.add_argument("--b", type=int, default=None, help="Batch size")
    parser.add_argument("--m", type=int, default=None, help="M dimension")
    parser.add_argument("--k", type=int, default=None, help="K dimension")
    parser.add_argument("--n", type=int, default=None, help="N dimension")
    parser.add_argument("--config", type=str, default="C1",
                        choices=["C1", "C2", "C3", "C4", "C5"],
                        help="PLENA workload config")
    args = parser.parse_args()

    # BMM workload configurations: (b, M, K, N)
    # Operation: (b, M, K) @ (b, K, N) -> (b, M, N)
    BMM_CONFIGS = {
        "C1": (4, 64, 64, 64),
        "C2": (8, 64, 128, 128),
        "C3": (16, 128, 128, 256),
        "C4": (32, 128, 256, 256),
        "C5": (64, 256, 256, 512),
    }

    # Use explicit args if provided, otherwise use config preset
    if args.b is not None and args.m is not None and args.k is not None and args.n is not None:
        batch_size, m, k, n = args.b, args.m, args.k, args.n
        print(f"Using custom config: b={batch_size}, M={m}, K={k}, N={n}")
    else:
        batch_size, m, k, n = BMM_CONFIGS[args.config]
        print(f"Using PLENA config {args.config}: b={batch_size}, M={m}, K={k}, N={n}")

    real_data_ratio = (8*8 + 8) / (8 * 8)
    fp_preload = [0.0]
    mlen = 64
    blen = 4
    vlen = 64

    torch.manual_seed(42)
    input_a = torch.randn(batch_size, m, k, dtype=torch.bfloat16)
    input_b = torch.randn(batch_size, k, n, dtype=torch.bfloat16)

    # Quantize inputs to MXFP to match hardware precision
    input_a_mxfp = quantize_to_mxfp(input_a).to(input_a.dtype)
    input_b_mxfp = quantize_to_mxfp(input_b).to(input_b.dtype)

    # Compute golden with MXFP-quantized inputs (float32 accumulation, then BF16 output)
    original_output = torch.bmm(input_a_mxfp.float(), input_b_mxfp.float()).to(torch.bfloat16)

    input_tensor = {
        "input_a": input_a_mxfp.reshape(batch_size * m, k),
        "input_b": input_b_mxfp.reshape(batch_size * k, n),
    }

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": original_output.flatten()
    }

    gen_assembly_code = "; BMM Test Generation \n"
    gen_assembly_code += f"; Shape: ({batch_size}, {m}, {k}) @ ({batch_size}, {k}, {n}) -> ({batch_size}, {m}, {n})\n"

    # Set the addr offset for input_b (after input_a)
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1],
        available_registers=[1],
        addr_reg_val=[int(m * k * batch_size * real_data_ratio)]
    )

    gen_assembly_code += reset_reg_asm(
        alive_registers=[1]
    )

    gen_assembly_code += batched_matmul_asm(
        mlen=mlen,
        blen=blen,
        b=batch_size,
        m=m,
        k=k,
        n=n,
        alive_registers=[1,2,3],
        w_base_hbm_offset_reg=1,
        w_prefetch_amount=k,
        a_base_hbm_offset_reg=0,
        a_prefetch_amount=4,
        result_base_address=0,
    )

    # Update plena_settings.toml with test-specific vlen/mlen
    update_plena_config(vlen=vlen, mlen=mlen)

    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    create_mem_for_sim(data_size=256, mode="behave_sim", asm="bmm", data=None, specified_data_order=["input_a", "input_b"])

    # Save comparison parameters for view_mem.py
    import json
    result_vram_offset = 0
    result_start_row = result_vram_offset // vlen
    num_result_rows = (batch_size * m * n) // vlen
    comparison_params = {
        "start_row_idx": result_start_row,
        "num_rows": num_result_rows,
        "num_batches": batch_size,
        "elements_per_batch": m * n
    }
    build_dir = Path(__file__).parent / "build"
    with open(build_dir / "comparison_params.json", "w") as f:
        json.dump(comparison_params, f, indent=2)

    print("================================================")
    print("Finished generating BMM test assembly code")
    print(f"Result location: row {result_start_row}, {num_result_rows} rows")
    print(f"Comparison params: {comparison_params}")
    print("================================================")
