from typing import Dict, List

def reset_reg_asm(
    alive_registers: List[int],
) -> str:
    """
    Generates assembly code for resetting registers.
    """
    generated_code = ""
    for register in alive_registers:
        generated_code += f"S_ADDI_INT gp{register}, gp0, 0 \n"
    return generated_code