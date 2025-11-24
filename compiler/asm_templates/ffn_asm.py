import os
from typing import Dict, List, Any, Optional
from pathlib import Path

IMM2_BOUND = 2**18

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
    
    activation_base_address: int
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
    

    # memory assignment
    # 0 -> activation
    # b * s * hidden_size -> upsize intermediate results
    # b * s * (hidden_size + intermediate_size) -> gate projection results

    w_actual_register = alive_registers[0]
    a_actual_register = alive_registers[1]
    up_result_register = alive_registers[2]
    intermediate_register = alive_registers[3]
    gate_result_register = alive_registers[4]

    # reset the registers
    generated_code = "; FFN Generation \n"

    # Settings for up and gate weight matrices prefetching
    assert hidden_size * intermediate_size < IMM2_BOUND, f"hidden_size * hidden_size must be less than {IMM2_BOUND}"
    generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, {hidden_size * intermediate_size} \n"
    generated_code += f"C_SET_SCALE_REG gp{w_actual_register} \n"
    generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, {intermediate_size} \n"
    generated_code += f"C_SET_STRIDE_REG gp{w_actual_register} \n"
    generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, 0 \n"
    assert hidden_size * batch * seq_len < IMM2_BOUND, f"hidden_size * batch * seq_len must be less than {IMM2_BOUND}"
    generated_code += f"S_ADDI_INT gp{up_result_register}, gp0, {batch * seq_len * hidden_size} \n"
    generated_code += f"S_ADDI_INT gp{gate_result_register}, gp{up_result_register}, {intermediate_size * batch * seq_len} \n"

    generated_code = " ; FFN Upsize Linear Generation \n"
    for weight_row in range (intermediate_size // blen):
        if weight_row % (mlen // blen) == 0:
            for weight_col in range (hidden_size // mlen):
                generated_code += f"H_PREFETCH_M gp{w_actual_register}, gp{w_actual_register}, a{up_weight_hbm_offset_reg}, 1, 0 \n"
                generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {mlen * mlen} \n"
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, 0 \n"
        for act_col in range (batch * seq_len // blen):
            generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{up_result_register}, {activation_base_address + act_col * hidden_size * blen} \n"
            for inner_loop_index in range (hidden_size // mlen):
                generated_code += f"M_MM 0, gp{w_actual_register}, gp{a_actual_register} \n"
                generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {mlen * mlen} \n"
                generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {mlen * blen} \n"
            generated_code += f"S_ADDI_INT gp{intermediate_register}, gp{up_result_register}, {act_col * batch * seq_len * intermediate_size + weight_row * blen} \n"
            generated_code += f"M_MM_WO gp{intermediate_register}, gp0, 0 \n"
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {weight_row * blen} \n"


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
                generated_code += f"M_MM gp0, gp{w_actual_register}, gp{a_actual_register} \n"
                generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {mlen * mlen} \n"
                generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {mlen * blen} \n"
            generated_code += f"S_ADDI_INT gp{intermediate_register}, gp{gate_result_register}, {act_col * batch * seq_len * intermediate_size + weight_row * blen} \n"
            generated_code += f"M_MM_WO gp{intermediate_register}, gp0, 0 \n"
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {hidden_size * blen} \n"

    # Hidden Size SILU Activation Generation
    generated_code += "; SILU Generation \n"
    generated_code += f"S_LD_FP f1, gp0, {const_one_fp_address} \n"
    generated_code += f"S_ADDI_INT gp{intermediate_register}, gp{gate_result_register}, 0 \n"
    for i in range(intermediate_size // vlen):
        # 0 : -x
        generated_code += f"V_SUB_VF gp{intermediate_register}, gp{intermediate_register}, f0, 0, 1 \n"
        # 1 : exp(-x)
        generated_code += f"V_EXP_V  gp{intermediate_register}, gp{intermediate_register}, 0 \n"
        # 2 : 1 + exp(-x)
        generated_code += f"V_ADD_VF gp{intermediate_register}, gp{intermediate_register}, f1, 0 \n"
        # 3 : 1 / (1 + exp(-x))
        generated_code += f"V_RECI_V  gp{intermediate_register}, gp{intermediate_register}, 0 \n"
        # 4 : (1 / (1 + exp(-x))) * gate_result
        generated_code += f"V_MUL_VV gp{intermediate_register}, gp{intermediate_register}, gp{gate_result_register}, 0 \n"
        generated_code += f"S_ADDI_INT gp{gate_result_register}, gp{gate_result_register}, {vlen} \n"


    generated_code += "; FFN Downsize Linear Generation \n"
    generated_code += f"S_ADDI_INT gp{intermediate_register}, gp{gate_result_register}, 0 \n"
    for weight_row in range (hidden_size // blen):
        if weight_row % (mlen // blen) == 0:
            for weight_col in range (intermediate_size // mlen):
                generated_code += f"H_PREFETCH_M gp{w_actual_register}, gp{w_actual_register}, a{down_weight_hbm_offset_reg}, 1, 0 \n"
                generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {mlen * mlen} \n"
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, 0 \n"
        for act_col in range (batch * seq_len // blen):
            generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{intermediate_register}, {act_col * hidden_size * blen} \n"
            for inner_loop_index in range (intermediate_size // mlen):
                generated_code += f"M_MM 0, gp{w_actual_register}, gp{a_actual_register} \n"
                generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {mlen * mlen} \n"
                generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {mlen * blen} \n"
            generated_code += f"S_ADDI_INT gp{intermediate_register}, gp0, {activation_base_address + act_col * batch * seq_len * hidden_size + weight_row * blen} \n"
            generated_code += f"M_MM_WO gp{intermediate_register}, gp0, 0 \n"
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {intermediate_register * blen} \n"

    return generated_code
