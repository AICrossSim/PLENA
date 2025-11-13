import os
from typing import Dict, List, Any, Optional
from pathlib import Path



def select_vvm_debug(
    alive_registers: List[int],
    activation_base_address: int,
    activation2_base_address: int,
    activation3_base_address: int,
    scratchpad_base_address: int,
    vlen: int,
    batch_size: int,
) -> str:
    """
    Generate assembly code for element-wise select operation (V_SELECT_VVM).
    Loops over batch_size rows to perform: output[i] = mask[i] ? input1[i] : input2[i]
    """
    act_addr = alive_registers[0]
    act2_addr = alive_registers[1]
    act3_addr = alive_registers[2]
    scratchpad_addr = alive_registers[3]

    generated_code = "; V_SELECT_VVM generation \n"
    generated_code += f"S_ADDI_INT gp{act_addr}, gp0, {activation_base_address} \n"
    generated_code += f"S_ADDI_INT gp{act2_addr}, gp0, {activation2_base_address} \n"
    generated_code += f"S_ADDI_INT gp{act3_addr}, gp0, {activation3_base_address} \n"
    generated_code += f"S_ADDI_INT gp{scratchpad_addr}, gp0, {scratchpad_base_address} \n"

    # Loop over batch_size rows
    for _ in range(batch_size):
        # out = select vvm: out[i] = mask[i] != 0 ? input1[i] : input2[i]
        generated_code += f"V_SELECT_VVM gp{scratchpad_addr}, gp{act_addr}, gp{act2_addr}, gp{act3_addr} \n"
        
        # Increment all address pointers by vlen (move to next row)
        generated_code += f"S_ADDI_INT gp{act_addr}, gp{act_addr}, {vlen} \n"
        generated_code += f"S_ADDI_INT gp{act2_addr}, gp{act2_addr}, {vlen} \n"
        generated_code += f"S_ADDI_INT gp{act3_addr}, gp{act3_addr}, {vlen} \n"
        generated_code += f"S_ADDI_INT gp{scratchpad_addr}, gp{scratchpad_addr}, {vlen} \n"

    return generated_code