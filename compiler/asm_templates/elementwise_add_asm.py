import os
from typing import Dict, List, Any, Optional
from pathlib import Path



def elementwise_add_asm(
    vlen: int,
    batch: int,
    hidden_size: int,
    alive_registers: List[int],
    stored_activation_base_address: int,
    previous_activation_base_address: int,
    previous_act_on_chip_addr_reg_index: int
) -> str:
    """
    Generates assembly code for vector elementwise add operation.
    assuming the prevous layer's activation is stored in the HBM
    Args:
        vlen (int): The number of rows in the vector.
    Returns:
        str: elementwise add, previous layer's activation add with the current layer's activation.
    """
    generated_code = "elementwise_add_asm generation \n"
    

    per_tile_offset = hidden_size
    previous_act_offset = alive_registers[0]
    previous_act_on_chip_addr = alive_registers[1]  
    load_v_on_chip_addr = alive_registers[2]

    generated_code += f"S_ADDI_INT {previous_act_offset}, gp0, 0 \n"
    generated_code += f"S_ADDI_INT {load_v_on_chip_addr}, gp0, {stored_activation_base_address} \n"
    generated_code += f"S_ADDI_INT {previous_act_on_chip_addr}, gp0, {previous_activation_base_address} \n"

    for i in range(batch):
        generated_code += f"H_PREFETCH_V {previous_act_on_chip_addr}, {previous_act_offset}, {previous_act_on_chip_addr_reg_index}, 0, 0 \n" 
        generated_code += f"V_ADD_VV {load_v_on_chip_addr}, {previous_act_on_chip_addr}, {load_v_on_chip_addr} \n"
        generated_code += f"S_ADDI_INT {previous_act_offset}, {previous_act_offset}, {per_tile_offset} \n"
        generated_code += f"S_ADDI_INT {previous_act_on_chip_addr}, {previous_act_on_chip_addr}, {per_tile_offset} \n"

    return generated_code
