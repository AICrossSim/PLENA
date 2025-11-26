import os
from typing import Dict, List, Any, Optional
from pathlib import Path
import math
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
    w_temp_register = alive_registers[1]
    a_actual_register = alive_registers[2]
    up_result_register = alive_registers[3]
    intermediate_register = alive_registers[4]
    gate_result_register = alive_registers[5]
    w_hbm_offset_register = alive_registers[6]

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
    # Set the address for on-chip sram
    generated_code += f"S_ADDI_INT gp{up_result_register}, gp0, {batch * seq_len * hidden_size} \n"
    generated_code += f"S_ADDI_INT gp{gate_result_register}, gp{up_result_register}, {intermediate_size * batch * seq_len} \n"

    generated_code += " ; FFN Upsize Linear Generation \n"
    for weight_row in range (intermediate_size // blen):
        if weight_row % (mlen // blen) == 0:
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, 0 \n"
            generated_code += f"S_ADDI_INT gp{w_hbm_offset_register}, gp0, {weight_row * blen} \n"
            generated_code += f"S_ADDI_INT gp{intermediate_register}, gp{up_result_register}, 0 \n"
            
            for weight_col in range (hidden_size // mlen):
                generated_code += f"H_PREFETCH_M gp{w_actual_register}, gp{w_hbm_offset_register}, a{up_weight_hbm_offset_reg}, 1, 0 \n"
                generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {mlen * mlen} \n"
                generated_code += f"S_ADDI_INT gp{w_hbm_offset_register}, gp{w_hbm_offset_register}, {mlen * intermediate_size} \n"
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, 0 \n"
        else:
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, {(weight_row % (mlen // blen)) * blen} \n"
            generated_code += f"S_ADDI_INT gp{intermediate_register}, gp{up_result_register}, {(weight_row % (mlen // blen)) * blen} \n"
        for act_col in range ((batch * seq_len) // blen):
            generated_code += f"S_ADDI_INT gp{a_actual_register}, gp0, {activation_base_address + act_col * mlen * blen} \n"
            generated_code += f"S_ADDI_INT gp{w_temp_register}, gp{w_actual_register}, 0 \n"
            for inner_loop_index in range (hidden_size // mlen):
                generated_code += f"M_MM 0, gp{w_temp_register}, gp{a_actual_register} \n"
                generated_code += f"S_ADDI_INT gp{w_temp_register}, gp{w_temp_register}, {mlen * mlen} \n"
                generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {mlen * batch * seq_len} \n"
            generated_code += f"M_MM_WO gp{intermediate_register}, gp0, 0 \n"
            generated_code += f"S_ADDI_INT gp{intermediate_register}, gp{intermediate_register}, {blen * mlen} \n"    # generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {activation_base_address} \n"
        if (weight_row + 1) % (mlen // blen) == 0 and weight_row != intermediate_size // blen - 1:
            generated_code += f"S_ADDI_INT gp{up_result_register}, gp{up_result_register}, {mlen * batch * seq_len} \n"

    generated_code += " ; FFN Gate Projection Generation \n"
    for weight_row in range (intermediate_size // blen):
        if weight_row % (mlen // blen) == 0:
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, 0 \n"
            generated_code += f"S_ADDI_INT gp{w_hbm_offset_register}, gp0, {weight_row * blen} \n"
            generated_code += f"S_ADDI_INT gp{intermediate_register}, gp{gate_result_register}, 0 \n"
            
            for weight_col in range (hidden_size // mlen):
                generated_code += f"H_PREFETCH_M gp{w_actual_register}, gp{w_hbm_offset_register}, a{gate_weight_hbm_offset_reg}, 1, 0 \n"
                generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {mlen * mlen} \n"
                generated_code += f"S_ADDI_INT gp{w_hbm_offset_register}, gp{w_hbm_offset_register}, {mlen * intermediate_size} \n"
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, 0 \n"
        else:
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, {(weight_row % (mlen // blen)) * blen} \n"
            generated_code += f"S_ADDI_INT gp{intermediate_register}, gp{gate_result_register}, {(weight_row % (mlen // blen)) * blen} \n"
        for act_col in range ((batch * seq_len) // blen):
            generated_code += f"S_ADDI_INT gp{a_actual_register}, gp0, {activation_base_address + act_col * mlen * blen} \n"
            generated_code += f"S_ADDI_INT gp{w_temp_register}, gp{w_actual_register}, 0 \n"
            for inner_loop_index in range (hidden_size // mlen):
                generated_code += f"M_MM 0, gp{w_temp_register}, gp{a_actual_register} \n"
                generated_code += f"S_ADDI_INT gp{w_temp_register}, gp{w_temp_register}, {mlen * mlen} \n"
                generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {mlen * batch * seq_len} \n"
            generated_code += f"M_MM_WO gp{intermediate_register}, gp0, 0 \n"
            generated_code += f"S_ADDI_INT gp{intermediate_register}, gp{intermediate_register}, {blen * mlen} \n"    # generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {activation_base_address} \n"
        if (weight_row + 1) % (mlen // blen) == 0 and weight_row != intermediate_size // blen - 1:
            generated_code += f"S_ADDI_INT gp{gate_result_register}, gp{gate_result_register}, {mlen * batch * seq_len} \n"


    # Intermediate Dim SILU Activation Generation, now x in shape of (b, s, intermediate_size)
    generated_code += "; SILU Generation \n"
    generated_code += f"S_LD_FP f1, gp0, {const_one_fp_address} \n"
    # Reset the addr for up and gate result
    generated_code += f"S_ADDI_INT gp{up_result_register}, gp0, {batch * seq_len * hidden_size} \n"
    generated_code += f"S_ADDI_INT gp{gate_result_register}, gp{up_result_register}, {intermediate_size * batch * seq_len} \n"
    generated_code += f"S_ADDI_INT gp{intermediate_register}, gp0, {activation_base_address} \n" 
    
    # Treat the original activation region as the place for scratchpad.
    for b in range(batch * seq_len):
        for i in range(intermediate_size // vlen):
            # 0 : -x
            generated_code += f"V_SUB_VF gp{intermediate_register}, gp{up_result_register}, f0, 0, 1 \n"
            # 1 : exp(-x)
            generated_code += f"V_EXP_V  gp{intermediate_register}, gp{intermediate_register}, 0 \n"
            # 2 : 1 + exp(-x)
            generated_code += f"V_ADD_VF gp{intermediate_register}, gp{intermediate_register}, f1, 0 \n"
            # 3 : 1 / (1 + exp(-x))
            generated_code += f"V_RECI_V  gp{intermediate_register}, gp{intermediate_register}, 0 \n"
            # 4 : (1 / (1 + exp(-x))) * gate_result
            generated_code += f"V_MUL_VV gp{intermediate_register}, gp{intermediate_register}, gp{up_result_register}, 0 \n"
            # 5: multiply by gate result and store to the up result region
            generated_code += f"V_MUL_VV gp{up_result_register}, gp{intermediate_register}, gp{gate_result_register}, 0 \n"
            generated_code += f"S_ADDI_INT gp{gate_result_register}, gp{gate_result_register}, {vlen} \n"
            generated_code += f"S_ADDI_INT gp{up_result_register}, gp{up_result_register}, {vlen} \n"

    generated_code += "; FFN Downsize Linear Generation \n"
    # Reset the addr for up and gate result
    generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, {hidden_size * intermediate_size} \n"
    generated_code += f"C_SET_SCALE_REG gp{w_actual_register} \n"
    generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, {hidden_size} \n"
    generated_code += f"C_SET_STRIDE_REG gp{w_actual_register} \n"
    generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, 0 \n"
    # Storing the results to the activation base region
    act_result_register = gate_result_register
    generated_code += f"S_ADDI_INT gp{act_result_register}, gp0, {activation_base_address} \n"
    generated_code += f"S_ADDI_INT gp{up_result_register}, gp0, {batch * seq_len * hidden_size} \n"
    for weight_row in range (hidden_size // blen):
        if weight_row % (mlen // blen) == 0:
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, 0 \n"
            generated_code += f"S_ADDI_INT gp{w_hbm_offset_register}, gp0, {weight_row * blen} \n"
            generated_code += f"S_ADDI_INT gp{intermediate_register}, gp{act_result_register}, 0 \n"
            for weight_col in range (intermediate_size // mlen):
                generated_code += f"H_PREFETCH_M gp{w_actual_register}, gp{w_hbm_offset_register}, a{down_weight_hbm_offset_reg}, 1, 0 \n"
                generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {mlen * mlen} \n"
                generated_code += f"S_ADDI_INT gp{w_hbm_offset_register}, gp{w_hbm_offset_register}, {mlen * hidden_size} \n"
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, 0 \n"
        else:
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, {(weight_row % (mlen // blen)) * blen} \n"
            generated_code += f"S_ADDI_INT gp{intermediate_register}, gp{act_result_register}, {(weight_row % (mlen // blen)) * blen} \n"
        for act_col in range (batch * seq_len // blen):
            generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{up_result_register}, {act_col * mlen * blen} \n"
            generated_code += f"S_ADDI_INT gp{w_temp_register}, gp{w_actual_register}, 0 \n"
            for inner_loop_index in range (intermediate_size // mlen):
                generated_code += f"M_MM 0, gp{w_actual_register}, gp{a_actual_register} \n"
                generated_code += f"S_ADDI_INT gp{w_temp_register}, gp{w_actual_register}, {mlen * mlen} \n"
                generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {mlen * batch * seq_len} \n"
            generated_code += f"M_MM_WO gp{intermediate_register}, gp0, 0 \n"
            generated_code += f"S_ADDI_INT gp{intermediate_register}, gp{intermediate_register}, {blen * mlen} \n"    # generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {activation_base_address} \n"
        if (weight_row + 1) % (mlen // blen) == 0 and weight_row != intermediate_size // blen - 1:
            generated_code += f"S_ADDI_INT gp{act_result_register}, gp{act_result_register}, {mlen * batch * seq_len} \n"
    return generated_code
