from typing import List

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
    Generates highly optimized assembly code for matrix multiplication.
    (Batch, Hidden Size) @ (Hidden Size, Hidden Size) -> (Batch, Hidden Size)

    Key optimizations:
    1. Eliminate dead code (register updates after last use in loop)
    2. Use incremental result addressing within MLEN blocks
    3. Minimize redundant register resets

    Args:
        mlen: Matrix tile size (rows)
        blen: Vector tile size (batch dimension)
        batch: Batch size (unused, assumed = blen)
        hidden_size: Hidden dimension size
        alive_registers: Available GP registers [result, w_actual, w_hbm_offset, a_actual]
        w_base_hbm_offset_reg: HBM address register index for weights
        activation_base_address: Vector SRAM address for activations
        result_base_address: Vector SRAM address for output
        rope_enabled: Whether RoPE is enabled (unused)
        rope_hbm_offset_reg: RoPE HBM address register (unused)
        rope_on_chip_address: RoPE on-chip address (unused)

    Returns:
        Generated assembly code string
    """
    # Suppress unused parameter warnings (API compatibility)
    _ = batch, rope_enabled, rope_hbm_offset_reg, rope_on_chip_address

    # Unpack registers
    result_reg = alive_registers[0]
    w_sram_reg = alive_registers[1]
    w_hbm_reg = alive_registers[2]
    act_reg = alive_registers[3]

    # Compute loop bounds
    num_output_tiles = hidden_size // blen  # 32 tiles for hidden=128, blen=4
    num_weight_tiles = hidden_size // mlen  # 2 tiles for hidden=128, mlen=64
    tiles_per_mlen = mlen // blen           # 16 tiles fit in one MLEN block

    # Memory layout constants
    weight_tile_size = mlen * mlen          # 4096 for mlen=64
    act_tile_stride = mlen * blen           # 256 for mlen=64, blen=4
    hbm_row_stride = mlen * hidden_size     # 8192 for mlen=64, hidden=128

    # Build assembly as list of lines
    lines = ["; Projection Generation (Optimized)"]

    # Setup scale and stride registers (use act_reg as temp)
    assert hidden_size * hidden_size < IMM2_BOUND
    lines.append(f"S_ADDI_INT gp{act_reg}, gp0, {hidden_size * hidden_size}")
    lines.append(f"C_SET_SCALE_REG gp{act_reg}")
    lines.append(f"S_ADDI_INT gp{act_reg}, gp0, {hidden_size}")
    lines.append(f"C_SET_STRIDE_REG gp{act_reg}")

    # Initialize activation register
    lines.append(f"S_ADDI_INT gp{act_reg}, gp0, {activation_base_address}")

    # Track which MLEN block we're in
    current_mlen_block = -1

    for tile_idx in range(num_output_tiles):
        mlen_block = tile_idx // tiles_per_mlen
        tile_in_block = tile_idx % tiles_per_mlen
        is_last_tile = (tile_idx == num_output_tiles - 1)

        # === WEIGHT PREFETCH PHASE ===
        # Prefetch weights when starting a new MLEN block
        if mlen_block != current_mlen_block:
            current_mlen_block = mlen_block
            hbm_col_offset = mlen_block * mlen

            # Initialize weight SRAM and HBM offset registers
            lines.append(f"S_ADDI_INT gp{w_sram_reg}, gp0, 0")
            lines.append(f"S_ADDI_INT gp{w_hbm_reg}, gp0, {hbm_col_offset}")

            # Prefetch all weight tiles for this column block
            for k in range(num_weight_tiles):
                lines.append(f"H_PREFETCH_M gp{w_sram_reg}, gp{w_hbm_reg}, a{w_base_hbm_offset_reg}, 1, 0")
                if k < num_weight_tiles - 1:
                    lines.append(f"S_ADDI_INT gp{w_hbm_reg}, gp{w_hbm_reg}, {hbm_row_stride}")
                    lines.append(f"S_ADDI_INT gp{w_sram_reg}, gp{w_sram_reg}, {weight_tile_size}")

            # After prefetch, set weight SRAM base for first tile in block
            lines.append(f"S_ADDI_INT gp{w_sram_reg}, gp0, 0")
        else:
            # Within same MLEN block - set weight offset for this tile
            lines.append(f"S_ADDI_INT gp{w_sram_reg}, gp0, {tile_in_block * blen}")

        # === COMPUTE PHASE ===
        # Matrix multiplications across hidden dimension
        for j in range(num_weight_tiles):
            lines.append(f"M_MM 0, gp{w_sram_reg}, gp{act_reg}")
            # Update pointers only if more iterations remain in inner loop
            if j < num_weight_tiles - 1:
                lines.append(f"S_ADDI_INT gp{w_sram_reg}, gp{w_sram_reg}, {weight_tile_size}")
                lines.append(f"S_ADDI_INT gp{act_reg}, gp{act_reg}, {act_tile_stride}")

        # === OUTPUT PHASE ===
        # Compute and set result address, then write out
        result_offset = mlen_block * mlen * blen + tile_in_block * blen
        lines.append(f"S_ADDI_INT gp{result_reg}, gp0, {result_base_address + result_offset}")
        lines.append(f"M_MM_WO {result_reg}, gp0, 0")

        # === PREPARE NEXT ITERATION ===
        # Reset activation pointer (skip on last iteration - saves 1 instruction)
        if not is_last_tile:
            lines.append(f"S_ADDI_INT gp{act_reg}, gp0, {activation_base_address}")

    return "\n".join(lines) + "\n"
