import os
from typing import Dict, List, Any, Optional
from pathlib import Path

def preload_act_asm(
    vlen: int,
    preload_len: int,
    batch: int,
    hidden_size: int,
    alive_registers: List[int],
    activation_offset_reg: int,
) -> str:
    """
    Generates assembly code for preloading activation.
    """
    generated_code = "; Preload Activation Generation \n"
    # get two registers from alive_registers, 1 as a address
    a_actual_register = alive_registers[0]

    # Set scale offset
    generated_code += f"S_ADDI_INT gp{a_actual_register}, gp0, {hidden_size * batch} \n"
    generated_code += f"C_SET_SCALE_REG gp{a_actual_register} \n"

    # reset the registers
    set_a_base_address = f"S_ADDI_INT gp{a_actual_register}, gp0, 0 \n"
    generated_code += set_a_base_address

    for i in range(batch * (hidden_size // (vlen * preload_len))):
        generated_code += f"H_PREFETCH_V gp{a_actual_register}, gp{a_actual_register}, a{activation_offset_reg}, 0, 0 \n"
        generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {vlen * preload_len} \n"
    return generated_code