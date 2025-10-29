from typing import List
import math


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

    # Presettings
    if reset_context:
        generated_code = "; QKT Per KV Head Multiplication \n"
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
    generated_code += f"M_BMM_WO gp0, 0 \n"
    return generated_code


def _online_softmax_code(
    mlen: int,
    alive_registers_int: List[int],
    alive_registers_fp: List[int],
    s_address: int,
    m_last_address: int,
    m_res_address: int,
    l_old_address: int,
) -> str:
    """
    s_address: the starting address of the QKT result
    alive_registers_int: the list of alive registers for fix point operations
    alive_registers_fp: the list of alive registers for floating point operations
    mlen: also Br: the number of row of the QKT result
    address_of_mlen: the address that contains the mlen (number of row of the QKT result) value 
    """
    # get two registers from alive_registers, 1 as m_last address, 1 as m_curr address
    m_last_register = alive_registers_fp[0]
    m_curr_register = alive_registers_fp[1]
    l_old_register = alive_registers_fp[2]
    # get a general address register
    s_address_register = alive_registers_int[0]
    general_address_register = alive_registers_int[1]
    # get a general tmp fp register for intermediate result
    tmp_fp_register = alive_registers_fp[3]
    sum_p_register = alive_registers_fp[4]


    # NOTE: you can change this if you have other way to load the address of m_last, m_curr, l_old

    load_s_address = f"""
    S_LD_FIX {general_address_register}, gp0, {s_address} \n
    """

    generated_code = ""
    generated_code += load_s_address

    for i in range(mlen):
        # load m_last
        load_m_last = f"""
        S_LD_FIX {general_address_register}, gp0, {m_last_address} \n
        S_ADDI_FIX {general_address_register}, {general_address_register}, {i-1} \n
        S_LD_FP {m_last_register}, gp0, {general_address_register}
        """
        generated_code += load_m_last

        # copy m_last to a tmp fp register
        generated_code += f"S_MV_FP {tmp_fp_register}, {m_last_register}, 0 \n"

        # find max of (P[x4], m_last) and store at m_curr
        generated_code += f"V_RED_MAX {m_last_register}, {s_address_register}, {0} \n"
        m_curr_register = m_last_register

        # m_res = m_last - m_curr
        generated_code += f"S_SUB_FP {tmp_fp_register}, {tmp_fp_register}, {m_curr_register} \n"
        m_res_register = tmp_fp_register

        # exp(m_res)
        generated_code += f"S_EXP_FP {m_res_register}, {m_res_register}, 0 \n"

        # store m_res
        generated_code += f"S_LD_FIX {general_address_register}, gp0, {m_res_address} \n"
        generated_code += f"S_ADDI_FIX {general_address_register}, {general_address_register}, {i} \n"
        generated_code += f"S_ST_FP {m_res_register}, {general_address_register}, {0} \n"

        # store m_curr
        generated_code += f"S_LD_FIX {general_address_register}, gp0, {m_last_address} \n"
        generated_code += f"S_ADDI_FIX {general_address_register}, {general_address_register}, {i} \n"
        generated_code += f"S_ST_FP {m_curr_register}, {general_address_register}, {0} \n"
        
        # S' = S - m_curr
        generated_code += f"V_SUB_VF {s_address_register}, {s_address_register}, {m_curr_register} \n"
        # P = exp(S')
        generated_code += f"V_EXP_V {s_address_register}, {s_address_register}, 0 \n"

        # load l_old 
        load_l_old = f"""
        S_LD_FIX {general_address_register}, gp0, {l_old_address} \n
        S_ADDI_FIX {general_address_register}, {general_address_register}, {i-1} \n
        S_LD_FP {l_old_register}, gp0, {general_address_register}
        """
        generated_code += load_l_old

        # P = sum(P)
        generated_code += f"V_RED_SUM {sum_p_register}, {s_address_register}, 0 \n"

        # l_s = l_old * exp(m_res)
        generated_code += f"S_MUL_FP {l_old_register}, {l_old_register}, {m_res_register} \n"
        l_s_register = l_old_register

        # l_s = l_old * exp(m_res) + sum(P)
        generated_code += f"S_ADD_FP {l_s_register}, {sum_p_register}, {l_s_register} \n"

        # store l_s
        generated_code += f"S_LD_FIX {general_address_register}, gp0, {l_old_address} \n"
        generated_code += f"S_ADDI_FIX {general_address_register}, {general_address_register}, {i} \n"
        generated_code += f"S_ST_FP {l_s_register}, {general_address_register}, 0 \n"

        # next row of S
        generated_code += f"S_ADD_FIX {s_address_register}, {s_address_register}, {mlen} \n"

    return generated_code

