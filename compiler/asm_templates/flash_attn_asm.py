from typing import List
import math
from .reset_reg_asm import reset_reg_asm, reset_fpreg_asm

# Memory Layout:
# -- FP SRAM --
# m old (MLEN)
# m res (MLEN)
# l old (MLEN)

# -- Vector SRAM --
# Q (HEAD_DIM * Hq, MLEN)
# S (MLEN, MLEN)
# PV (Head_Dim * Hq, MLEN)
# O_Old (Head_Dim, MLEN)






def qkt_multiply(
    batch: int,
    mlen: int,
    blen: int,
    hq: int,
    hkv: int,
    d: int,
    s: int,
    alive_registers: List[int],
    q_base_address: int,
    k_base_address: int,
    k_base_hbm_offset_reg: int,
    k_head_index: int,
    q_head_index: int,
    reset_context: bool = False,
    s_base_address: int = 0,
) -> str:
    """
    Args:
        mlen: the number of rows in the first matrix.
        blen: the number of columns in the second matrix.
        hq: the number of heads in the query.
        hkv: the number of heads in the key and value.
        d: the head dimension
        s: the sequence length
        alive_registers: the list of alive registers.
        q_base_address: the base address of the query.
        k_base_address: the base address of the key.
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
    
    # Presettings
    if reset_context:
        generated_code += f"S_ADDI_INT gp{q_base_register}, gp0, {hkv *d * s * batch} \n"
        generated_code += f"C_SET_SCALE_REG gp{q_base_register} \n"
        generated_code += f"S_ADDI_INT gp{q_base_register}, gp0, {hkv * d * batch} \n"
        generated_code += f"C_SET_STRIDE_REG gp{q_base_register} \n"

    # Prefetch K from HBM
    generated_code += f"S_ADDI_INT gp{q_base_register}, gp0, {q_base_address + q_head_index * d} \n"
    generated_code += f"S_ADDI_INT gp{k_base_register}, gp0, {k_base_address + k_head_index * d} \n"
    generated_code += f"H_PREFETCH_M gp{k_base_register}, gp{k_base_register}, a{k_base_hbm_offset_reg}, 1, 1 \n"

    # QKT multiply
    generated_code += f"M_BTMM 0, gp{q_base_register}, gp{k_base_register} \n"
    generated_code += f"S_ADDI_INT gp{s_base_register}, gp0, {mlen * mlen} \n"
    generated_code += f"M_BMM_WO gp{s_base_register}, 0 \n"
    return generated_code


def _online_softmax_code(
    mlen: int,
    alive_registers_int: List[int],
    alive_registers_fp: List[int],
    s_address: int,
    m_start_address: int
) -> str:
    """
    Args:
    s_address: the starting address of the QKT result
    alive_registers_int: the list of alive registers for fix point operations
    alive_registers_fp: the list of alive registers for floating point operations
    mlen: also Br: the number of row of the QKT result
    address_of_mlen: the address that contains the mlen (number of row of the QKT result) value 
    Description:
        This part of asm is for the inner loop of the flash attention, mapping to line 9 to line 10 process,
        which requires per row level computation, hence with the loop mlen times.
    """
    # get two registers from alive_registers, 1 as m_last address, 1 as m_curr address
    m_last_register = alive_registers_fp[0]
    m_curr_register = alive_registers_fp[1]
    l_old_register = alive_registers_fp[2]
    tmp_fp_register = alive_registers_fp[3]
    sum_p_register = alive_registers_fp[4]

    # get a general address register
    s_address_register      = alive_registers_int[0] # general address register
    m_last_address_register = alive_registers_int[1]
    m_res_address_register  = alive_registers_int[2] # m_res address register
    l_old_address_register  = alive_registers_int[3] # l_old address register
    general_address_register = alive_registers_int[4] # general address register
    

    generated_code = "; Online Softmax Code \n"

    # Presettings
    # Load the starting address of S, which is the QKT result of the current head, in shape of (MLEN, MLEN)
    generated_code += f"S_ADDI_INT gp{s_address_register}, gp0, {s_address} \n"
    generated_code += f"S_ADDI_INT gp{m_last_address_register}, gp0, {m_start_address} \n"
    generated_code += f"S_ADDI_INT gp{m_res_address_register}, gp{m_last_address_register}, {mlen} \n"
    generated_code += f"S_ADDI_INT gp{l_old_address_register}, gp{m_res_address_register}, {mlen} \n"

    for i in range(mlen):
        # load m_last
        assert m_start_address < 262144, "m_start_address must be less than 262144"
        generated_code += f"S_LD_FP f{m_last_register}, gp{m_last_address_register}, {i} \n"
        # copy m_last to a tmp fp register
        generated_code += f"S_ADD_FP f{tmp_fp_register}, f{m_last_register}, f0 \n"

        # find max of (P[x4], m_last) and store at m_curr
        generated_code += f"V_RED_MAX f{m_last_register}, gp{s_address_register}, {0} \n"

        # m_res = m_last - m_curr
        generated_code += f"S_SUB_FP f{tmp_fp_register}, f{tmp_fp_register}, f{m_curr_register} \n"

        # exp(m_res)
        generated_code += f"S_EXP_FP f{tmp_fp_register}, f{tmp_fp_register}, 0 \n"

        # store m_res
        generated_code += f"S_ST_FP f{tmp_fp_register}, gp{m_res_address_register}, {i} \n"

        # store m_curr
        generated_code += f"S_ST_FP f{m_curr_register}, gp{m_last_address_register}, {i} \n"
        
        # S' = S - m_curr
        generated_code += f"V_SUB_VF gp{s_address_register}, gp{s_address_register}, f{m_curr_register} \n"

        # P = exp(S')
        generated_code += f"V_EXP_V gp{s_address_register}, gp{s_address_register}, 0 \n"

        # load l_old 
        generated_code += f"S_LD_FP f{l_old_register}, gp{l_old_address_register}, {i} \n"

        # P = sum(P)
        generated_code += f"V_RED_SUM f{sum_p_register}, gp{s_address_register}, 0 \n"

        # l_s = l_old * exp(m_res)
        generated_code += f"S_MUL_FP f{l_old_register}, f{l_old_register}, f{tmp_fp_register} \n"
        l_s_register = l_old_register

        # l_s = l_old * exp(m_res) + sum(P)
        generated_code += f"S_ADD_FP f{l_s_register}, f{sum_p_register}, f{l_s_register} \n"

        # store l_s
        generated_code += f"S_ST_FP f{l_s_register}, gp{l_old_address_register}, {i} \n"

        # next row of S
        generated_code += f"S_ADDI_INT gp{s_address_register}, gp{s_address_register}, {mlen} \n"

    return generated_code

def _computing_pv_code(
    d: int,
    alive_registers: List[int],
    p_base_address: int,
    v_base_address: int,
    v_base_hbm_offset_reg: int,
    q_head_index: int,
    v_head_index: int
) -> str:
    """
    Args:
    
    Description:
        This part of asm is for the computing of the PV operation, mapping to line 10 process,
        which requires per head dimension level computation, hence with the loop head_dim // mlen times.
        (mlen, mlen) @ (mlen, head_dim) = (mlen, head_dim)
    """
    generated_code = "; PV Per KV Head Multiplication \n"
    p_base_register = alive_registers[0]
    v_base_register = alive_registers[1]
    # Prefetch K from HBM
    generated_code += f"S_ADDI_INT gp{p_base_register}, gp0, {p_base_address + q_head_index * d} \n"
    generated_code += f"S_ADDI_INT gp{v_base_register}, gp0, {v_base_address + v_head_index * d} \n"
    generated_code += f"H_PREFETCH_M gp{v_base_register}, gp{v_base_register}, a{v_base_hbm_offset_reg}, 1, 1 \n"

    # QKT multiply
    generated_code += f"M_BTMM 0, gp{p_base_register}, gp{v_base_register} \n"
    generated_code += f"M_BMM_WO gp0, 0 \n"
    return generated_code

# def _computing_o_code(
#     mlen: int,
#     alive_registers_int: List[int],
#     alive_registers_fp: List[int],
#     m_res_base_address: int,
#     pv_base_address: int,
#     o_old_base_address: int,
#     head_dim: int,
# ) -> str:
#     """
#     line 10 in flash attention algorithm

