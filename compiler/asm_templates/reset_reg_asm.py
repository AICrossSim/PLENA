from typing import Dict, List

def reset_reg_asm(
    alive_registers: List[int],
) -> str:
    """
    Generates assembly code for resetting registers.
    """
    generated_code = f"; Reset Registers [{alive_registers}] \n"
    for register in alive_registers:
        generated_code += f"S_ADDI_INT gp{register}, gp0, 0 \n"
    return generated_code


def reset_fpreg_asm(
    alive_registers: List[int],
) -> str:
    """
    Generates assembly code for resetting floating point registers.
    """
    generated_code = f"; Reset Floating Point Registers [{alive_registers}] \n"
    for register in alive_registers:
        generated_code += f"S_ADD_FP f{register}, f0, f0 \n"
    return generated_code