def _computing_pv_code(
    mlen: int,
    alive_registers_int: List[int],
    alive_registers_fp: List[int],
    v_hbm_address: int,
    v_base_address: int,
    p_base_address: int,
    v_block_size_address: int,
    p_block_size_address: int,
    head_dim: int,
    blen: int,
    pv_result_address: int,
) -> str:
    """
    mlen: the number of row of the QKT result
    head_dim: the head dimension
    blen: the block size
    alive_registers_int: the list of alive registers for fix point operations
    alive_registers_fp: the list of alive registers for floating point operations
    v_base_address: the base address of V
    p_base_address: the base address of P
    v_actual_address: the actual address of V
    p_actual_address: the actual address of P
    v_block_size_address: the address of the block size of V: address pointing to BLEN * MLEN
    p_block_size_address: the address of the block size of P: address pointing to BLEN * MLEN
    pv_result_address: the address of the result of the PV operation
    """
    v_head_dim_iteration_number = head_dim // mlen

    general_address_register = alive_registers_int[0]
    tmp_fix_register = alive_registers_int[1]
    generated_code = ""

    # load v from hbm
    generated_code += f"H_PREFETCH_V [rd: gp0, rs1: gp2, rs2: {v_hbm_address}, rstride: 0, precision: kv ];"

    for i in range(v_head_dim_iteration_number):
        p_actual_address = p_base_address

        # update pv_result_address
        generated_code += f"S_LD_FIX {general_address_register}, gp0, {pv_result_address} \n"
        generated_code += f"S_LD_FIX {tmp_fix_register}, gp0, {FIXED_SRAM_ADDRESS_MAP["s_block_size_address"]} \n"
        generated_code += f"S_ADD_FIX {general_address_register}, {general_address_register}, {tmp_fix_register} \n"
        generated_code += f"S_ST_FIX {general_address_register}, gp0, {pv_result_address} \n"

        # update v_actual_address
        generated_code += f"S_LD_FIX {general_address_register}, gp0, {v_base_address} \n"
        generated_code += f"S_LD_FIX {tmp_fix_register}, gp0, {FIXED_SRAM_ADDRESS_MAP["s_block_size_address"]} \n"
        generated_code += f"S_ADD_FIX {general_address_register}, {general_address_register}, {tmp_fix_register} \n"
        generated_code += f"S_ST_FIX {general_address_register}, gp0, {v_base_address} \n"


        generated_code += _general_mlen_mlen_multiply_code(
            mlen=mlen,
            blen=blen,
            alive_registers=alive_registers_int,
            reduce_size=mlen,
            reduce_unit_size=mlen,
            q_base_address=v_base_address,
            k_base_address=p_actual_address,
            smallest_q_block_size_address=v_block_size_address,
            smallest_kt_block_size_address=p_block_size_address,
            whole_kt_block_size_address=v_block_size_address,
            whole_q_block_size_address=p_block_size_address,
            s_address=pv_result_address,
        )
        # ;<<<< -------Complete PV------- >>>>
    return generated_code

def _computing_o_code(
    mlen: int,
    alive_registers_int: List[int],
    alive_registers_fp: List[int],
    m_res_base_address: int,
    pv_base_address: int,
    o_old_base_address: int,
    head_dim: int,
) -> str:
    """
    line 10 in flash attention algorithm

    head_dim: the head dimension
    mlen: the number of row of the QKT result
    alive_registers_int: the list of alive registers for fix point operations
    alive_registers_fp: the list of alive registers for floating point operations
    m_res_address: the address of the m_res
    pv_result_address: the address of the PV result
    o_old_base_address: the base address of the old O
    """
    m_res_vector_address_register = alive_registers_int[0]
    o_old_vector_address_register = alive_registers_int[1]
    m_res_fp_register = alive_registers_fp[0]
    generated_code = ""
    head_dim_iteration_number = head_dim // mlen
    # break diag(MLEN) * (MLEN * Head_dim) into diag(MLEN) * [(MLEN * MLEN) ... (MLEN * MLEN)]

    # load o_old base address
    generated_code += f"S_LD_FIX {o_old_vector_address_register}, gp0, {o_old_base_address} \n"

    # computing the diag(MLEN) * (MLEN * MLEN)
    for i in range(head_dim_iteration_number):
        # reload m_res base address
        generated_code += f"S_LD_FIX {m_res_vector_address_register}, gp0, {m_res_base_address} \n"

        # loop over different row of m_res
        for j in range(mlen):
            # load m_res
            generated_code += f"S_LD_FP {m_res_fp_register}, {m_res_vector_address_register}, {j} \n"
            # boardcast m_res to multiply with a row of a block of O_old and write to o_old
            generated_code += f"V_MUL_VF {o_old_vector_address_register}, {o_old_vector_address_register}, {m_res_vector_address_register} \n"
            # add pv row to o_old
            generated_code += f"V_ADD_VV {o_old_vector_address_register}, {o_old_vector_address_register}, {pv_base_address} \n"

            # update o_old base address
            generated_code += f"S_ADDI_FIX {o_old_vector_address_register}, {o_old_vector_address_register}, {mlen} \n"
            # update pv base address
            generated_code += f"S_ADDI_FIX {pv_base_address}, {pv_base_address}, {mlen} \n"


    # now o_old should contain the result of the current o, diag(exp(m_res)) * O_old + PV
    return generated_code


