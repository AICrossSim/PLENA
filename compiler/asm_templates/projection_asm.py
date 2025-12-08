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
    rope_on_chip_address: int = 0,
    use_loop_instructions: bool = False,
) -> str:
    """
    Generates assembly code for matrix multiplication.
    (Batch, Hidden Size) @ (Hidden Size, Hidden Size) -> (Batch, Hidden Size)

    Args:
        mlen: Matrix tile size (rows)
        blen: Vector tile size (batch dimension)
        batch: Batch size (unused, assumed = blen)
        hidden_size: Hidden dimension size
        alive_registers: Available GP registers [result, w_actual, w_hbm_offset, a_actual, loop_outer, loop_inner]
        w_base_hbm_offset_reg: HBM address register index for weights
        activation_base_address: Vector SRAM address for activations
        result_base_address: Vector SRAM address for output
        rope_enabled: Whether RoPE is enabled (unused)
        rope_hbm_offset_reg: RoPE HBM address register (unused)
        rope_on_chip_address: RoPE on-chip address (unused)
        use_loop_instructions: If True, use C_LOOP_START/END for compact code

    Returns:
        Generated assembly code string
    """
    if use_loop_instructions:
        return _projection_asm_with_loops(
            mlen,
            blen,
            batch,
            hidden_size,
            alive_registers,
            w_base_hbm_offset_reg,
            activation_base_address,
            result_base_address,
            rope_enabled,
            rope_hbm_offset_reg,
            rope_on_chip_address,
        )
    else:
        return _projection_asm_unrolled(
            mlen,
            blen,
            batch,
            hidden_size,
            alive_registers,
            w_base_hbm_offset_reg,
            activation_base_address,
            result_base_address,
            rope_enabled,
            rope_hbm_offset_reg,
            rope_on_chip_address,
        )

