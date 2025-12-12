import os
from typing import Dict, List, Any, Optional
from pathlib import Path


def argmux_debug(
    alive_registers: List[int],
    activation_base_address: int,
    scratchpad_base_address: int,
    vlen: int,
    batch_size: int,
) -> str:
    """
    Generate assembly code for Argnmux.
    """
    act_addr = alive_registers[0]
    scratchpad_addr = alive_registers[1]

    
    generated_code = "; Argnmux for dLLM generation \n"
    generated_code += f"S_ADDI_INT gp{act_addr}, gp0, {activation_base_address} \n"
    generated_code += f"S_ADDI_INT gp{scratchpad_addr}, gp0, {scratchpad_base_address} \n"


    # Loop over batch_size rows
    for _ in range(batch_size):
        # calcualte the out = vector + reciprocal
        generated_code += f"S_ADD_FP f2, f0, f0 \n"
        generated_code += f"V_RED_MAX_IDX f2, gp{act_addr}, 0\n"
        # S' = S - m_curr
        #generated_code += f"V_SUB_VF gp{scratchpad_addr}, gp{act_addr}, f2, 0\n"
        # P = exp(S')
        #generated_code += f"V_EXP_V gp{scratchpad_addr}, gp{scratchpad_addr}, 0 \n"
        # dum = sum(P)
        #generated_code += f"V_RED_SUM f2, gp{scratchpad_addr}\n"
        # # Compute reciprocal
        #generated_code += f"S_RECI_FP f2, f2 \n"
        # S' = S+reciprocal
        generated_code += f"V_ADD_VF gp{scratchpad_addr}, gp{act_addr}, f2, 0 \n"
        
        # Increment all address pointers by vlen (move to next row)
        generated_code += f"S_ADDI_INT gp{act_addr}, gp{act_addr}, {vlen} \n"
        generated_code += f"S_ADDI_INT gp{scratchpad_addr}, gp{scratchpad_addr}, {vlen} \n"



    return generated_code
