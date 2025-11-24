import os
from typing import Dict, List, Any, Optional
from pathlib import Path

def rms_norm_asm(
    _eps_offset: int,
    reci_hid_offset: int,
    alive_registers: List[int],
    activation_base_address: int,
    scratchpad_base_address: int,
    vlen: int,
    batch_size: int,
    hidden_dim: int
) -> str:
    """
    Generate assembly code for L2 normalization.
    """
    act_addr = alive_registers[0]
    scratchpad_addr = alive_registers[1]

    generated_code = "; RMS Norm generation \n"
    generated_code += f"S_ADDI_INT gp{act_addr}, gp0, {activation_base_address} \n"
    generated_code += f"S_ADDI_INT gp{scratchpad_addr}, gp0, {scratchpad_base_address} \n"

    # Load eps into f1
    generated_code += f"S_LD_FP f1, gp0, {_eps_offset} \n"
    # Reset f2 as accumulator for reduction.
    generated_code += "S_ADD_FP f2, f0, f0 \n"
    # Load the 1/ hidden_dim into f3
    generated_code += f"S_LD_FP f3, gp0, {reci_hid_offset} \n"
    for batch in range(batch_size):
        for i in range(hidden_dim // vlen):
            # Compute square of the activation vector and summation
            generated_code += f"V_MUL_VV gp{scratchpad_addr}, gp{act_addr}, gp{act_addr}, 0 \n"
            generated_code += f"V_RED_SUM f2, gp{scratchpad_addr} \n"

            # Move to next vector
            generated_code += f"S_ADDI_INT gp{act_addr}, gp{act_addr}, {vlen * batch_size} \n"

        # Taking the avg
        generated_code += f"S_MUL_FP f2, f2, f3 \n"

        # Plus epsilon
        generated_code += f"S_ADD_FP f2, f2, f1 \n"

        # Compute square root
        generated_code += "S_SQRT_FP f2, f2 \n"

        # Compute reciprocal
        generated_code += "S_RECI_FP f2, f2 \n"

        for i in range(hidden_dim // vlen):
            # Normalize the activation vector
            generated_code += f"V_MUL_VF gp{act_addr}, gp{act_addr}, f2, 0 \n"

            # Move to next vector
            generated_code += f"S_ADDI_INT gp{act_addr}, gp{act_addr}, {vlen * batch_size} \n"

        generated_code += "S_ADD_FP f2, f0, f0 \n"
        generated_code += f"S_ADDI_INT gp{act_addr}, gp0, {activation_base_address + vlen * batch} \n"
    return generated_code