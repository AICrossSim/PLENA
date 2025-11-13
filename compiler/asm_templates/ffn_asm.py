import os
from typing import Dict, List, Any, Optional
from pathlib import Path


def ffn_asm(
    mlen: int,
    vlen: int,
    blen: int,
    batch: int,
    seq_len: int,
    hidden_size: int,
    intermediate_size: int,

    alive_registers: List[int],
    gate_weight_hbm_offset_reg: int,
    up_weight_hbm_offset_reg: int,
    down_weight_hbm_offset_reg: int,
    const_one_fp_address: int,
    
    w_prefetch_amount: int,
    activation_base_address: int,
    result_base_address: int
) -> str:
    """
    Generates assembly code for a FFN operation.

    Args:
        mlen (int): The number of rows in the matrix.
        vlen (int): The number of columns in the matrix.
        blen (int): The number of columns in the second matrix.
        batch (int): The number of batches.
        hidden_size (int): The number of rows in the hidden size.
        intermediate_size (int): The number of rows in the intermediate size.
        alive_registers (List[int]): List of registers that are alive.
        gate_weight_hbm_offset_reg (int): index for the address mapper pointing to the base addr of the gate weight matrix.
        up_weight_hbm_offset_reg (int): index for the address mapper pointing to the base addr of the up weight matrix.
        down_weight_hbm_offset_reg (int): index for the address mapper pointing to the base addr of the down weight matrix.
        activation_base_address (int): index for the address mapper pointing to the base addr of the activation matrix.
        result_base_address (int): index for the address mapper pointing to the base addr of the result matrix.
    Functionality:
        Upsize linear   (b, s, hidden_size) @ (hidden_size, intermediate_size) - > (b, s, intermediate_size)
        Gate Projection (b, s, hidden_size) @ (hidden_size, intermediate_size) -> (b, s, intermediate_size)
        SILU Activation (b, s, intermediate_size) -> (b, s, intermediate_size)
        Downsize linear (b, s, intermediate_size) @ (intermediate_size, hidden_size) -> (b, s, hidden_size)
    """
    
    # Dot product of weight (Hidden Size, Hidden Size) and activation (Batch, 1, Hidden Size)
    # get two registers from alive_registers, 1 as w address, 1 as a address

    w_actual_register = alive_registers[0]
    a_actual_register = alive_registers[1]
    result_register = alive_registers[2]
    intermediate_register = alive_registers[3]

    # reset the registers
    generated_code = "; FFN Generation \n"

    # Settings
    generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, {hidden_size * intermediate_size} \n"
    generated_code += f"C_SET_SCALE_REG gp{w_actual_register} \n"
    generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, {intermediate_size} \n"
    generated_code += f"C_SET_STRIDE_REG gp{w_actual_register} \n"
    generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, 0 \n"

    generated_code = " ; FFN Upsize Linear Generation \n"
    for weight_row in range (intermediate_size // blen):
        if weight_row % (mlen // blen) == 0:
            for weight_col in range (hidden_size // mlen):
                generated_code += f"H_PREFETCH_M gp{w_actual_register}, gp{w_actual_register}, a{up_weight_hbm_offset_reg}, 1, 0 \n"
                generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {mlen * mlen} \n"
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, 0 \n"
        for act_col in range (batch * seq_len // blen):
            generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {activation_base_address + act_col * hidden_size * blen} \n"
            for inner_loop_index in range (hidden_size // mlen):
                generated_code += f"M_MM 0, gp{w_actual_register}, gp{a_actual_register} \n"
                generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {mlen * mlen} \n"
                generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {mlen * blen} \n"
            generated_code += f"M_MM_WO gp{result_register}, 0, 0 \n"
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {hidden_size * blen} \n"


    generated_code = " ; FFN Gate Projection Generation \n"
    for weight_row in range (intermediate_size // blen):
        if weight_row % (mlen // blen) == 0:
            for weight_col in range (hidden_size // mlen):
                generated_code += f"H_PREFETCH_M gp{w_actual_register}, gp{w_actual_register}, a{gate_weight_hbm_offset_reg}, 1, 0 \n"
                generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {mlen * mlen} \n"
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, 0 \n"
        for act_col in range (batch * seq_len // blen):
            generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {activation_base_address + act_col * hidden_size * blen} \n"
            for inner_loop_index in range (hidden_size // mlen):
                generated_code += f"M_MM 0, {w_actual_register}, {a_actual_register} \n"
                generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {mlen * mlen} \n"
                generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {mlen * blen} \n"
            generated_code += f"M_MM_WO {result_register}, 0, 0 \n"
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {hidden_size * blen} \n"

    # Hidden Size SILU Activation Generation
    generated_code += "; SILU Generation \n"
    generated_code += f"S_LD_FP f1, gp0, {const_one_fp_address} \n"
    for i in range(intermediate_size // vlen):
        generated_code += f"V_SUB_VV gp{intermediate_register}, gp{intermediate_register}, gp{result_register} \n"
        generated_code += f"V_EXP_V  gp{intermediate_register}, gp{intermediate_register} \n"
        generated_code += f"V_ADD_VF gp{intermediate_register}, gp{intermediate_register}, f1 \n"
        generated_code += f"V_ADD_VF gp{intermediate_register}, gp{intermediate_register}, f1 \n"
        generated_code += f"V_REC_V  gp{intermediate_register}, gp{intermediate_register} \n"
        generated_code += f"V_MUL_VV gp{result_register}, gp{result_register}, gp{intermediate_register} \n"


    generated_code += "; FFN Downsize Linear Generation \n"

    row_loop_over_hid = hidden_size // blen
    col_loop_over_hid = intermediate_size // mlen

    # for i in range(row_loop_over_hid):
    #     generated_code += f"; <---- Generating New Row Tile at index {i} ----> \n"
    #     for j in range(col_loop_over_hid):
    #         generated_code += f"; <---- Generating New Column Tile at row {i} col {j} ----> \n"
    #         generated_code += f"M_MM 0, {w_actual_register}, {result_register} \n"
    #         generated_code += set_w_actual_address
    #         generated_code += set_result_address
    #     generated_code += f"M_MM_WO {a_actual_register}, 0, 0 \n"
    #     if (i % blen) == 0:
    #         generated_code += set_a_actual_address

    return generated_code
