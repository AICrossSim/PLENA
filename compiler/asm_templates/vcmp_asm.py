import os
from typing import Dict, List, Any, Optional
from pathlib import Path



def vcmp_asm_debug(
    alive_registers: List[int],
    activation_base_address: int,
    scratchpad_base_address: int,
    vlen: int,
    batch_size: int,
) -> str:
    """
    Generate assembly code for element-wise select operation (V_SELECT_VVM).
    Loops over batch_size rows to perform: output[i] = mask[i] ? input1[i] : input2[i]
    """
    act_addr = alive_registers[0]
    scratchpad_addr = alive_registers[1]
    #scalar_addr = alive_registers[2]

    generated_code = "; V_SELECT_VVM generation \n"
    generated_code += f"S_ADDI_INT gp{act_addr}, gp0, {activation_base_address} \n"
    generated_code += f"S_ADDI_INT gp{scratchpad_addr}, gp0, {scratchpad_base_address} \n"

    # Reset registers for execution
    # Load scalar value into fp register
    generated_code += f"S_LD_FP f1, gp0, 5 \n"
    # Convert int to float (approximate, using the scalar as-is)
    # For simplicity, we'll use a preloaded value or assume scalar is set
    #generated_code += f"V_CMP_EQ_VF gp{scratchpad_addr}, gp{act_addr}, f1\n"


    # Loop over batch_size rows
    for _ in range(batch_size):
        # out = select vvm: out[i] = mask[i] != 0 ? input1[i] : input2[i]
        generated_code += f"V_CMP_EQ_VF gp{scratchpad_addr}, gp{act_addr}, f1 \n"
        
        # Increment all address pointers by vlen (move to next row)
        generated_code += f"S_ADDI_INT gp{act_addr}, gp{act_addr}, {vlen} \n"
        generated_code += f"S_ADDI_INT gp{scratchpad_addr}, gp{scratchpad_addr}, {vlen} \n"

    return generated_code


def vcmp_eq_asm(
    gp_dst: int,
    gp_vec: int,
    fp_scalar: int,
) -> str:
    """
    Generate assembly code for vector compare equal with scalar.
    V_CMP_EQ_VF: mask[i] = (vec[i] == scalar) ? 1.0 : 0.0
    
    This is the ONLY compare instruction needed for dLLM's Top-K + Scatter operation.
    
    Args:
        gp_dst: Destination vector register (will store mask result)
        gp_vec: Source vector register
        fp_scalar: Scalar floating-point register
        
    Returns:
        Assembly code string
    """
    return f"V_CMP_EQ_VF gp{gp_dst}, gp{gp_vec}, f{fp_scalar}\n"


def scatter_with_vcmp(
    gp_dst: int,
    gp_value: int,
    gp_positions: int,
    fp_idx: int,
    gp_mask_temp: int,
) -> str:
    """
    Generate assembly code for scatter operation using V_CMP_EQ + V_SELECT.
    Scatter effect: dst[idx] = value
    
    This is the core pattern for dLLM's Top-K implementation.
    
    Args:
        gp_dst: Destination vector register (will be modified at position idx)
        gp_value: Value vector (all elements should be the same value to scatter)
        gp_positions: Position vector [0, 1, 2, ..., L-1]
        fp_idx: Scalar index where to scatter
        gp_mask_temp: Temporary register for mask
        
    Returns:
        Assembly code string
    """
    asm = "; Scatter operation using V_CMP_EQ + V_SELECT\n"
    # Generate one-hot mask
    asm += f"V_CMP_EQ_VF gp{gp_mask_temp}, gp{gp_positions}, f{fp_idx}\n"
    # Conditional update: dst = mask ? value : dst
    asm += f"V_SELECT_VVM gp{gp_dst}, gp{gp_value}, gp{gp_dst}, gp{gp_mask_temp}\n"
    return asm

