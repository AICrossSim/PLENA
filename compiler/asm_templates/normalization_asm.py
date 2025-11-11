import os
from typing import Dict, List, Any, Optional
from pathlib import Path



def select_vvm_debug(
    alive_registers: List[int],
    activation_base_address: int,
    activation2_base_address: int,
    activation3_base_address: int,
    scratchpad_base_address: int,
    vlen: int,
    batch_size: int,
    hidden_dim: int
) -> str:
    """
    Generate assembly code for L2 normalization.
    """
    act_addr = alive_registers[0]
    act2_addr = alive_registers[1]
    act3_addr = alive_registers[2]
    scratchpad_addr = alive_registers[3]

    generated_code = "; RMS Norm generation \n"
    generated_code += f"S_ADDI_INT gp{act_addr}, gp0, {activation_base_address} \n"
    generated_code += f"S_ADDI_INT gp{act2_addr}, gp0, {activation2_base_address} \n"
    generated_code += f"S_ADDI_INT gp{act3_addr}, gp0, {activation3_base_address} \n"
    generated_code += f"S_ADDI_INT gp{scratchpad_addr}, gp0, {scratchpad_base_address} \n"


    # out = select vvm
    generated_code += f"V_SELECT_VVM gp{scratchpad_addr}, gp{act_addr}, gp{act2_addr}, gp{act3_addr} \n"


    return generated_code


def argmux_debug(
    alive_registers: List[int],
    activation_base_address: int,
    scratchpad_base_address: int,
    vlen: int,
    batch_size: int,
    hidden_dim: int,
    a2_base_hbm_offset_addr: int
) -> str:
    """
    Generate assembly code for L2 normalization.
    """
    act_addr = alive_registers[0]
    act2_addr = alive_registers[1]
    scratchpad_addr = alive_registers[2]


    generated_code = "; RMS Norm debug (element-wise add) \n"
    generated_code += f"S_ADDI_INT gp{act_addr}, gp0, {activation_base_address} \n"
    generated_code += f"S_ADDI_INT gp{act2_addr}, gp0, {a2_base_hbm_offset_addr} \n"
    generated_code += f"S_ADDI_INT gp{scratchpad_addr}, gp0, {scratchpad_base_address} \n"
    generated_code += f"V_ADD_VV gp{scratchpad_addr}, gp{act_addr}, gp{act2_addr} \n"
    return generated_code


    '''
    generated_code = "; RMS Norm generation \n"
    generated_code += f"S_ADDI_INT gp{act_addr}, gp0, {activation_base_address} \n"
    generated_code += f"S_ADDI_INT gp{scratchpad_addr}, gp0, {scratchpad_base_address} \n"

    #generated_code += f"H_PREFETCH_M gp{w_actual_register}, gp{w_hbm_offset_register}, a{w_base_hbm_offset_reg}, 1, 0 \n"
    generated_code += "S_ADD_FP f2, f0, f0 \n"
    generated_code += f"V_RED_MAX f2, gp{act_addr}\n"

    # S' = S - m_curr
    generated_code += f"V_SUB_VF gp{scratchpad_addr}, gp{act_addr}, f2 \n"

    # P = exp(S')
    generated_code += f"V_EXP_V gp{scratchpad_addr}, gp{scratchpad_addr}, 0 \n"

    # dum = sum(P)
    generated_code += f"V_RED_SUM f2, gp{scratchpad_addr}\n"

    # # Compute reciprocal
    generated_code += "S_RECI_FP f2, f2 \n"

    # S' = S+reciprocal
    generated_code += f"V_ADD_VF gp{scratchpad_addr}, gp{act_addr}, f2 \n"

    return generated_code
    '''

def argmux_debug_backup(
    alive_registers: List[int],
    activation_base_address: int,
    scratchpad_base_address: int,
    vlen: int,
    batch_size: int,
    hidden_dim: int
) -> str:
    """
    Generate assembly code for L2 normalization.
    """
    act_addr = alive_registers[0]
    scratchpad_addr = alive_registers[1]

    generated_code = "; RMS Norm generation \n"
    generated_code += f"S_ADDI_INT gp{act_addr}, gp0, {activation_base_address} \n"
    generated_code += f"S_ADDI_INT gp{scratchpad_addr}, gp0, {scratchpad_base_address} \n"

    #generated_code += f"H_PREFETCH_M gp{w_actual_register}, gp{w_hbm_offset_register}, a{w_base_hbm_offset_reg}, 1, 0 \n"
    generated_code += "S_ADD_FP f2, f0, f0 \n"
    generated_code += f"V_RED_MAX f2, gp{act_addr}\n"

    # S' = S - m_curr
    generated_code += f"V_SUB_VF gp{scratchpad_addr}, gp{act_addr}, f2 \n"

    # P = exp(S')
    generated_code += f"V_EXP_V gp{scratchpad_addr}, gp{scratchpad_addr}, 0 \n"

    # dum = sum(P)
    generated_code += f"V_RED_SUM f2, gp{scratchpad_addr}\n"

    # # Compute reciprocal
    generated_code += "S_RECI_FP f2, f2 \n"

    # S' = S+reciprocal
    generated_code += f"V_ADD_VF gp{scratchpad_addr}, gp{act_addr}, f2 \n"

    return generated_code