#     head_dim: the head dimension
#     mlen: the number of row of the QKT result
#     alive_registers_int: the list of alive registers for fix point operations
#     alive_registers_fp: the list of alive registers for floating point operations
#     m_res_address: the address of the m_res
#     pv_result_address: the address of the PV result
#     o_old_base_address: the base address of the old O
#     """
#     m_res_vector_address_register = alive_registers_int[0]
#     o_old_vector_address_register = alive_registers_int[1]
#     m_res_fp_register = alive_registers_fp[0]
#     generated_code = ""
#     head_dim_iteration_number = head_dim // mlen
#     # break diag(MLEN) * (MLEN * Head_dim) into diag(MLEN) * [(MLEN * MLEN) ... (MLEN * MLEN)]

#     # load o_old base address
#     generated_code += f"S_LD_FIX {o_old_vector_address_register}, gp0, {o_old_base_address} \n"

#     # computing the diag(MLEN) * (MLEN * MLEN)
#     for i in range(head_dim_iteration_number):
#         # reload m_res base address
#         generated_code += f"S_LD_FIX {m_res_vector_address_register}, gp0, {m_res_base_address} \n"

#         # loop over different row of m_res
#         for j in range(mlen):
#             # load m_res
#             generated_code += f"S_LD_FP {m_res_fp_register}, {m_res_vector_address_register}, {j} \n"
#             # boardcast m_res to multiply with a row of a block of O_old and write to o_old
#             generated_code += f"V_MUL_VF {o_old_vector_address_register}, {o_old_vector_address_register}, {m_res_vector_address_register} \n"
#             # add pv row to o_old
#             generated_code += f"V_ADD_VV {o_old_vector_address_register}, {o_old_vector_address_register}, {pv_base_address} \n"

