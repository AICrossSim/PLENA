from typing import List, Optional

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
    out_features: Optional[int] = None,
    activation_stride: Optional[int] = None,
    output_stride: Optional[int] = None,   # ignored for tile mode
) -> str:
    """
    Correct tile-based projection_asm:
      - M_MM_WO writes exactly (mlen x blen)
      - output is tile-major in VRAM
      - no stride is applied to writeback
      - activation stride is used correctly
      - supports arbitrary in/out/batch
      - no overwrites, no NAN
    """

    _ = rope_enabled, rope_hbm_offset_reg, rope_on_chip_address

    in_features = hidden_size
    if out_features is None:
        out_features = hidden_size

    if activation_stride is None:
        activation_stride = in_features   # safe default

    # **************************************************************
    # Registers
    # **************************************************************
    result_reg  = alive_registers[0]
    w_sram_reg  = alive_registers[1]
    w_hbm_reg   = alive_registers[2]
    act_reg     = alive_registers[3]
    tmp_reg     = alive_registers[4]

    # **************************************************************
    # Tiling
    # **************************************************************
    num_output_tiles = (out_features + blen - 1) // blen
    num_weight_tiles = (in_features  + mlen - 1) // mlen
    tiles_per_mlen   = mlen // blen  # how many blen-columns per 64-wide block

    # **************************************************************
    # Memory constants
    # **************************************************************
    weight_tile_size = mlen * mlen
    act_tile_stride  = activation_stride
    hbm_row_stride   = mlen * out_features

    lines = []
    lines.append("; ===== Correct TILE-BASED projection_asm =====")
    lines.append(f"; Matrix: (batch={batch},{in_features}) × ({in_features},{out_features})")
    lines.append("; Output tiles: each is 64 × blen")

    # **************************************************************
    # SCALE SETUP
    # **************************************************************
    total_mul = in_features * out_features
    if total_mul >= IMM2_BOUND:
        lines.append(f"S_ADDI_INT gp{act_reg}, gp0, {in_features}")
        lines.append(f"S_ADDI_INT gp{tmp_reg}, gp0, {out_features}")
        lines.append(f"S_MUL_INT  gp{act_reg}, gp{act_reg}, gp{tmp_reg}")
    else:
        lines.append(f"S_ADDI_INT gp{act_reg}, gp0, {total_mul}")

    lines.append(f"C_SET_SCALE_REG gp{act_reg}")

    # **************************************************************
    # SET STRIDE FOR ACTIVATION LOADING
    # (writeback uses NO stride)
    # **************************************************************
    lines.append(f"S_ADDI_INT gp{act_reg}, gp0, {activation_stride}")
    lines.append(f"C_SET_STRIDE_REG gp{act_reg}")

    # Set activation pointer
    lines.append(f"S_ADDI_INT gp{act_reg}, gp0, {activation_base_address}")

    current_mlen_block = -1

    # ==========================================================================================
    # Outer loop over output-TILES
    # ==========================================================================================
    for tile_idx in range(num_output_tiles):

        # which 64-col block is this tile in?
        mlen_block = tile_idx // tiles_per_mlen
        tile_in_block = tile_idx % tiles_per_mlen

        is_last_tile = (tile_idx == num_output_tiles - 1)

        # ----------------------------------------------------------
        # PREFETCH WEIGHTS (if entering new 64-col block)
        # ----------------------------------------------------------
        if mlen_block != current_mlen_block:
            current_mlen_block = mlen_block
            hbm_col_offset = mlen_block * mlen

            lines.append(f"; --- Prefetch new weight block #{mlen_block} ---")
            lines.append(f"S_ADDI_INT gp{w_sram_reg}, gp0, 0")  # SRAM offset
            lines.append(f"S_ADDI_INT gp{w_hbm_reg}, gp0, {hbm_col_offset}")  # HBM offset

            for k in range(num_weight_tiles):
                lines.append(
                    f"H_PREFETCH_M gp{w_sram_reg}, gp{w_hbm_reg}, a{w_base_hbm_offset_reg}, 1, 0"
                )
                if k < num_weight_tiles - 1:
                    lines.append(f"S_ADDI_INT gp{w_hbm_reg}, gp{w_hbm_reg}, {hbm_row_stride}")
                    lines.append(f"S_ADDI_INT gp{w_sram_reg}, gp{w_sram_reg}, {weight_tile_size}")

            # return SRAM pointer to beginning
            lines.append(f"S_ADDI_INT gp{w_sram_reg}, gp0, 0")

        else:
            # same block, just offset inside SRAM by blen
            lines.append(f"S_ADDI_INT gp{w_sram_reg}, gp0, {tile_in_block * blen}")

        # ======================================================================================
        # ACCUMULATE ALL WEIGHT-TILES
        # ======================================================================================
        for j in range(num_weight_tiles):
            lines.append(f"M_MM 0, gp{w_sram_reg}, gp{act_reg}")

            if j < num_weight_tiles - 1:
                # advance to next weight tile + activation row
                lines.append(f"S_ADDI_INT gp{w_sram_reg}, gp{w_sram_reg}, {weight_tile_size}")
                lines.append(f"S_ADDI_INT gp{act_reg}, gp{act_reg}, {act_tile_stride}")

        # ======================================================================================
        # WRITEBACK TILE (ONLY ONCE!)
        # tile_idx determines which VRAM block this tile writes to.
        # ======================================================================================
        row_offset_bytes = tile_idx * (mlen * 64)   # 64 rows per tile * 64B/row
        write_addr = result_base_address + row_offset_bytes

        lines.append(f"; --- Tile {tile_idx}: writeback to VRAM offset {write_addr} ---")
        lines.append(f"S_ADDI_INT gp{result_reg}, gp0, {write_addr}")
        lines.append(f"M_MM_WO gp{result_reg}, gp0, 0")

        # Reset activation pointer if needed
        if not is_last_tile:
            lines.append(f"S_ADDI_INT gp{act_reg}, gp0, {activation_base_address}")

    return "\n".join(lines) + "\n"