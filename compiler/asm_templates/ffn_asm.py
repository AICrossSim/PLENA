import os
from typing import Dict, List, Any, Optional
from pathlib import Path



def ffn_asm(
    mlen: int,
    blen: int,
    batch: int,
    hidden_size: int,
    alive_registers: List[int],
    weight_hbm_offset_reg: int,
    intermediate_size: int,
    const_address: int,
    activation_base_address: int,
    result_base_address: int
) -> str:
    """
    Generates assembly code for a general matrix multiplication operation.

    Args:
        mlen (int): The number of rows in the first matrix.
        blen (int): The number of columns in the second matrix.
        alive_registers (List[int]): List of registers that are alive.
        rope_base_address (int): index for the address mapper pointing to the base addr of the rope matrix.
        activation_base_address (int): index for the address mapper pointing to the base addr of the activation matrix.
    Functionality:
        Upsize linear   (b, s, hidden_size) @ (hidden_size, intermediate_size) - > (b, s, intermediate_size)
        Activation      (b, s, intermediate_size) -> (b, s, intermediate_size)
        Downsize linear (b, s, intermediate_size) @ (intermediate_size, hidden_size) -> (b, s, hidden_size)
    """
    generated_code = " ; FFN Upsize Linear Generation \n"
    # Dot product of weight (Hidden Size, Hidden Size) and activation (Batch, 1, Hidden Size)
    assert batch < blen, "Batch size must be greater than blen"
    # get two registers from alive_registers, 1 as w address, 1 as a address
    w_base_register = alive_registers[0]
    a_base_register = alive_registers[1]
    result_register = alive_registers[2]
    w_actual_register = alive_registers[3]
    a_actual_register = alive_registers[4]
    intermediate_register = alive_registers[5]
    # reset the registers
    set_w_base_register  = f"S_ADDI_INT gp{w_base_register}, gp0, 0 \n"
    set_a_base_address   = f"S_ADDI_INT gp{a_base_register}, gp0, {activation_base_address} \n"
    set_result_address   = f"S_ADDI_INT gp{result_register}, gp0, {result_base_address} \n"

    set_w_actual_address = f"S_ADD_INT gp{w_actual_register}, gp0, {w_base_register} \n"
    set_a_actual_address = f"S_ADD_INT gp{a_actual_register}, gp0, {a_base_register} \n"

    increment_result_actual_address = f"S_ADDI_INT gp{result_register}, gp{result_register}, {mlen} \n"

    row_loop_over_hid = intermediate_size // blen
    vect_loop_over_hid = intermediate_size // vlen
    col_loop_over_hid = hidden_size // mlen
    generated_code += set_w_base_register
    generated_code += set_a_base_address
    generated_code += set_result_address
    
    generated_code += f"PREFETECH_M {w_actual_register}, gp0, a{weight_hbm_offset_reg}, 1, 0 \n"
    for i in range(row_loop_over_hid):
        generated_code += f"; <---- Generating New Row Tile at index {i} ----> \n"
        for j in range(col_loop_over_hid):
            generated_code += f"; <---- Generating New Column Tile at row {i} col {j} ----> \n"
            generated_code += f"M_MM 0, {w_actual_register}, {a_actual_register} \n"
            generated_code += set_w_actual_address
            generated_code += set_a_actual_address
        generated_code += f"M_MM_WO {result_register}, 0, 0 \n"
        if (i % blen) == 0:
            generated_code += increment_result_actual_address
    
    generated_code += "; SILU Generation \n"
    fp_const_reg = "f1"
    generated_code += f"S_LD_FP {fp_const_reg}, gp0, {const_address} \n"
    for i in range(vect_loop_over_hid):
        generated_code += f"; <---- per VLEN block {i} ----> \n"
        generated_code += f"V_SUB_VV {intermediate_register}, {intermediate_register}, {result_register} \n"
        generated_code += f"V_EXP_V  {intermediate_register}, {intermediate_register} \n"
        generated_code += f"V_ADD_VF {intermediate_register}, {intermediate_register}, {fp_const_reg} \n"
        generated_code += f"V_ADD_VF {intermediate_register}, {intermediate_register}, {fp_const_reg} \n"
        generated_code += f"V_REC_V  {intermediate_register}, {intermediate_register} \n"
        generated_code += f"V_MUL_VV {result_register}, {result_register}, {intermediate_register} \n"


    generated_code += "; FFN Downsize Linear Generation \n"

    row_loop_over_hid = hidden_size // blen
    col_loop_over_hid = intermediate_size // mlen

    for i in range(row_loop_over_hid):
        generated_code += f"; <---- Generating New Row Tile at index {i} ----> \n"
        for j in range(col_loop_over_hid):
            generated_code += f"; <---- Generating New Column Tile at row {i} col {j} ----> \n"
            generated_code += f"M_MM 0, {w_actual_register}, {result_register} \n"
            generated_code += set_w_actual_address
            generated_code += set_result_address
        generated_code += f"M_MM_WO {a_actual_register}, 0, 0 \n"
        if (i % blen) == 0:
            generated_code += set_a_actual_address

    return generated_code