def rms_norm_asm_debug(
    _eps_offset: int,
    reci_hid_offset: int,
    alive_registers: List[int],
    activation_base_address: int,
    scratchpad_base_address: int,
    vlen: int,
    batch_size: int,
    hidden_dim: int,
    a2_base_hbm_offset_reg: int
) -> str:
    """
    Generate assembly code for L2 normalization.
    """
    act_addr = alive_registers[0]
    # 当提供第二个输入基址且寄存器数量足够时，执行元素级加法：out = in1 + in2
    #if activation2_base_address is not None and len(alive_registers) >= 3:
    #    act2_addr = alive_registers[1]
    #    scratchpad_addr = alive_registers[2]#

    #    generated_code = "; RMS Norm debug (element-wise add) \n"
    #    generated_code += f"S_ADDI_INT gp{act_addr}, gp0, {activation_base_address} \n"
    #    generated_code += f"S_ADDI_INT gp{act2_addr}, gp0, {activation2_base_address} \n"
    #    generated_code += f"S_ADDI_INT gp{scratchpad_addr}, gp0, {scratchpad_base_address} \n"
    #    generated_code += f"V_ADD_VV gp{scratchpad_addr}, gp{act_addr}, gp{act2_addr} \n"
    #    return generated_code

    scratchpad_addr = alive_registers[1]

    generated_code = "; RMS Norm generation \n"
    generated_code += f"S_ADDI_INT gp{act_addr}, gp0, {activation_base_address} \n"
    generated_code += f"S_ADDI_INT gp{scratchpad_addr}, gp0, {scratchpad_base_address} \n"

    generated_code += "S_ADD_FP f2, f0, f0 \n"
    generated_code += f"V_RED_SUM f2, gp{act_addr} \n"
    generated_code += f"V_ADD_VF gp{scratchpad_addr}, gp{act_addr}, f2 \n"
    '''
    # Load eps into f1
    #generated_code += f"S_LD_FP f1, gp0, {_eps_offset} \n"
    # Reset f2 as accumulator for reduction.
    generated_code += "S_ADD_FP f2, f0, f0 \n"
    # Load the 1/ hidden_dim into f3
    #generated_code += f"S_LD_FP f3, gp0, {reci_hid_offset} \n"
    for batch in range(batch_size):
        for i in range(hidden_dim // vlen):
            # Compute square of the activation vector and summation
            generated_code += f"V_ADD_VF gp{scratchpad_addr}, gp{act_addr}, f0 \n"
            generated_code += f"V_RED_SUM f2, gp{scratchpad_addr} \n"

            # Move to next vector
            generated_code += f"S_ADDI_INT gp{act_addr}, gp{act_addr}, {vlen} \n"
        
        # Taking the avg
        #generated_code += f"S_MUL_FP f2, f2, f3 \n"

        # # Plus epsilon
        #generated_code += f"S_ADD_FP f2, f2, f1 \n"

        # # Compute square root
        #generated_code += "S_SQRT_FP f2, f2 \n"

        # # Compute reciprocal
        generated_code += "S_RECI_FP f2, f2 \n"
        generated_code += f"S_ADD_FP fp{scratchpad_addr}, gp{scratchpad_addr}, f0 \n"

        for i in range(hidden_dim // vlen):
            # Normalize the activation vector
            generated_code += f"V_MUL_VF gp{act_addr}, gp{act_addr}, f2 \n"

        #    # Move to next vector
        #    generated_code += f"S_ADDI_INT gp{act_addr}, gp{act_addr}, {vlen * batch_size} \n"
        
        generated_code += "S_ADD_FP f2, f0, f0 \n"
        generated_code += f"S_ADDI_INT gp{act_addr}, gp0, {activation_base_address + vlen * batch} \n"
    '''
    return generated_code



def rms_norm_asm(
    _eps_offset: int,
    reci_hid_offset: int,
    alive_registers: List[int],
    activation_base_address: int,
    scratchpad_base_address: int,
    vlen: int,
    batch_size: int,
    hidden_dim: int
) -> str:
    """
    Generate assembly code for L2 normalization.
    """
    act_addr = alive_registers[0]
    scratchpad_addr = alive_registers[1]

    generated_code = "; RMS Norm generation \n"
    generated_code += f"S_ADDI_INT gp{act_addr}, gp0, {activation_base_address} \n"
    generated_code += f"S_ADDI_INT gp{scratchpad_addr}, gp0, {scratchpad_base_address} \n"
    
    # Load eps into f1
    generated_code += f"S_LD_FP f1, gp0, {_eps_offset} \n"
    # Reset f2 as accumulator for reduction.
    generated_code += "S_ADD_FP f2, f0, f0 \n"
    # Load the 1/ hidden_dim into f3
    generated_code += f"S_LD_FP f3, gp0, {reci_hid_offset} \n"
    for batch in range(batch_size):
        for i in range(hidden_dim // vlen):
            # Compute square of the activation vector and summation
            generated_code += f"V_MUL_VV gp{scratchpad_addr}, gp{act_addr}, gp{act_addr} \n"
            generated_code += f"V_RED_SUM f2, gp{scratchpad_addr} \n"

            # Move to next vector
            generated_code += f"S_ADDI_INT gp{act_addr}, gp{act_addr}, {vlen * batch_size} \n"
        
        # Taking the avg
        generated_code += f"S_MUL_FP f2, f2, f3 \n"

        # # Plus epsilon
        generated_code += f"S_ADD_FP f2, f2, f1 \n"

        # # Compute square root
        generated_code += "S_SQRT_FP f2, f2 \n"

        # # Compute reciprocal
        generated_code += "S_RECI_FP f2, f2 \n"

        for i in range(hidden_dim // vlen):
            # Normalize the activation vector
            generated_code += f"V_MUL_VF gp{act_addr}, gp{act_addr}, f2 \n"

            # Move to next vector
            generated_code += f"S_ADDI_INT gp{act_addr}, gp{act_addr}, {vlen * batch_size} \n"
        
        generated_code += "S_ADD_FP f2, f0, f0 \n"
        generated_code += f"S_ADDI_INT gp{act_addr}, gp0, {activation_base_address + vlen * batch} \n"

    return generated_code