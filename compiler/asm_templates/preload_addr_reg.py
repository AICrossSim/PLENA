import os
from typing import Dict, List, Any, Optional
from pathlib import Path


def preload_addr_reg_asm(
    alive_registers: List[int],
    addr_reg_val: List[int]
) -> str:
    """
    Generates assembly code for preloading address registers.
    """
    generated_code = "; Preload Addr Reg Generation \n"
    for i in range(len(addr_reg_val)):
        if addr_reg_val[i] <= 262143:
            # use S_ADDI_INT
            generated_code += f"S_ADDI_INT gp{alive_registers[i]}, gp0, {addr_reg_val[i]} \n"
        else:
            # use S_LUI_INT, Load the upper 20 bits of the address first, then add the lower 12 bits
            generated_code += f"S_LUI_INT gp{alive_registers[i]}, {addr_reg_val[i] >> 12} \n"
            generated_code += f"S_ADDI_INT gp{alive_registers[i]}, gp{alive_registers[i]}, {addr_reg_val[i] & 0xFFF} \n"
        
        generated_code += f"C_SET_ADDR_REG gp{alive_registers[i]}, gp{alive_registers[i]}, gp{alive_registers[i]} \n"

    return generated_code