"""QKT multiplication assembly code generation for Flash Attention."""

from typing import List

IMM2_BOUND = 2**18 - 1


def qkt_multiply(
    d: int,
    mlen: int,
    alive_registers: List[int],
    q_base_address: int,
    k_base_hbm_offset_reg: int,
    q_head_index: int,
    k_head_index: int,
    s_base_address: int = 0,
    q_row_stride: int = 1,  # Stride for Q row access in units of MLEN (= hq * d / mlen)
) -> str:
    """
    Args:
        mlen: the number of rows in the first matrix.
        blen: the number of columns in the second matrix.
        d: the head dimension
        q_len: the query length
        alive_registers: the list of alive registers.
        q_base_address: the base address of the query.
        k_base_address: the base address of the key.
        q_row_stride: stride for Q row access (= hq * d / mlen). For Q layout [s_q, hq, d],
                      each token row has hq * d elements, so stride = (hq * d) / mlen.
    Description:
        This part of asm code gen template is used to compute QKT result.
        Assuming Q is in dim of (B, S, Hq, D), K is in dim of (B, S, Hkv, D)
        The num of Hq // Hkv of Q heads share the same K head.
        This template will perform, single batch, MLEN tiled, per KV head, QKT multiplication.
        (MLEN, Hq // Hkv, D) @ broadcast(D, 1, MLEN) = (Hq // Hkv, MLEN, MLEN)
    """
    q_base_register = alive_registers[0]
    k_base_register = alive_registers[1]
    s_base_register = q_base_register
    generated_code = "; QKT Per KV Head Multiplication \n"

    # Set Q row stride for M_BTMM
    # M_BTMM uses mm_load_stride to determine Q row spacing: v_addr + i * mlen * stride_len
    # For Q layout [s_q, hq, d], each token has hq * d elements, so stride = (hq * d) / mlen
    generated_code += f"S_ADDI_INT gp{q_base_register}, gp0, {q_row_stride} \n"
    generated_code += f"C_SET_STRIDE_REG gp{q_base_register} \n"

    # Prefetch K from HBM
    generated_code += f"S_ADDI_INT gp{q_base_register}, gp0, {q_base_address + q_head_index * d} \n"
    generated_code += f"S_ADDI_INT gp{k_base_register}, gp0, {k_head_index * d} \n"
    # Use stride_en=0 for contiguous prefetch to avoid 64-byte alignment issues
    # When stride < 64 elements, strided access causes unaligned HBM reads
    # Parameter order: rd, rs1, rs2, rstride(stride_en), funct1(scale_en)
    generated_code += f"H_PREFETCH_M gp{k_base_register}, gp{k_base_register}, a{k_base_hbm_offset_reg}, 0, 1 \n"

    # QKT multiply
    generated_code += f"M_BTMM 0, gp{q_base_register}, gp{k_base_register} \n"
    generated_code += f"S_ADDI_INT gp{s_base_register}, gp0, {s_base_address + q_head_index * mlen * mlen} \n"
    generated_code += f"M_BMM_WO gp{s_base_register}, 0 \n"

    return generated_code
