import os
from typing import Dict, List, Any, Optional
from pathlib import Path

def get_transfer_index_debug(
    alive_registers: List[int],
    logits_base_address: int, # input (B,L,V)
    mask_base_address: int,   # input (B,L)
    output_base_address: int, # input (B,L)
    temp_base_address: int,   # temp ()
    x0_p_base_address: int,   # x0_p (B,L)
    k_values: List[int],
    vlen: int,
    batch_size: int,
) -> str:
    """
    Generate assembly code for Argnmux.
    """
    logits_addr = alive_registers[0]
    mask_addr = alive_registers[1]
    output_addr = alive_registers[2]
    temp_addr = alive_registers[3]
    x0_p_addr = alive_registers[4]
    k_reg = alive_registers[5]
    
    generated_code = "; Argnmux for dLLM generation \n"
    generated_code += f"S_ADDI_INT gp{logits_addr}, gp0, {logits_base_address} \n"
    generated_code += f"S_ADDI_INT gp{mask_addr}, gp0, {mask_base_address} \n"
    generated_code += f"S_ADDI_INT gp{output_addr}, gp0, {output_base_address} \n"
    generated_code += f"S_ADDI_INT gp{temp_addr}, gp0, {temp_base_address} \n"
    generated_code += f"S_ADDI_INT gp{x0_p_addr}, gp0, {x0_p_base_address} \n"
    
    # Loop over batch_size rows
    for batch_idx in range(batch_size):  
        for i in range(vlen):
            # calculate the scalar from vector, and put the scalar into the FP_MEM one by one, until the number of vlen
            #generated_code += f"S_ADD_FP f1, f0, f0 \n"
            generated_code += f"V_RED_MAX f1, gp{logits_addr}, 0\n"
            # S' = S - m_curr
            generated_code += f"V_SUB_VF gp{temp_addr}, gp{logits_addr}, f1, 0\n"
            # P = exp(S')
            generated_code += f"V_EXP_V gp{temp_addr}, gp{temp_addr}, 0 \n"
            # dum = sum(P)
            generated_code += f"V_RED_SUM f1, gp{temp_addr}\n"
            # Compute reciprocal
            generated_code += f"S_RECI_FP f1, f1 \n"
            # Store reciprocal into f1, FP_MEM[fp_reg<gp0>+i] = fp_reg<f1>
            generated_code += f"S_ST_FP f1, gp0, {i} \n"
            generated_code += f"S_ADDI_INT gp{logits_addr}, gp{logits_addr}, {vlen} \n"
        
        # grab these accumulated vlen scalar(stored reciprocal) into SRAM to form an vector again
        # SRAM[gp<x0_p_addr>] = FP_MEM[gp0+0 : gp0+0+vlen]
        generated_code += f"S_MAP_V_FP gp{x0_p_addr}, gp0, 0 \n"
    
        # Load k value for this batch into scalar register
        k_value = k_values[batch_idx] if batch_idx < len(k_values) else k_values[0]
        generated_code += f"S_ADDI_INT gp{k_reg}, gp0, {k_value} \n"
        
        # Execute V_TOPK_MASK instruction
        # V_TOPK_MASK rd, rs1, rs2, k_scalar
        # rd: output mask (vector), rs1: confidence vector, rs2: input mask (vector), k_scalar: k value (scalar)
        generated_code += f"V_TOPK_MASK gp{output_addr}, gp{x0_p_addr}, gp{mask_addr}, gp{k_reg}\n"
        
        # Increment all address pointers by vlen (move to next row)
        generated_code += f"S_ADDI_INT gp{x0_p_addr}, gp{x0_p_addr}, {vlen} \n"
        generated_code += f"S_ADDI_INT gp{mask_addr}, gp{mask_addr}, {vlen} \n"
        generated_code += f"S_ADDI_INT gp{output_addr}, gp{output_addr}, {vlen} \n"
    

    return generated_code