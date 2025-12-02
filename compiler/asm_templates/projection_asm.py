import os
from typing import Dict, List, Any, Optional
from pathlib import Path
import math

IMM2_BOUND = 2**18

def projection_asm(
    mlen: int,
    blen: int,
    batch: int,
    hidden_size: int,
    alive_registers: List[int],
    w_base_hbm_offset_reg: int,
    activation_base_address: int,
    result_base_address: int,
    rope_enabled: bool = False,
    rope_hbm_offset_reg: int = 0,
    rope_on_chip_address: int = 0
) -> str:
    """
    Generates optimized assembly code for a general matrix multiplication operation.
    (Batch, Hidden Size) @ (Hidden Size, Hidden Size) -> (Batch, Hidden Size)
    assume Batch = BLEN for this version.

    Optimizations applied:
    1. Eliminated redundant register resets by using incremental addressing
    2. Removed unnecessary activation pointer resets within MLEN blocks
    3. Better register utilization to minimize unnecessary loads from gp0
    4. Streamlined inner loop to reduce instruction count

    Args:
        mlen (int): The number of rows in the first matrix.
        blen (int): The number of columns in the second matrix.
        alive_registers (List[int]): List of registers that are alive.
        weight_base_address (int): index for the address mapper pointing to the base addr of the weight matrix.
        rope_base_address (int): index for the address mapper pointing to the base addr of the rope matrix.
        activation_base_address (int): addr pointing to the addr of activations in the vector sram.
    Returns:
        str: Generated assembly code for projection, including dot product and RoPE(cond)
    """
    generated_code = "; Projection Generation \n"

    result_register         = alive_registers[0]
    w_actual_register       = alive_registers[1]
    w_hbm_offset_register   = alive_registers[2]
    a_actual_register       = alive_registers[3]

    # Set scale offset
    assert hidden_size * hidden_size < IMM2_BOUND, f"hidden_size * hidden_size must be less than {IMM2_BOUND}"
    generated_code += f"S_ADDI_INT gp{a_actual_register}, gp0, {hidden_size * hidden_size} \n"
    generated_code += f"C_SET_SCALE_REG gp{a_actual_register} \n"
    generated_code += f"S_ADDI_INT gp{a_actual_register}, gp0, {hidden_size} \n"
    generated_code += f"C_SET_STRIDE_REG gp{a_actual_register} \n"

    row_loop_over_hid = hidden_size // blen
    col_loop_over_hid = hidden_size // mlen
    tiles_per_mlen = mlen // blen  # Number of BLEN tiles that fit in MLEN

    # Precompute constants for better code generation
    weight_tile_size = mlen * mlen
    activation_tile_stride = mlen * blen
    total_activation_size = col_loop_over_hid * activation_tile_stride

    # Initialize activation register once at the start
    generated_code += f"S_ADDI_INT gp{a_actual_register}, gp0, {activation_base_address} \n"

    for i in range(row_loop_over_hid):
        tile_in_mlen = i % tiles_per_mlen
        mlen_tile_idx = i // tiles_per_mlen

        if tile_in_mlen == 0:
            # Load a complete col of hidden size into on-chip memory (hidden_size, mlen)
            # This happens when we start a new MLEN-sized column block
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, 0 \n"
            generated_code += f"S_ADDI_INT gp{w_hbm_offset_register}, gp0, {mlen_tile_idx * mlen} \n"

            # Prefetch all weight tiles for this MLEN column
            for k in range(col_loop_over_hid):
                generated_code += f"H_PREFETCH_M gp{w_actual_register}, gp{w_hbm_offset_register}, a{w_base_hbm_offset_reg}, 1, 0 \n"
                generated_code += f"S_ADDI_INT gp{w_hbm_offset_register}, gp{w_hbm_offset_register}, {mlen * hidden_size} \n"
                generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {weight_tile_size} \n"

            # Reset weight register for compute phase
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, 0 \n"
        else:
            # Within the same MLEN block, just offset the weight address
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, {tile_in_mlen * blen} \n"

        # Perform matrix multiplications for all hidden dimension tiles
        for j in range(col_loop_over_hid):
            generated_code += f"M_MM 0, gp{w_actual_register}, gp{a_actual_register} \n"
            # Update weight and activation pointers
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {weight_tile_size} \n"
            if j < col_loop_over_hid - 1:
                generated_code += f"S_ADDI_INT gp{a_actual_register}, gp{a_actual_register}, {activation_tile_stride} \n"

        # Write out result with proper offset
        result_offset = mlen_tile_idx * mlen * blen + tile_in_mlen * blen
        generated_code += f"S_ADDI_INT gp{result_register}, gp0, {result_base_address + result_offset} \n"
        generated_code += f"M_MM_WO {result_register}, gp0, 0 \n"

        # Reset activation pointer for next row iteration (except last iteration)
        if i < row_loop_over_hid - 1:
            generated_code += f"S_ADDI_INT gp{a_actual_register}, gp0, {activation_base_address} \n"

    return generated_code
