import os
from typing import Dict, List, Any, Optional
from pathlib import Path

def projection_asm(
    mlen: int,
    blen: int,
    batch: int,
    hidden_size: int,
    alive_registers: List[int],
    head_dim: int,
    w_base_hbm_offset_reg: int,
    rope_hbm_offset_reg: int,
    rope_on_chip_address: int,
    activation_base_address: int,
    result_base_address: int,
    rope_enabled: bool = True
) -> str:
    """
    Generates assembly code for a general matrix multiplication operation.
    (Batch, Hidden Size) @ (Hidden Size, Hidden Size) -> (Batch, Hidden Size)

    Args:
        mlen (int): The number of rows in the first matrix.
        blen (int): The number of columns in the second matrix.
        alive_registers (List[int]): List of registers that are alive.
        weight_base_address (int): index for the address mapper pointing to the base addr of the weight matrix.
        rope_base_address (int): index for the address mapper pointing to the base addr of the rope matrix.
        activation_base_address (int): addr pointing to the addr of activations in the vector sram.
    Returns:
        str: Generated assembly code for projection, including dot product and RoPE(cond)
    """
    generated_code = ""
    assert batch <= blen, "Batch size must be less than blen"
    # get two registers from alive_registers, 1 as w address, 1 as a address
    result_register     = alive_registers[0]
    w_actual_register   = alive_registers[1]
    a_actual_register   = alive_registers[2]

    # Set scale offset
    generated_code += f"S_ADDI_INT gp{a_actual_register}, gp0, {hidden_size * hidden_size} \n"
    generated_code += f"C_SET_SCALE_REG gp{a_actual_register} \n"

    # reset the registers
    set_a_base_address   = f"S_ADDI_INT gp{a_actual_register}, gp0, {activation_base_address} \n"
    set_result_address   = f"S_ADDI_INT gp{result_register}, gp0, {result_base_address} \n"
    increment_w_actual_address = f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {mlen * blen} \n"
    increment_a_actual_address = f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {mlen * blen} \n"
    increment_result_actual_address = f"S_ADDI_INT gp{result_register}, gp{result_register}, {blen * blen} \n"

    row_loop_over_hid = hidden_size // blen
    col_loop_over_hid = hidden_size // mlen
    generated_code += set_a_base_address
    generated_code += set_result_address

    for i in range(row_loop_over_hid):
        generated_code += f"; <---- Generating New Row Tile at index {i} ----> \n"
        generated_code += f"H_PREFETCH_M gp{w_actual_register}, gp{w_actual_register}, a{w_base_hbm_offset_reg}, 0, 0 \n"
        for j in range(col_loop_over_hid):
            generated_code += f"; <---- Generating New Column Tile at row {i} col {j} \n"
            generated_code += f"M_MM 0, gp{w_actual_register}, gp{a_actual_register} \n"
            generated_code += increment_w_actual_address
            generated_code += increment_a_actual_address
        generated_code += f"M_MM_WO {result_register}, 0, 0 \n"
        generated_code += set_a_base_address
        generated_code += increment_result_actual_address
        break
    
    # RoPE
    if rope_enabled:
        generated_code += "; Generating RoPE code here \n"
        generated_code += set_result_address 
        
        upper_base_register = alive_registers[0]
        lower_base_register = alive_registers[1]
        roped_upper_base_register = alive_registers[2]
        roped_lower_base_register = alive_registers[3]
        cos_base_register = alive_registers[4]
        sin_base_register = alive_registers[5]
        intermediate_1_register = alive_registers[6]
        intermediate_2_register = alive_registers[7]

        generated_code += f"S_ADDI_INT      gp{cos_base_register}, gp0, {rope_on_chip_address} \n"
        generated_code += f"H_PREFETCH_V    gp{cos_base_register}, gp{rope_on_chip_address}, a{rope_hbm_offset_reg}, 0, 0 \n"
        generated_code += f"S_ADDI_INT      gp{sin_base_register}, gp{cos_base_register}, {head_dim} \n"
        generated_code += f"H_PREFETCH_V    gp{sin_base_register}, gp{rope_on_chip_address}, a{rope_hbm_offset_reg}, 0, 0 \n"

        for i in range(batch * head_dim):
            generated_code += f"; <---- Generating RoPE code for batch {i // head_dim} head {i % head_dim} ----> \n"
            generated_code += f"V_MUL_VV gp{intermediate_1_register}, gp{upper_base_register}, gp{cos_base_register} \n"
            generated_code += f"V_MUL_VV gp{intermediate_2_register}, gp{lower_base_register}, gp{sin_base_register} \n"
            generated_code += f"V_SUB_VV gp{roped_upper_base_register}, gp{intermediate_1_register}, gp{intermediate_2_register} \n"
            generated_code += f"V_MUL_VV gp{intermediate_1_register}, gp{upper_base_register}, gp{sin_base_register} \n"
            generated_code += f"V_MUL_VV gp{intermediate_2_register}, gp{lower_base_register}, gp{cos_base_register} \n"
            generated_code += f"V_ADD_VV gp{roped_lower_base_register}, gp{intermediate_1_register}, gp{intermediate_2_register} \n"
            generated_code += f"S_ADDI_INT gp{upper_base_register}, gp{upper_base_register}, {mlen} \n"
            generated_code += f"S_ADDI_INT gp{lower_base_register}, gp{lower_base_register}, {mlen} \n"
            generated_code += f"S_ADDI_INT gp{roped_upper_base_register}, gp{roped_upper_base_register}, {mlen} \n"
            generated_code += f"S_ADDI_INT gp{roped_lower_base_register}, gp{roped_lower_base_register}, {mlen} \n"

    return generated_code
