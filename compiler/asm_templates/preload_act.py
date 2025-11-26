import os
from typing import Dict, List, Any, Optional
from pathlib import Path
import math


IMM2_BOUND = 2**18

def preload_act_asm_bug(
    vlen: int,
    preload_len: int,
    batch: int,
    hidden_size: int,
    scale: int,
    act_hbm_offset: int,
    act_vram_offset: int,
    alive_registers: List[int],
    activation_offset_reg: int,
    stride_size = None
) -> str:
    """
    Generates assembly code for preloading activation.
    Memory Layout: Here we assume the activation is stored in (Hidden // MLEN , Batch (Integrate with Seq Len), MLEN)
    """
    generated_code = "; Preload Activation Generation \n"
    # get two registers from alive_registers, 1 as a address
    a_actual_register   = alive_registers[0]
    set_stride_register = alive_registers[1]
    result_register     = alive_registers[2]
    stride_len = vlen if stride_size is None else stride_size

    # Set scale offset
    generated_code += f"S_ADDI_INT gp{a_actual_register}, gp0, {scale} \n"
    generated_code += f"C_SET_SCALE_REG gp{a_actual_register} \n"

    # reset the registers
    generated_code += f"S_ADDI_INT gp{a_actual_register}, gp0, {act_hbm_offset} \n"
    generated_code += f"S_ADDI_INT gp{result_register}, gp0, {act_vram_offset} \n"
    load_amount_per_hidden = math.ceil(hidden_size / vlen)
    
    if batch == 1:
        for i in range(math.ceil(hidden_size / (vlen * preload_len))):
            generated_code += f"H_PREFETCH_V gp{result_register}, gp{a_actual_register}, a{activation_offset_reg}, 0, 0 \n"
            generated_code += f"S_ADDI_INT gp{result_register}, gp{result_register}, {vlen * preload_len} \n"
            generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {vlen * preload_len} \n"
    else:
        generated_code += f"S_ADDI_INT gp{set_stride_register}, gp0, {stride_len} \n"
        generated_code += f"C_SET_STRIDE_REG gp{set_stride_register} \n"
        assert batch * hidden_size <= IMM2_BOUND, "batch * hidden_size must be less than {IMM2_BOUND}"
        for i in range(load_amount_per_hidden):
            for j in range(math.ceil(batch / preload_len)):
                generated_code += f"H_PREFETCH_V gp{result_register}, gp{a_actual_register}, a{activation_offset_reg}, 1, 0 \n"
                generated_code += f"S_ADDI_INT gp{result_register}, gp{result_register}, {vlen * preload_len} \n"
                generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {hidden_size * preload_len} \n"
            generated_code += f"S_ADDI_INT gp{a_actual_register}, gp0, {(i + 1) * vlen} \n"
    return generated_code


def preload_act_asm(
    vlen: int,
    preload_len: int,
    batch: int,
    hidden_size: int,
    scale: int,
    act_hbm_offset: int,
    act_vram_offset: int,
    alive_registers: List[int],
    activation_offset_reg: int,
    stride_size = None
) -> str:
    """
    Generates assembly code for preloading activation.
    """
    generated_code = "; Preload Activation Generation \n"
    # get two registers from alive_registers, 1 as a address
    a_actual_register   = alive_registers[0]
    set_stride_register = alive_registers[1]
    result_register     = alive_registers[2]
    stride_len = vlen if stride_size is None else stride_size

    # Set scale offset
    #generated_code += f"S_ADDI_INT gp{a_actual_register}, gp0, {hidden_size * batch} \n"
    generated_code += f"S_ADDI_INT gp{a_actual_register}, gp0, {scale} \n"
    generated_code += f"C_SET_SCALE_REG gp{a_actual_register} \n"

    # reset the registers
    set_a_base_address = f"S_ADDI_INT gp{a_actual_register}, gp0, {act_hbm_offset} \n"
    set_act_vram_base_address = f"S_ADDI_INT gp{result_register}, gp0, {act_vram_offset} \n"
    generated_code += set_a_base_address
    generated_code += set_act_vram_base_address
    
    if batch == 1:
        generated_code += f"S_ADDI_INT gp{set_stride_register}, gp0, {stride_len} \n"
        generated_code += f"C_SET_STRIDE_REG gp{set_stride_register} \n"
        #for i in range((hidden_size + (vlen * preload_len) - 1) // (vlen * preload_len)):
        for i in range((1 * hidden_size) // (vlen * preload_len)):
            #generated_code += f"H_PREFETCH_V gp{a_actual_register}, gp{a_actual_register}, a{activation_offset_reg}, 0, 0 \n"
            #generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {vlen * preload_len} \n"
            generated_code += f"H_PREFETCH_V gp{result_register}, gp{a_actual_register}, a{activation_offset_reg}, 0, 0 \n"
            generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {vlen * preload_len} \n"
            generated_code += f"S_ADDI_INT gp{result_register}, gp{result_register}, {vlen * preload_len} \n"
    else:
        generated_code += f"S_ADDI_INT gp{set_stride_register}, gp0, {stride_len} \n"
        generated_code += f"C_SET_STRIDE_REG gp{set_stride_register} \n"
        for i in range((batch * hidden_size) // (vlen * preload_len)):
            generated_code += f"H_PREFETCH_V gp{result_register}, gp{a_actual_register}, a{activation_offset_reg}, 1, 0 \n"
            generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {vlen * preload_len} \n"
            generated_code += f"S_ADDI_INT gp{result_register}, gp{result_register}, {vlen * preload_len} \n"

    return generated_code