import os
from typing import Dict, List, Any, Optional
from pathlib import Path


def topk_mask_debug(
    alive_registers: List[int],
    confidence_base_address: int,
    mask_base_address: int,
    output_base_address: int,
    k_values: List[int],
    vlen: int,
    batch_size: int,
) -> str:
    """
    Generate assembly code for V_TOPK_MASK operation.
    
    Args:
        alive_registers: List of available registers [confidence_addr, mask_addr, output_addr, k_reg]
        confidence_base_address: Base address of confidence vector in VRAM
        mask_base_address: Base address of input mask in VRAM
        output_base_address: Base address where output mask will be stored
        k_values: List of k values for each batch (number of top elements to select)
        vlen: Vector length (elements per vector)
        batch_size: Number of batches to process
    
    Returns:
        Generated assembly code string
    """
    confidence_addr = alive_registers[0]
    mask_addr = alive_registers[1]
    output_addr = alive_registers[2]
    k_reg = alive_registers[3]
    
    generated_code = "; V_TOPK_MASK for dLLM generation \n"
    generated_code += f"S_ADDI_INT gp{confidence_addr}, gp0, {confidence_base_address} \n"
    generated_code += f"S_ADDI_INT gp{mask_addr}, gp0, {mask_base_address} \n"
    generated_code += f"S_ADDI_INT gp{output_addr}, gp0, {output_base_address} \n"

    # Loop over batch_size rows
    for i in range(batch_size):
        # Load k value for this batch into scalar register
        k_value = k_values[i] if i < len(k_values) else k_values[0]
        generated_code += f"S_ADDI_INT gp{k_reg}, gp0, {k_value} \n"
        
        # Execute V_TOPK_MASK instruction
        # V_TOPK_MASK rd, rs1, rs2, k_scalar
        # rd: output mask (vector), rs1: confidence vector, rs2: input mask (vector), k_scalar: k value (scalar)
        generated_code += f"V_TOPK_MASK gp{output_addr}, gp{confidence_addr}, gp{mask_addr}, gp{k_reg}\n"
        
        # Increment all address pointers by vlen (move to next row)
        generated_code += f"S_ADDI_INT gp{confidence_addr}, gp{confidence_addr}, {vlen} \n"
        generated_code += f"S_ADDI_INT gp{mask_addr}, gp{mask_addr}, {vlen} \n"
        generated_code += f"S_ADDI_INT gp{output_addr}, gp{output_addr}, {vlen} \n"

    return generated_code


def topk_mask_simple(
    alive_registers: List[int],
    confidence_reg_address: int,
    mask_reg_address: int,
    output_reg_address: int,
    k_value: int,
) -> str:
    """
    Generate a single V_TOPK_MASK instruction.
    
    Args:
        confidence_reg: Register number containing confidence vector
        mask_reg: Register number containing input mask
        output_reg: Register number for output mask
        k_reg: Register number containing k value (scalar)
    
    Returns:
        Single V_TOPK_MASK assembly instruction
    """
    confidence_reg = alive_registers[0]
    mask_reg = alive_registers[1]
    output_reg = alive_registers[2]
    k_reg = alive_registers[3]


    generated_code = "; V_SELECT_VVM generation \n"
    generated_code += f"S_ADDI_INT gp{confidence_reg}, gp0, {confidence_reg_address} \n"
    generated_code += f"S_ADDI_INT gp{mask_reg}, gp0, {mask_reg_address} \n"
    generated_code += f"S_ADDI_INT gp{output_reg}, gp0, {output_reg_address} \n"
    generated_code += f"S_ADDI_INT gp{k_reg}, gp0, {k_value} \n"

    generated_code += f"V_TOPK_MASK gp{output_reg}, gp{confidence_reg}, gp{mask_reg}, gp{k_reg}\n"

    return generated_code

