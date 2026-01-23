from typing import List, Optional

IMM2_BOUND = 2**18  # 262144 - max immediate value for S_ADDI_INT
LUI_SHIFT = 12      # S_LUI_INT shifts immediate by 12 bits


def _load_large_immediate(reg: int, value: int, temp_reg: int = None) -> List[str]:
    """
    Generate assembly to load a potentially large immediate value into a register.

    For values < IMM2_BOUND: uses single S_ADDI_INT
    For larger values: uses S_LUI_INT + S_ADDI_INT or S_MUL_INT

    Args:
        reg: Target register number
        value: Value to load
        temp_reg: Optional temp register for multiplication approach

    Returns:
        List of assembly instruction strings
    """
    lines = []
    if value < IMM2_BOUND:
        # Simple case: fits in immediate
        lines.append(f"S_ADDI_INT gp{reg}, gp0, {value}")
    else:
        # Use S_LUI_INT (load upper immediate) + S_ADDI_INT
        # S_LUI_INT rd, imm -> gp_reg = imm << 12
        upper = value >> LUI_SHIFT
        lower = value & ((1 << LUI_SHIFT) - 1)  # 0xFFF = 4095

        if upper < IMM2_BOUND:
            lines.append(f"S_LUI_INT gp{reg}, {upper}")
            if lower > 0:
                lines.append(f"S_ADDI_INT gp{reg}, gp{reg}, {lower}")
        elif temp_reg is not None:
            # For very large values, use multiplication
            # Find factors that fit in immediate
            # Try to factor value = a * b where both a, b < IMM2_BOUND
            import math
            sqrt_val = int(math.sqrt(value))
            for a in range(sqrt_val, 0, -1):
                if value % a == 0:
                    b = value // a
                    if a < IMM2_BOUND and b < IMM2_BOUND:
                        lines.append(f"S_ADDI_INT gp{reg}, gp0, {a}")
                        lines.append(f"S_ADDI_INT gp{temp_reg}, gp0, {b}")
                        lines.append(f"S_MUL_INT gp{reg}, gp{reg}, gp{temp_reg}")
                        return lines
            # Fallback: shouldn't reach here for reasonable values
            raise ValueError(f"Cannot load value {value} - too large")
        else:
            raise ValueError(f"Value {value} too large, need temp_reg for multiplication")
    return lines


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
) -> str:
    """
    Generates optimized assembly code for matrix multiplication (linear layer).
    (Batch, in_features) @ (in_features, out_features) -> (Batch, out_features)

    Supports both square matrices (hidden_size x hidden_size) and rectangular
    matrices when out_features is specified. Now supports larger weight matrices
    beyond IMM2_BOUND using S_LUI_INT or S_MUL_INT instructions.

    Args:
        mlen: Matrix tile size (rows)
        blen: Vector tile size (batch dimension)
        batch: Batch size (unused, assumed = blen)
        hidden_size: Input dimension (in_features)
        alive_registers: Available GP registers [result, w_actual, w_hbm_offset, a_actual]
        w_base_hbm_offset_reg: HBM address register index for weights
        activation_base_address: Vector SRAM address for activations
        result_base_address: Vector SRAM address for output
        rope_enabled: Whether RoPE is enabled (unused)
        rope_hbm_offset_reg: RoPE HBM address register (unused)
        rope_on_chip_address: RoPE on-chip address (unused)
        out_features: Output dimension. If None, defaults to hidden_size (square matrix)

    Returns:
        Generated assembly code string
    """
    # Suppress unused parameter warnings (API compatibility)
    _ = batch, rope_enabled, rope_hbm_offset_reg, rope_on_chip_address

    # Support rectangular matrices: in_features x out_features
    in_features = hidden_size
    if out_features is None:
        out_features = hidden_size  # Backward compatible: square matrix

    # Unpack registers
    w_actual_register = alive_registers[0]
    w_temp_register = alive_registers[1]
    act_reg = alive_registers[2]
    intermediate_register = alive_registers[3]
    w_hbm_offset_register = alive_registers[4]
    result_reg = alive_registers[5]

    # Compute loop bounds
    num_output_tiles = out_features // blen   # Output tiles (columns of weight)
    num_weight_tiles = in_features // mlen    # Accumulation tiles (rows of weight)
    tiles_per_mlen = mlen // blen             # Tiles fit in one MLEN block

    # Memory layout constants
    weight_tile_size = mlen * mlen            # 4096 for mlen=64
    act_tile_stride = mlen * blen             # 256 for mlen=64, blen=4
    hbm_row_stride = mlen * out_features      # Stride between weight row blocks in HBM

    # Build assembly as list of lines
    lines = ["; Projection Generation (Optimized)"]
    lines.append(f"; Linear: (batch, {in_features}) @ ({in_features}, {out_features}) -> (batch, {out_features})")

    # Setup scale and stride registers (use act_reg as temp)
    # Scale = total weight matrix size, Stride = output dimension
    scale_value = in_features * out_features
    lines.extend(_load_large_immediate(act_reg, scale_value, temp_reg=w_temp_register))
    lines.append(f"C_SET_SCALE_REG gp{act_reg}")
    lines.extend(_load_large_immediate(act_reg, out_features))
    lines.append(f"C_SET_STRIDE_REG gp{act_reg}")

    # Initialize activation register
    lines.append(f"S_ADDI_INT gp{act_reg}, gp0, {activation_base_address}")
    lines.append(f"S_ADDI_INT gp{result_reg}, gp0, {result_base_address}")

    for weight_row in range (out_features // blen):
        if weight_row % (mlen // blen) == 0:
            lines.append(f"S_ADDI_INT gp{w_actual_register}, gp0, 0 ")
            lines.append(f"S_ADDI_INT gp{w_hbm_offset_register}, gp0, {weight_row * blen} ")
            lines.append(f"S_ADDI_INT gp{intermediate_register}, gp{result_reg}, 0 ")
            for weight_col in range (hidden_size // mlen):
                lines.append(f"H_PREFETCH_M gp{w_actual_register}, gp{w_hbm_offset_register}, a{w_base_hbm_offset_reg}, 1, 0 ")
                lines.append(f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {mlen * mlen} ")
                lines.append(f"S_ADDI_INT gp{w_hbm_offset_register}, gp{w_hbm_offset_register}, {mlen * out_features} ")
            lines.append(f"S_ADDI_INT gp{w_actual_register}, gp0, 0 ")
        else:
            lines.append(f"S_ADDI_INT gp{w_actual_register}, gp0, {(weight_row % (mlen // blen)) * blen} ")
            lines.append(f"S_ADDI_INT gp{intermediate_register}, gp{result_reg}, {(weight_row % (mlen // blen)) * blen} ")
        for act_col in range (batch // blen):
            lines.append(f"S_ADDI_INT gp{act_reg}, gp0, {activation_base_address + act_col * mlen * blen} ")
            lines.append(f"S_ADDI_INT gp{w_temp_register}, gp{w_actual_register}, 0 ")
            for inner_loop_index in range (hidden_size // mlen):
                lines.append(f"M_MM 0, gp{w_temp_register}, gp{act_reg} ")
                lines.append(f"S_ADDI_INT gp{w_temp_register}, gp{w_temp_register}, {mlen * mlen} ")
                lines.append(f"S_ADDI_INT gp{act_reg}, gp{act_reg}, {mlen * batch} ")
            lines.append(f"M_MM_WO gp{intermediate_register}, gp0, 0 ")
            lines.append(f"S_ADDI_INT gp{intermediate_register}, gp{intermediate_register}, {blen * mlen} ")    # lines.append f"S_ADDI_INT gp{act_reg}, gp{act_reg}, {activation_base_address} \n"
        if (weight_row + 1) % (mlen // blen) == 0 and weight_row != out_features // blen - 1:
            lines.append(f"S_ADDI_INT gp{result_reg}, gp{result_reg}, {mlen * batch} ")

    return "\n".join(lines) + "\n"
