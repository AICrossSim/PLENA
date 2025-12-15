import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import nn
from compiler.asm_templates import preload_act_asm, reset_reg_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim


def silu_asm(
    const_one_fp_address: int,
    alive_registers: list,
    activation_base_address: int,
    scratchpad_base_address: int,
    vlen: int,
    batch_size: int,
    hidden_dim: int
) -> str:
    """
    Generate assembly code for SiLU activation.
    SiLU(x) = x * sigmoid(x) = x * (1 / (1 + exp(-x)))
    """
    act_addr = alive_registers[0]
    scratchpad_addr = alive_registers[1]
    loop_reg = alive_registers[2]

    num_vectors = (batch_size * hidden_dim) // vlen

    generated_code = "; SiLU Activation Generation\n"
    generated_code += f"S_ADDI_INT gp{act_addr}, gp0, {activation_base_address}\n"
    generated_code += f"S_ADDI_INT gp{scratchpad_addr}, gp0, {scratchpad_base_address}\n"

    # Load constant 1.0 into f1
    generated_code += f"S_LD_FP f1, gp0, {const_one_fp_address}\n"

    generated_code += f"C_LOOP_START gp{loop_reg}, {num_vectors}\n"

    # SiLU computation: x * sigmoid(x) = x * (1 / (1 + exp(-x)))
    # Step 1: -x (negate using f0=0, with reverse order flag)
    generated_code += f"V_SUB_VF gp{scratchpad_addr}, gp{act_addr}, f0, 0, 1\n"
    # Step 2: exp(-x)
    generated_code += f"V_EXP_V gp{scratchpad_addr}, gp{scratchpad_addr}, 0\n"
    # Step 3: 1 + exp(-x)
    generated_code += f"V_ADD_VF gp{scratchpad_addr}, gp{scratchpad_addr}, f1, 0\n"
    # Step 4: 1 / (1 + exp(-x)) = sigmoid(x)
    generated_code += f"V_RECI_V gp{scratchpad_addr}, gp{scratchpad_addr}, 0\n"
    # Step 5: x * sigmoid(x) = silu(x), store in-place
    generated_code += f"V_MUL_VV gp{act_addr}, gp{scratchpad_addr}, gp{act_addr}, 0\n"

    # Move to next vector
    generated_code += f"S_ADDI_INT gp{act_addr}, gp{act_addr}, {vlen}\n"

    generated_code += f"C_LOOP_END gp{loop_reg}\n"

    return generated_code


if __name__ == "__main__":
    hidden_size = 128
    batch_size = 4
    vlen = 64

    # FP SRAM layout: [0]=0.0, [1]=1.0 (for sigmoid computation)
    fp_preload = [0.0, 1.0]

    torch.manual_seed(42)
    act_tensor = torch.randn(batch_size, hidden_size)

    print("Input tensor shape:", act_tensor.shape)
    print("Input tensor (first 8 values):", act_tensor[0, :8])

    # Compute golden output using PyTorch
    original_output = nn.functional.silu(act_tensor)

    print("Output tensor (first 8 values):", original_output[0, :8])

    input_tensor = {
        "act_tensor": act_tensor,
    }

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": original_output
    }

    gen_assembly_code = "; SiLU Test Generation\n"

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

    # SiLU computation
    gen_assembly_code += silu_asm(
        const_one_fp_address=1,
        alive_registers=[1, 2, 3, 4, 5],
        activation_base_address=0,
        scratchpad_base_address=hidden_size * batch_size,
        vlen=vlen,
        batch_size=batch_size,
        hidden_dim=hidden_size
    )

    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    create_mem_for_sim(data_size=256, mode="behave_sim", asm="silu", data=None, specified_data_order=["act_tensor"])

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
    print("Finished generating SiLU test assembly code")
    print(f"Result location: row {result_start_row}, {num_result_rows} rows")
    print(f"Comparison params: {comparison_params}")
    print("================================================")
