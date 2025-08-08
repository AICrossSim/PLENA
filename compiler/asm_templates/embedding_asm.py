import os
from typing import Dict, List, Any, Optional
from pathlib import Path



def embedding_asm(
    vlen: int,
    batch: int,
    alive_registers: List[int],
    voc_table_row_size: int,
    activation_base_address: int,
    voc_table_base_addr_reg_index: int,
    input_ids: list[int]
) -> str:
    """
    Generates assembly code for embedding lookup operation.
    Returns:
        str: elementwise add, previous layer's activation add with the current layer's activation.
    """
    assert len(input_ids) == batch, "Input IDs length must match batch"
    generated_code = "; Embedding_asm generation \n"
    indx_reg = alive_registers[0]
    table_entry_addr = alive_registers[1] 
    load_v_on_chip_addr = alive_registers[2]

    generated_code += f"S_ADDI_INT gp{table_entry_addr}, gp0, {voc_table_row_size} \n"
    generated_code += f"S_ADDI_INT gp{load_v_on_chip_addr}, gp0, {activation_base_address} \n"

    for i in range(batch):
        input_id = input_ids[i]
        generated_code += f"S_ADDI_INT gp{indx_reg}, gp0, {input_id} \n"
        generated_code += f"S_MUL_INT gp{indx_reg}, gp{indx_reg}, gp{table_entry_addr} \n"
        generated_code += f"H_PREFETCH_V gp{load_v_on_chip_addr}, gp{indx_reg}, a{voc_table_base_addr_reg_index}, 0, 0 \n" 
        generated_code += f"S_ADDI_INT gp{load_v_on_chip_addr}, {load_v_on_chip_addr}, {vlen} \n"

    return generated_code
