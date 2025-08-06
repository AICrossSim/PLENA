import os
from typing import Dict, List, Any, Optional
from pathlib import Path



def projection_asm(
    mlen: int,
    blen: int,
    batch: int,
    hidden_size: int,
    alive_registers: List[int],
    weight_base_address: int,
    head_dim: int,
    cos_base_address: int,
    sin_base_address: int,
    rope_base_address: int,
    activation_addr_int_sram_index: int,
    activation_base_address: int,
    result_base_address: int,
    rope_enabled: bool = True
) -> str:
    """
    Generates assembly code for a general matrix multiplication operation.

    Args:
        mlen (int): The number of rows in the first matrix.
        blen (int): The number of columns in the second matrix.
        alive_registers (List[int]): List of registers that are alive.
        weight_base_address (int): index for the address mapper pointing to the base addr of the weight matrix.
        rope_base_address (int): index for the address mapper pointing to the base addr of the rope matrix.
        activation_base_address (int): index for the address mapper pointing to the base addr of the activation matrix.
    Returns:
        str: Generated assembly code for projection, including dot product and RoPE(cond)
    """
    generated_code = ""
    # Dot product of weight (Hidden Size, Hidden Size) and activation (Batch, 1, Hidden Size)
    assert batch > blen, "Batch size must be greater than blen"
    # get two registers from alive_registers, 1 as w address, 1 as a address
    w_base_register = alive_registers[0]
    a_base_register = alive_registers[1]
    result_register = alive_registers[2]
    w_actual_register = alive_registers[3]
    a_actual_register = alive_registers[4]
    # reset the registers
    set_w_base_register  = f"S_LD_INT {w_base_register}, gp0, {weight_base_address} \n"
    set_a_base_address   = f"S_LD_INT {a_base_register}, gp0, {activation_base_address} \n"
    set_result_address   = f"S_LD_INT {result_register}, gp0, {result_base_address} \n"

    set_w_actual_address = f"S_ADD_INT {w_actual_register}, gp0, {w_base_register} \n"
    set_a_actual_address = f"S_ADD_INT {a_actual_register}, gp0, {a_base_register} \n"
    increment_result_actual_address = f"S_ADD_INT {result_register}, gp0, {a_base_register} \n"

    row_loop_over_hid = hidden_size // blen
    col_loop_over_hid = hidden_size // mlen
    generated_code += set_w_base_register
    generated_code += set_a_base_address
    generated_code += set_result_address

    for i in range(row_loop_over_hid):
        generated_code += f"<---- Generating New Row Tile at index {i} ----> \n"
        for j in range(col_loop_over_hid):
            generated_code += f"<---- Generating New Column Tile at row {i} col {j} \n"
            generated_code += f"M_MM 0, {w_actual_register}, {a_actual_register} \n"
            generated_code += set_w_actual_address
            generated_code += set_a_actual_address
        generated_code += f"M_MM_WO {result_register}, 0, 0 \n"
    generated_code += increment_result_actual_address
    
    # RoPE
    if rope_enabled:
        generated_code += " Generating RoPE code here \n"
        generated_code += set_result_address 
        per_head_dim = hidden_size // head_dim
        num_mlen_per_head = per_head_dim // mlen
        
        upper_base_register = alive_registers[0]
        lower_base_register = alive_registers[1]
        roped_upper_base_register = alive_registers[2]
        roped_lower_base_register = alive_registers[3]
        cos_base_register = alive_registers[4]
        sin_base_register = alive_registers[5]
        intermediate_1_register = alive_registers[6]
        intermediate_2_register = alive_registers[7]


        generated_code += f"S_LD_INT {cos_base_register}, gp0, {cos_base_address} \n"
        generated_code += f"S_LD_INT {sin_base_register}, gp0, {sin_base_address} \n"

        for i in range(batch * head_dim):
            generated_code += f"<---- Generating RoPE code for batch {i // head_dim} head {i % head_dim} ----> \n"
            generated_code += f"V_MUL_VV {intermediate_1_register}, {upper_base_register}, {cos_base_register} \n"
            generated_code += f"V_MUL_VV {intermediate_2_register}, {lower_base_register}, {sin_base_register} \n"
            generated_code += f"V_SUB_VV {roped_upper_base_register}, {intermediate_1_register}, {intermediate_2_register} \n"
            generated_code += f"V_MUL_VV {intermediate_1_register}, {upper_base_register}, {sin_base_register} \n"
            generated_code += f"V_MUL_VV {intermediate_2_register}, {lower_base_register}, {cos_base_register} \n"
            generated_code += f"V_ADD_VV {roped_lower_base_register}, {intermediate_1_register}, {intermediate_2_register} \n"
            generated_code += f"S_ADDI_INT {upper_base_register}, {mlen} \n"
            generated_code += f"S_ADDI_INT {lower_base_register}, {mlen} \n"
            generated_code += f"S_ADDI_INT {roped_upper_base_register}, {mlen} \n"
            generated_code += f"S_ADDI_INT {roped_lower_base_register}, {mlen} \n"

    return generated_code
