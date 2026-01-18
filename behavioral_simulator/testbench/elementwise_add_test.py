import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import argparse
import torch
from compiler.asm_templates import elementwise_add_asm, preload_act_asm, reset_reg_asm, preload_addr_reg_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim
from quant.quantizer.hardware_quantizer.mxfp import _mx_fp_quantize_hardware
from config_utils import update_plena_config, get_comparison_params


def quantize_to_mxfp(tensor):
    """
    Quantize tensor to MXFP format matching hardware (E4M3 with 8-bit scale per block of 8).
    Uses the same quantizer as the behavioral simulator's memory loader.
    Returns the dequantized tensor (what hardware sees after HBM->VRAM load).
    """
    orig_shape = tensor.shape
    bm_x, _, _, _ = _mx_fp_quantize_hardware(
        tensor, width=8, exponent_width=4, exponent_bias_width=8, block_size=[8]
    )
    return bm_x.reshape(orig_shape)


if __name__ == "__main__":
    # Elementwise add: current activation + previous activation
    parser = argparse.ArgumentParser(description="Elementwise add testbench configuration")
    parser.add_argument("--hidden-size", type=int, default=128, help="Hidden size (elements per batch)")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size")
    parser.add_argument("--vlen", type=int, default=64, help="Vector length")
    parser.add_argument("--mlen", type=int, default=64, help="Matrix tile length (defaults to vlen)")
    parser.add_argument("--blen", type=int, default=4, help="Batch tile length")
    args = parser.parse_args()

    hidden_size = args.hidden_size
    batch_size = args.batch_size
    real_data_ratio = (8*8 + 8) / (8 * 8)
    fp_preload = [0.0]
    vlen = args.vlen
    mlen = args.mlen
    blen = args.blen
    hbm_m_prefetch_amount = mlen

    torch.manual_seed(42)
    act_tensor = torch.randn(batch_size, hidden_size, dtype=torch.bfloat16)
    prev_tensor = torch.randn(batch_size, hidden_size, dtype=torch.bfloat16)

    # Quantize inputs to MXFP to match hardware precision
    act_mxfp = quantize_to_mxfp(act_tensor).to(act_tensor.dtype)
    prev_mxfp = quantize_to_mxfp(prev_tensor).to(act_tensor.dtype)

    # Compute golden with MXFP-quantized inputs
    original_output = act_mxfp + prev_mxfp

    input_tensor = {
        "act_tensor": act_tensor,
        "prev_tensor": prev_tensor,
    }

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": original_output
    }

    gen_assembly_code = "; Elementwise Add Test Generation\n"
    gen_assembly_code += f"; Shape: ({batch_size}, {hidden_size})\n"

    # Calculate HBM offsets
    # Layout in HBM: [current activation | previous activation]
    act_hbm_size = int(hidden_size * batch_size * real_data_ratio)
    prev_hbm_offset = act_hbm_size

    # Set the addr offset for previous activation in HBM
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1],
        available_registers=[1],
        addr_reg_val=[prev_hbm_offset]
    )

    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3,4,5]
    )

    # Preload current activation into VRAM
    gen_assembly_code += preload_act_asm(
        vlen=vlen,
        preload_len=4,
        batch=batch_size,
        hidden_size=hidden_size,
        alive_registers=[1,2,3,4,5],
        act_vram_offset=0,
        activation_offset_reg=0,
        stride_size=hidden_size
    )

    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3,4,5]
    )

    # Place previous activation after current activation in VRAM
    previous_activation_base_address = hidden_size * batch_size

    gen_assembly_code += elementwise_add_asm(
        vlen=vlen,
        batch=batch_size,
        hidden_size=hidden_size,
        alive_registers=[1,2,3],
        stored_activation_base_address=0,
        previous_activation_base_address=previous_activation_base_address,
        previous_act_on_chip_addr_reg_index=1
    )

    # Update plena_settings.toml with test-specific vlen/mlen/blen and prefetch amount
    update_plena_config(
        vlen=vlen,
        mlen=mlen,
        blen=blen,
        hbm_m_prefetch_amount=hbm_m_prefetch_amount
    )

    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    create_mem_for_sim(
        data_size=256,
        mode="behave_sim",
        asm="elementwise_add",
        data=None,
        specified_data_order=["act_tensor", "prev_tensor"]
    )

    # Save comparison parameters for view_mem.py
    import json
    result_vram_offset = 0  # activation_base_address
    comparison_params = get_comparison_params(
        vlen=vlen,
        batch_size=batch_size,
        hidden_size=hidden_size,
        result_vram_offset=result_vram_offset
    )
    build_dir = Path(__file__).parent / "build"
    with open(build_dir / "comparison_params.json", "w") as f:
        json.dump(comparison_params, f, indent=2)

    print("================================================")
    print("Finished generating elementwise add assembly code")
    print(f"Result location: row {comparison_params['start_row_idx']}, {comparison_params['num_rows']} rows")
    print(f"Comparison params: {comparison_params}")
    print("================================================")