def _computing_row_wise_scaling_code(
    mlen: int,
    alive_registers_int: List[int],
    alive_registers_fp: List[int],
    o_old_base_address: int,
    l_old_base_address: int,
) -> str:
    """ 
    line 12 in flash attention algorithm


    mlen: the number of row of the QKT result
    alive_registers_int: the list of alive registers for fix point operations
    alive_registers_fp: the list of alive registers for floating point operations
    o_old_base_address: the base address of the old O
    """
    o_old_vector_address_register = alive_registers_int[0]
    l_old_vector_address_register = alive_registers_int[1]
    l_old_fp_register = alive_registers_fp[0]

    generated_code = ""
    # load l_old base address
    generated_code += f"S_LD_FIX {l_old_vector_address_register}, gp0, {l_old_base_address} \n"
    # load o_old base address
    generated_code += f"S_LD_FIX {o_old_vector_address_register}, gp0, {o_old_base_address} \n"

    # loop over different row of Br
    for i in range(mlen):
        # load l_old
        generated_code += f"S_LD_FP {l_old_fp_register}, {l_old_vector_address_register}, {i} \n"
        # compute the inverse of l_old
        generated_code += f"S_RECI_FP {l_old_fp_register}, {l_old_fp_register}, 0 \n"
        # multiply o_old with the inverse of l_old
        generated_code += f"V_MUL_VF {o_old_vector_address_register}, {o_old_vector_address_register}, {l_old_fp_register} \n"

        # update o_old base address
        generated_code += f"S_ADDI_FIX {o_old_vector_address_register}, {o_old_vector_address_register}, {mlen} \n"

    return generated_code


MLEN = 16
BLEN = 16
HEAD_DIM = 128
SEQ_LEN = 2048
alive_registers_int = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
ALIVE_REGISTERS_FP = [0, 1, 2, 3, 4, 5, 6, 7]

FIXED_SRAM_ADDRESS_MAP = {
    "q_block_size_address": 2,
    "k_block_size_address": 2,
    "q_mm_block_size_address": 3,
    "k_mm_block_size_address": 3,
    "q_dot_product_block_size_address": 4,
    "k_dot_product_block_size_address": 4,
    "v_block_size_address": 4,
    "p_block_size_address": 4,
    "s_block_size_address": 5,
    "m_res_address": 6,
    "m_last_address": 7,
    "l_old_address": 8,
    "pv_result_address": 9,
    "o_old_address": 10,
    "s_address": 11,
}

FIXED_SRAM_LAYOUT = {
    0: 0,
    1: None,
    2: (MLEN * HEAD_DIM),
    3: (BLEN * HEAD_DIM),
    4: (BLEN * MLEN),
    5: (MLEN * MLEN),
    6: MLEN,
    7: 2*MLEN,
    8: 3 * MLEN,
    9: (HEAD_DIM * MLEN) + (MLEN * MLEN),
    10: 2 * (HEAD_DIM * MLEN) + (MLEN * MLEN),
    11: (MLEN * MLEN),
}

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
    k_base_hbm_offset_reg: int,
) -> str:
    generated_code = ""
    q_seq_iteration_number = (seq_len + mlen - 1) // mlen
    k_seq_iteration_number = (seq_len + mlen - 1) // mlen
    q_index_2_kv_index = hq // hkv

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
                    alive_registers=alive_registers_int,
                    q_base_address=q_base_address + j * d,
                    k_base_address=k_base_address + i * d,
                    k_base_hbm_offset_reg=k_base_hbm_offset_reg,
                    q_head_index=q_index_2_kv_index * kv_head_index,
                    k_head_index=kv_head_index,
                    reset_context=True,
                )
                break
            break
        break

        #     generated_code += _online_softmax_code(
        #         mlen=mlen,
        #         alive_registers_int=alive_registers_int,
        #         alive_registers_fp=alive_registers_fp,
        #         s_address=s_address,
        #         m_last_address=m_last_base_address,
        #         m_res_address=m_res_base_address,
        #         l_old_address=l_old_base_address,
        #     )

        #     generated_code += _computing_pv_code(
        #         mlen=mlen,
        #         alive_registers_int=alive_registers_int,
        #         alive_registers_fp=alive_registers_fp,
        #         v_hbm_address=v_hbm_address,
        #         v_base_address=v_base_address,
        #         p_base_address=s_address,
        #         v_block_size_address=FIXED_SRAM_ADDRESS_MAP["v_block_size_address"],
        #         p_block_size_address=FIXED_SRAM_ADDRESS_MAP["p_block_size_address"],
        #         head_dim=head_dim,
        #         blen=blen,
        #         pv_result_address=pv_result_address,
        #     )

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