def _projection_asm_unrolled(
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
    Unrolled implementation with optional RoPE support.

    Without RoPE: requires 4 registers
    With RoPE: requires 8 registers for the RoPE computation phase
    """
    _ = batch  # unused

    # Unpack registers for matmul phase
    result_reg = alive_registers[0]
    w_sram_reg = alive_registers[1]
    w_hbm_reg = alive_registers[2]
    act_reg = alive_registers[3]

    # RoPE registers (reuse after matmul completes)
    if rope_enabled:
        assert len(alive_registers) >= 8, "RoPE requires 8 registers"

    # Compute loop bounds
    num_output_tiles = hidden_size // blen  # 32 tiles for hidden=128, blen=4
    num_weight_tiles = hidden_size // mlen  # 2 tiles for hidden=128, mlen=64
    tiles_per_mlen = mlen // blen           # 16 tiles fit in one MLEN block

    # Memory layout constants
    weight_tile_size = mlen * mlen          # 4096 for mlen=64
    act_tile_stride = mlen * blen           # 256 for mlen=64, blen=4
    hbm_row_stride = mlen * hidden_size     # 8192 for mlen=64, hidden=128

    # Build assembly as list of lines
    lines = ["; Projection Generation (Unrolled)"]

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

    # RoPE phase is currently not implemented - placeholder for future work
    # The stride-mode memory layout makes in-place RoPE challenging

    return "\n".join(lines) + "\n"


def _projection_asm_with_loops(
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
    Optimized implementation using C_LOOP_START/END instructions.

    Uses nested loops:
    - Outer loop: iterates over MLEN blocks (num_mlen_blocks times)
    - Middle loop: iterates over tiles within each MLEN block (tiles_per_mlen times)
    - Inner compute: unrolled for latency hiding (num_weight_tiles M_MM ops)

    Register allocation (matmul phase):
    - result_reg: tracks output SRAM address (incremented each tile)
    - w_sram_reg: weight SRAM base offset for current tile column
    - w_hbm_reg: HBM column offset (incremented each MLEN block)
    - act_reg: activation address (reset each tile)
    - loop_outer_reg: outer loop counter
    - loop_inner_reg: middle loop counter
    - w_tile_offset_reg: tracks tile offset within MLEN block (incremented by blen each tile)

    Without RoPE: requires 7 registers
    With RoPE: requires 8 registers (reuses registers after matmul completes)
    """
    if rope_enabled:
        assert len(alive_registers) >= 8, "RoPE requires 8 registers"

    # Unpack registers (need 3 extra for loop counters and tile offset)
    assert len(alive_registers) >= 7, "Loop version requires 7 registers"
    result_reg = alive_registers[0]
    w_sram_reg = alive_registers[1]
    w_hbm_reg = alive_registers[2]
    act_reg = alive_registers[3]
    loop_outer_reg = alive_registers[4]      # Outer loop counter (MLEN blocks)
    loop_inner_reg = alive_registers[5]      # Middle loop counter (tiles per block)
    w_tile_offset_reg = alive_registers[6]   # Tile offset within MLEN block

    # Compute loop bounds
    num_mlen_blocks = hidden_size // mlen   # Number of MLEN column blocks
    tiles_per_mlen = mlen // blen           # Tiles within each MLEN block
    num_weight_tiles = hidden_size // mlen  # Weight tiles for accumulation

    # Memory layout constants
    weight_tile_size = mlen * mlen          # 4096 for mlen=64
    act_tile_stride = mlen * blen           # 256 for mlen=64, blen=4
    hbm_row_stride = mlen * hidden_size     # 8192 for mlen=64, hidden=128
    result_tile_stride = blen               # Result increment per tile within block

    lines = ["; Projection Generation (Loop-Optimized)"]

    # === SETUP PHASE ===
    # Setup scale and stride registers
    assert hidden_size * hidden_size < IMM2_BOUND
    lines.append(f"S_ADDI_INT gp{act_reg}, gp0, {hidden_size * hidden_size}")
    lines.append(f"C_SET_SCALE_REG gp{act_reg}")
    lines.append(f"S_ADDI_INT gp{act_reg}, gp0, {hidden_size}")
    lines.append(f"C_SET_STRIDE_REG gp{act_reg}")

    # Initialize base addresses
    lines.append(f"S_ADDI_INT gp{act_reg}, gp0, {activation_base_address}")
    lines.append(f"S_ADDI_INT gp{result_reg}, gp0, {result_base_address}")
    lines.append(f"S_ADDI_INT gp{w_hbm_reg}, gp0, 0")  # HBM column offset starts at 0

    # === OUTER LOOP: MLEN blocks ===
    lines.append(f"; Outer loop: {num_mlen_blocks} MLEN blocks")
    lines.append(f"C_LOOP_START gp{loop_outer_reg}, {num_mlen_blocks}")

    # --- Prefetch weights for this MLEN block ---
    lines.append(f"S_ADDI_INT gp{w_sram_reg}, gp0, 0")  # Reset SRAM offset for prefetch

    # Prefetch loop (unrolled - typically small)
    for k in range(num_weight_tiles):
        lines.append(f"H_PREFETCH_M gp{w_sram_reg}, gp{w_hbm_reg}, a{w_base_hbm_offset_reg}, 1, 0")
        if k < num_weight_tiles - 1:
            lines.append(f"S_ADDI_INT gp{w_hbm_reg}, gp{w_hbm_reg}, {hbm_row_stride}")
            lines.append(f"S_ADDI_INT gp{w_sram_reg}, gp{w_sram_reg}, {weight_tile_size}")

    # After prefetch: reset HBM offset back to column start for next block computation
    # HBM advanced by (num_weight_tiles-1)*hbm_row_stride, need to set to mlen offset for next block
    # We'll handle this at end of outer loop

    # Reset tile offset for compute phase
    lines.append(f"S_ADDI_INT gp{w_tile_offset_reg}, gp0, 0")

    # === MIDDLE LOOP: tiles within MLEN block ===
    # Unroll by factor of 8 to reduce loop overhead
    unroll_factor = 1
    loop_iterations = tiles_per_mlen // unroll_factor

    lines.append(f"; Middle loop: {loop_iterations} iterations (unroll={unroll_factor})")
    lines.append(f"C_LOOP_START gp{loop_inner_reg}, {loop_iterations}")

    # Process unroll_factor tiles per loop iteration
    for u in range(unroll_factor):
        # --- Compute: inner accumulation loop (unrolled for latency hiding) ---
        for j in range(num_weight_tiles):
            if j == 0:
                lines.append(f"M_MM 0, gp{w_tile_offset_reg}, gp{act_reg}")
                if num_weight_tiles > 1:
                    lines.append(f"S_ADDI_INT gp{w_sram_reg}, gp{w_tile_offset_reg}, {weight_tile_size}")
            else:
                lines.append(f"M_MM 0, gp{w_sram_reg}, gp{act_reg}")
                if j < num_weight_tiles - 1:
                    lines.append(f"S_ADDI_INT gp{w_sram_reg}, gp{w_sram_reg}, {weight_tile_size}")
            if j < num_weight_tiles - 1:
                lines.append(f"S_ADDI_INT gp{act_reg}, gp{act_reg}, {act_tile_stride}")

        # --- Output and prepare for next tile ---
        lines.append(f"M_MM_WO {result_reg}, gp0, 0")
        lines.append(f"S_ADDI_INT gp{result_reg}, gp{result_reg}, {result_tile_stride}")
        lines.append(f"S_ADDI_INT gp{w_tile_offset_reg}, gp{w_tile_offset_reg}, {blen}")
        if num_weight_tiles > 1:
            lines.append(f"S_ADDI_INT gp{act_reg}, gp0, {activation_base_address}")

    lines.append(f"C_LOOP_END gp{loop_inner_reg}")
    # END middle loop

    # --- Prepare next MLEN block ---
    # Result address correction: after tiles_per_mlen iterations, result_reg has been
    # incremented by tiles_per_mlen * blen. But next block starts at
    # (next_block) * mlen * blen, so we need to add:
    # mlen * blen - tiles_per_mlen * blen = (mlen - tiles_per_mlen) * blen
    # = (mlen - mlen/blen) * blen = mlen * blen - mlen = mlen * (blen - 1)
    # Actually: next_block_start = current_block_start + mlen * blen
    # current position = current_block_start + tiles_per_mlen * blen
    # correction = mlen * blen - tiles_per_mlen * blen = blen * (mlen - tiles_per_mlen)
    result_block_jump = mlen * blen - tiles_per_mlen * blen
    if result_block_jump > 0:
        lines.append(f"S_ADDI_INT gp{result_reg}, gp{result_reg}, {result_block_jump}")

    # HBM offset correction: after prefetch, was at block_start + (num_weight_tiles-1)*hbm_row_stride
    # Next block start: (current_block + 1) * mlen
    # Correction: -(num_weight_tiles-1)*hbm_row_stride + mlen
    hbm_correction = mlen - (num_weight_tiles - 1) * hbm_row_stride
    if hbm_correction >= 0:
        lines.append(f"S_ADDI_INT gp{w_hbm_reg}, gp{w_hbm_reg}, {hbm_correction}")
    else:
        # Need to subtract - load the correction amount and subtract
        # Use w_tile_offset_reg as temp (it's reset at start of next iteration anyway)
        correction_amount = -hbm_correction
        lines.append(f"S_ADDI_INT gp{w_tile_offset_reg}, gp0, {correction_amount}")
        lines.append(f"S_SUB_INT gp{w_hbm_reg}, gp{w_hbm_reg}, gp{w_tile_offset_reg}")

    lines.append(f"C_LOOP_END gp{loop_outer_reg}")
    # END outer loop

    # RoPE phase is currently not implemented - placeholder for future work
    # The stride-mode memory layout makes in-place RoPE challenging

    return "\n".join(lines) + "\n"