#             # update o_old base address
#             generated_code += f"S_ADDI_FIX {o_old_vector_address_register}, {o_old_vector_address_register}, {mlen} \n"
#             # update pv base address
#             generated_code += f"S_ADDI_FIX {pv_base_address}, {pv_base_address}, {mlen} \n"


#     # now o_old should contain the result of the current o, diag(exp(m_res)) * O_old + PV
#     return generated_code


# def _computing_row_wise_scaling_code(
#     mlen: int,
#     alive_registers_int: List[int],
#     alive_registers_fp: List[int],
#     o_old_base_address: int,
#     l_old_base_address: int,
# ) -> str:
#     """ 
#     line 12 in flash attention algorithm


#     mlen: the number of row of the QKT result
#     alive_registers_int: the list of alive registers for fix point operations
#     alive_registers_fp: the list of alive registers for floating point operations
#     o_old_base_address: the base address of the old O
#     """
#     o_old_vector_address_register = alive_registers_int[0]
#     l_old_vector_address_register = alive_registers_int[1]
#     l_old_fp_register = alive_registers_fp[0]

#     generated_code = ""
#     # load l_old base address
#     generated_code += f"S_LD_FIX {l_old_vector_address_register}, gp0, {l_old_base_address} \n"
#     # load o_old base address
#     generated_code += f"S_LD_FIX {o_old_vector_address_register}, gp0, {o_old_base_address} \n"

#     # loop over different row of Br
#     for i in range(mlen):
#         # load l_old
#         generated_code += f"S_LD_FP {l_old_fp_register}, {l_old_vector_address_register}, {i} \n"
#         # compute the inverse of l_old
#         generated_code += f"S_RECI_FP {l_old_fp_register}, {l_old_fp_register}, 0 \n"
#         # multiply o_old with the inverse of l_old
#         generated_code += f"V_MUL_VF {o_old_vector_address_register}, {o_old_vector_address_register}, {l_old_fp_register} \n"

#         # update o_old base address
#         generated_code += f"S_ADDI_FIX {o_old_vector_address_register}, {o_old_vector_address_register}, {mlen} \n"

#     return generated_code


# MLEN = 16
# BLEN = 16
# HEAD_DIM = 128
# SEQ_LEN = 2048
# alive_registers_int = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
# ALIVE_REGISTERS_FP = [0, 1, 2, 3, 4, 5, 6, 7]

# FIXED_SRAM_ADDRESS_MAP = {
#     "q_block_size_address": 2,
#     "k_block_size_address": 2,
#     "q_mm_block_size_address": 3,
#     "k_mm_block_size_address": 3,
#     "q_dot_product_block_size_address": 4,
#     "k_dot_product_block_size_address": 4,
#     "v_block_size_address": 4,
#     "p_block_size_address": 4,
#     "s_block_size_address": 5,
#     "m_res_address": 6,
#     "m_last_address": 7,
#     "l_old_address": 8,
#     "pv_result_address": 9,
#     "o_old_address": 10,
#     "s_address": 11,
# }

# FIXED_SRAM_LAYOUT = {
#     0: 0,
#     1: None,
#     2: (MLEN * HEAD_DIM),
#     3: (BLEN * HEAD_DIM),
#     4: (BLEN * MLEN),
#     5: (MLEN * MLEN),
#     6: MLEN,
#     7: 2*MLEN,
#     8: 3 * MLEN,
#     9: (HEAD_DIM * MLEN) + (MLEN * MLEN),
#     10: 2 * (HEAD_DIM * MLEN) + (MLEN * MLEN),
#     11: (MLEN * MLEN),
# }

