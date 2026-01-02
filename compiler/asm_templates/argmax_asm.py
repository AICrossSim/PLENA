import os
from typing import Dict, List, Any, Optional
from pathlib import Path


def argmax_debug(
    alive_registers: List[int],
    input_base_address: int,
    vlen: int,
    batch_size: int,
) -> str:
    """
    Generate assembly code for Argnmax.
    """
    input_addr   = alive_registers[0]
    max_idx_addr = alive_registers[1]
    max_idx_offset_addr = alive_registers[2]
    
    generated_code = "; Argnmax for dLLM generation \n"
    generated_code += f"S_ADDI_INT gp{input_addr}, gp0, {input_base_address} \n"

    
    # Loop over batch_size rows
    for i in range(batch_size):
        generated_code += f"S_ADD_INT gp{max_idx_addr}, gp0, gp0 \n"  # Initialize idx to 0
        generated_code += f"S_ADD_INT gp{max_idx_offset_addr}, gp0, gp0 \n"  # Initialize idx offset to 0
        # calcualte the index of the max value
        generated_code += f"S_ADD_FP f1, f0, f0 \n"
        generated_code += f"V_RED_MAX_IDX gp{max_idx_addr}, gp{input_addr}, gp{max_idx_offset_addr}, f1\n"

        # Store the max_idx from gp{max_idx_addr} into INT_MEM, INT_MEM[int_reg<gp0>+i] = gp{max_idx_addr}
        generated_code += f"S_ST_INT gp{max_idx_addr}, gp0, {i} \n"
 
        # Increment all address pointers by vlen (move to next row)
        generated_code += f"S_ADDI_INT gp{input_addr}, gp{input_addr}, {vlen} \n"



    return generated_code



def stable_max_softmax_method(
    alive_registers: List[int],
    input_base_address: int,
    output_base_address: int,
    vlen: int,
    batch_size: int,
) -> str:
    """
    Generate assembly code for Argnmax.
    """
    input_addr = alive_registers[0]
    output_addr = alive_registers[1]

    
    generated_code = "; Argnmax for dLLM generation \n"
    generated_code += f"S_ADDI_INT gp{input_addr}, gp0, {input_base_address} \n"
    generated_code += f"S_ADDI_INT gp{output_addr}, gp0, {output_base_address} \n"

    
    # Loop over batch_size rows
    for i in range(batch_size):
        # calcualte the out = vector + reciprocal
        generated_code += f"S_ADD_FP f1, f0, f0 \n"
        generated_code += f"V_RED_MAX f1, gp{input_addr}, 0\n"
        # S' = S - m_curr
        generated_code += f"V_SUB_VF gp{output_addr}, gp{input_addr}, f1, 0\n"
        # P = exp(S')
        generated_code += f"V_EXP_V gp{output_addr}, gp{output_addr}, 0 \n"
        # dum = sum(P)
        generated_code += f"V_RED_SUM f1, gp{output_addr}\n"
        # # Compute reciprocal
        generated_code += f"S_RECI_FP f1, f1 \n"
        # Store reciprocal value from f1 to FP_MEM: FP_MEM[fp_reg<gp0>+i] = fp_reg<f1>
        generated_code += f"S_ST_FP f1, gp0, {i} \n"
        
        # Increment all address pointers by vlen (move to next row)
        generated_code += f"S_ADDI_INT gp{input_addr}, gp{input_addr}, {vlen} \n"



    return generated_code
