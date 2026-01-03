import os
from typing import Dict, List, Any, Optional
from pathlib import Path


def argmax_debug(
    alive_registers: List[int],
    input_base_address: int,
    output_base_address: int,
    vlen: int,
    batch_size: int,
    gen_length: int,
    vocal_size: int,
) -> str:
    """
    Generate assembly code for Argnmax.
    """
    input_addr          = alive_registers[0]
    output_addr         = alive_registers[1]
    len_addr            = alive_registers[2]
    max_idx_addr        = alive_registers[3]
    max_idx_offset_addr = alive_registers[4]
    
    generated_code = "; Argnmax for dLLM generation \n"
    generated_code += f"S_ADDI_INT gp{input_addr}, gp0, {input_base_address} \n"
    generated_code += f"S_ADDI_INT gp{output_addr}, gp0, {output_base_address} \n"
    generated_code += f"S_ADDI_INT gp{len_addr}, gp0, {gen_length} \n"

    # Loop over batch_size rows
    for batch_idx in range(batch_size):
        for i in range(gen_length):
            input_i_address = input_base_address + (batch_idx*gen_length + i) *vlen*(vocal_size // vlen)

            generated_code += f"S_ADD_FP f1, f0, f0 \n"
            generated_code += f"S_ADDI_INT gp{input_addr}, gp0, {input_i_address} \n"
            generated_code += f"S_ADD_INT gp{max_idx_offset_addr},  gp0, gp0 \n"  # Initialize offset to 0
            for j in range(vocal_size // vlen):
                generated_code += f"V_RED_MAX_IDX gp{max_idx_addr}, gp{input_addr}, gp{max_idx_offset_addr}, f1\n"
                generated_code += f"S_ADDI_INT gp{input_addr}, gp{input_addr}, {vlen} \n"
                generated_code += f"S_ADDI_INT gp{max_idx_offset_addr}, gp{max_idx_offset_addr}, {vlen} \n"

            # INT_MEM[int_reg<gp0>+ (batch_idx*vlen + i)] = gp{max_idx_addr}
            generated_code += f"S_ST_INT gp{max_idx_addr}, gp0, {batch_idx*gen_length + i} \n"
        

    return generated_code


def stable_max_softmax_method(
    alive_registers: List[int],
    input_base_address: int,
    output_base_address: int,
    vlen: int,
    batch_size: int,
    gen_length: int,
    vocal_size: int,
) -> str:
    """
    Generate assembly code for Argnmax.
    """
    input_addr  = alive_registers[0]
    output_addr = alive_registers[1]
    len_reg     = alive_registers[2]

    
    generated_code = "; Argnmax for dLLM generation \n"
    generated_code += f"S_ADDI_INT gp{input_addr}, gp0, {input_base_address} \n"
    generated_code += f"S_ADDI_INT gp{output_addr}, gp0, {output_base_address} \n"
    generated_code += f"S_ADDI_INT gp{len_reg}, gp0, {gen_length} \n"

    
    # Loop over batch_size rows
    for batch_idx in range(batch_size):
        for i in range(gen_length):
            input_i_address = input_base_address + (batch_idx*gen_length + i) *vlen*(vocal_size // vlen)

            generated_code += f"S_ADD_FP f1, f0, f0 \n"
            generated_code += f"S_ADD_FP f2, f0, f0 \n"
            
            generated_code += f"S_ADDI_INT gp{input_addr}, gp0, {input_i_address} \n"
            for j in range(vocal_size // vlen):
                generated_code += f"V_RED_MAX f1, gp{input_addr}, 0\n"
                # Update gp{input_addr}
                generated_code += f"S_ADDI_INT gp{input_addr}, gp{input_addr}, {vlen} \n"

            generated_code += f"S_ADDI_INT gp{input_addr}, gp0, {input_i_address} \n"
            for j in range(vocal_size // vlen):
                generated_code += f"V_SUB_VF gp{output_addr}, gp{input_addr}, f1, 0\n"
                generated_code += f"V_EXP_V gp{output_addr}, gp{output_addr}, 0 \n"
                generated_code += f"V_RED_SUM f2, gp{output_addr}\n"
            
            generated_code += f"S_RECI_FP f2, f2 \n"
            # Store reciprocal value from f2 to FP_MEM: FP_MEM[fp_reg<gp0>+i] = fp_reg<f2>
            generated_code += f"S_ST_FP f2, gp0, {i} \n"
        
        # SRAM[gp<x0_p_addr>] = FP_MEM[gp0+0 : gp0+0+gen_length]
        generated_code += f"S_MAP_V_FP gp{output_addr}, gp0, 0, gp{len_reg} \n"
        generated_code += f"S_ADDI_INT gp{output_addr}, gp{output_addr}, {vlen} \n"



    return generated_code
