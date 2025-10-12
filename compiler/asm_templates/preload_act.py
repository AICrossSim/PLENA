import os
from typing import Dict, List, Any, Optional
from pathlib import Path

def preload_act_asm(
    vlen: int,
    preload_len: int,
    batch: int,
    hidden_size: int,
    alive_registers: List[int],
    activation_base_address: int,
) -> str:
    """
    Generates assembly code for preloading activation.
    """
    generated_code = "; Preload Activation Generation \n"
    # get two registers from alive_registers, 1 as a address
    a_base_register = alive_registers[0]
    a_actual_register = alive_registers[1]
    # reset the registers
    set_a_base_address = f"S_ADDI_INT gp{a_base_register}, gp0, {activation_base_address} \n"

    generated_code += set_a_base_address
    for i in range(batch * (hidden_size // (vlen * preload_len))):
        generated_code += f"H_PREFETCH_V gp{a_actual_register}, gp{a_actual_register}, a{activation_base_address}, 1, 0 \n"
        generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {vlen * preload_len} \n"
    return generated_code