def flash_attn_asm(
    mlen: int,
    blen: int,
    batch: int,
    hq: int,
    hkv: int,
    d: int,
    seq_len: int,
    alive_registers_int: List[int],
    alive_registers_fp: List[int],
    q_base_address: int,
    k_base_address: int,
    v_base_address: int,
    s_base_address: int,
    m_start_address: int,
    k_base_hbm_offset_reg: int,
    v_base_hbm_offset_reg: int,
) -> str:
    generated_code = ""
    q_seq_iteration_number = (seq_len + mlen - 1) // mlen
    k_seq_iteration_number = (seq_len + mlen - 1) // mlen
    q_index_2_kv_index = hq // hkv
    m_fp_sram_start_address = m_start_address
    # loop over different sequence blocks
    for kv_head_index in range(hkv):
        for i in range(k_seq_iteration_number):
            for j in range(q_seq_iteration_number):
                generated_code += qkt_multiply(
                    mlen=mlen,
                    blen=blen,
                    batch=batch,
                    hq=hq,
                    hkv=hkv,
                    d=d,
                    s=seq_len,
                    alive_registers=alive_registers_int[0:2],
                    q_base_address=q_base_address + j * d,
                    k_base_address=k_base_address + i * d,
                    k_base_hbm_offset_reg=k_base_hbm_offset_reg,
                    q_head_index=q_index_2_kv_index * kv_head_index,
                    k_head_index=kv_head_index,
                    s_base_address=s_base_address,
                    reset_context=True,
                )
                generated_code += reset_reg_asm(alive_registers_int[0:2])

                for head_index in range(hq // hkv):
                    # Per Q head level online softmax
                    generated_code += _online_softmax_code(
                        mlen=mlen,
                        alive_registers_int=alive_registers_int[0:5],
                        alive_registers_fp=alive_registers_fp[0:5],
                        s_address=s_base_address + head_index * mlen * mlen,
                        m_start_address=m_fp_sram_start_address
                    )
                    m_fp_sram_start_address += mlen * 3
                    generated_code += reset_fpreg_asm(alive_registers_fp[0:5])
                    generated_code += reset_reg_asm(alive_registers_int[0:5])
                    break


                generated_code += _computing_pv_code(
                    d=d,
                    alive_registers=alive_registers_int[0:2],
                    p_base_address=s_base_address,
                    v_base_address=v_base_address,
                    v_base_hbm_offset_reg=v_base_hbm_offset_reg,
                    q_head_index=q_index_2_kv_index * kv_head_index,
                    v_head_index=kv_head_index,
                )
                break
            break
        break

        #     generated_code += _computing_o_code(
        #         mlen=mlen,
        #         alive_registers_int=alive_registers_int,
        #         alive_registers_fp=alive_registers_fp,
        #         m_res_base_address=m_res_base_address,
        #         pv_base_address=pv_result_address,
        #         o_old_base_address=o_old_address,
        #         head_dim=head_dim,
        #     )

        #     general_address_register = alive_registers_int[0]
        #     tmp_fix_register = alive_registers_int[1]

        #     # update k base address
        #     generated_code += f"S_LD_FIX {general_address_register}, gp0, {k_base_address} \n"
        #     generated_code += f"S_LD_FIX {tmp_fix_register}, gp0, {FIXED_SRAM_ADDRESS_MAP["k_block_size_address"]} \n"
        #     generated_code += f"S_ADD_FIX {general_address_register}, {general_address_register}, {tmp_fix_register} \n"
        #     generated_code += f"S_ST_FIX {general_address_register}, gp0, {k_base_address} \n"

        #     # update s address
        #     generated_code += f"S_LD_FIX {general_address_register}, gp0, {s_address} \n"
        #     generated_code += f"S_LD_FIX {tmp_fix_register}, gp0, {FIXED_SRAM_ADDRESS_MAP["s_block_size_address"]} \n"
        #     generated_code += f"S_ADD_FIX {general_address_register}, {general_address_register}, {tmp_fix_register} \n"
        #     generated_code += f"S_ST_FIX {general_address_register}, gp0, {s_address} \n"

        # generated_code += _computing_row_wise_scaling_code(
        #     mlen=mlen,
        #     alive_registers_int=alive_registers_int,
        #     alive_registers_fp=alive_registers_fp,
        #     o_old_base_address=o_old_address,
        #     l_old_base_address=l_old_base_address,
        # )

        # # update q base address
        # generated_code += f"S_LD_FIX {general_address_register}, gp0, {q_base_address} \n"
        # generated_code += f"S_LD_FIX {tmp_fix_register}, gp0, {FIXED_SRAM_ADDRESS_MAP["q_block_size_address"]} \n"
        # generated_code += f"S_ADD_FIX {general_address_register}, {general_address_register}, {tmp_fix_register} \n"
        # generated_code += f"S_ST_FIX {general_address_register}, gp0, {q_base_address} \n"
    
    return generated_code