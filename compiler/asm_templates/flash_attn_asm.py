from typing import List

def _general_mlen_mlen_multiply_code(
    mlen: int,
    blen: int,
    alive_registers: List[int],
    reduce_size: int,
    reduce_unit_size: int,
    q_base_address: int,
    k_base_address: int,
    smallest_q_block_size_address: int,
    smallest_kt_block_size_address: int,
    whole_kt_block_size_address: int,
    whole_q_block_size_address: int,
    s_address: int,
) -> str:
    """
    MLEN: buffer size (MLEN * MLEN)
    BLEN: Multiplier block size (BLEN * BLEN)
    reduce_size: the size of the multiplier contracting dimension (usually head_dim)
    reduce_unit_size: the size of the multiplier contracting unit (usually MLEN), it can at most do reduce_unit_size dot product at a time
    q_base_address: Q base address
    k_base_address: K base address
    smallest_q_block_size_address: the size of of the smallest operational block of q. Usually (BLEN * reduce_unit_size)
    smallest_kt_block_size_address: the size of of the smallest operational block of kt. Usually (BLEN * reduce_unit_size)
    whole_kt_block_size_address: the size of the whole kt block. Usually (BLEN * Head_dim)
    whole_q_block_size_address: the size of the whole q block. Usually (BLEN * Head_dim)
    s_address: the target starting address for where to save the result of the dot product
    """

    # get two registers from alive_registers, 1 as q address, 1 as k address
    q_base_register = alive_registers[0]
    k_base_register = alive_registers[1]
    # q and k actual register are used to store the actual address of q and k
    q_actual_register = alive_registers[2]
    k_actual_register = alive_registers[3]
    # block size register is used to store the block size of q and k
    # we will use this block size register to store the address of s too
    block_size_register = alive_registers[4]

    # set q address
    # set k address
    set_q_base_address = f"S_LD_FIX {q_base_register}, gp0, {q_base_address} \n"
    set_k_base_address = f"S_LD_FIX {k_base_register}, gp0, {k_base_address} \n"

    set_q_actual_address = f"S_ADD_FIX {q_actual_register}, gp0, {q_base_register} \n"
    set_k_actual_address = f"S_ADD_FIX {k_actual_register}, gp0, {q_base_register} \n"

    generated_code = ""
    # Q and KT internal loop iteration number
    qkt_loop_iteration_number = mlen // blen
    # contracting loop iteration number
    contracting_loop_iteration_number = reduce_size // reduce_unit_size

    generated_code += set_q_base_address
    generated_code += set_k_base_address
    for i in range(qkt_loop_iteration_number):
        for j in range(qkt_loop_iteration_number):
            generated_code += set_q_actual_address
            generated_code += set_k_actual_address
            for k in range(contracting_loop_iteration_number):
                if k != contracting_loop_iteration_number - 1:
                    # multiply q and kt
                    generated_code += f"M_TMM 0, {q_actual_register}, {k_actual_register} \n"
                else:
                    # multiply q and kt and store to S. No index needed for S. This is an append operation.
                    generated_code += f"S_LD_FIX {block_size_register}, gp0, {s_address} \n"
                    generated_code += f"M_MM_WO {block_size_register}, {q_actual_register}, {k_actual_register} \n"

                # load q block size
                generated_code += f"S_LD_FIX {block_size_register}, gp0, {smallest_q_block_size_address} \n"
                # add q block size to q address
                generated_code += f"S_ADD_FIX {q_actual_register}, {q_actual_register}, {block_size_register} \n"
                # load kt block size
                generated_code += f"S_LD_FIX {block_size_register}, gp0, {smallest_kt_block_size_address} \n"
                # add kt block size to k address
                generated_code += f"S_ADD_FIX {k_actual_register}, {k_actual_register}, {block_size_register} \n"
            
            # load the next internal block of KT
            generated_code += f"S_LD_FIX {block_size_register}, gp0, {whole_kt_block_size_address} \n"
            # add kt block size to k base address
            generated_code += f"S_ADD_FIX {k_base_register}, {k_base_register}, {block_size_register} \n"
        
        # load the next internal block of Q
        generated_code += f"S_LD_FIX {block_size_register}, gp0, {whole_q_block_size_address} \n"
        # add q block size to q base address
        generated_code += f"S_ADD_FIX {q_base_register}, {q_base_register}, {block_size_register} \n"
        # reset k base address
        generated_code += f"S_ADDI_FIX {k_base_register}, gp0, {k_base_address} \n"
    
    return generated_code


def _online_softmax_code(
    mlen: int,
    alive_registers_fix: List[int],
    alive_registers_fp: List[int],
    s_address: int,
    m_last_address: int,
    m_res_address: int,
    l_old_address: int,
) -> str:
    """
    s_address: the starting address of the QKT result
    alive_registers_fix: the list of alive registers for fix point operations
    alive_registers_fp: the list of alive registers for floating point operations
    mlen: also Br: the number of row of the QKT result
    address_of_mlen: the address that contains the mlen (number of row of the QKT result) value 
    """
    # get two registers from alive_registers, 1 as m_last address, 1 as m_curr address
    m_last_register = alive_registers_fp[0]
    m_curr_register = alive_registers_fp[1]
    l_old_register = alive_registers_fp[2]
    # get a general address register
    s_address_register = alive_registers_fix[0]
    general_address_register = alive_registers_fix[1]
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
    alive_registers_fix: List[int],
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
    alive_registers_fix: the list of alive registers for fix point operations
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

    general_address_register = alive_registers_fix[0]
    tmp_fix_register = alive_registers_fix[1]
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
            alive_registers=alive_registers_fix,
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
    alive_registers_fix: List[int],
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
    alive_registers_fix: the list of alive registers for fix point operations
    alive_registers_fp: the list of alive registers for floating point operations
    m_res_address: the address of the m_res
    pv_result_address: the address of the PV result
    o_old_base_address: the base address of the old O
    """
    m_res_vector_address_register = alive_registers_fix[0]
    o_old_vector_address_register = alive_registers_fix[1]
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
    alive_registers_fix: List[int],
    alive_registers_fp: List[int],
    o_old_base_address: int,
    l_old_base_address: int,
) -> str:
    """ 
    line 12 in flash attention algorithm


    mlen: the number of row of the QKT result
    alive_registers_fix: the list of alive registers for fix point operations
    alive_registers_fp: the list of alive registers for floating point operations
    o_old_base_address: the base address of the old O
    """
    o_old_vector_address_register = alive_registers_fix[0]
    l_old_vector_address_register = alive_registers_fix[1]
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
ALIVE_REGISTERS_FIX = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
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
    # qk hbm addresses
    q_hbm_address: int = "a2",
    k_hbm_address: int = "a3",
    v_hbm_address: int = "a4",
    # qkv sram addresses
    q_base_address: int = 0,
    k_base_address: int = 0,
    v_base_address: int = 0,
    # model info
    mlen: int = MLEN,
    head_dim: int = HEAD_DIM,
    blen: int = BLEN,
    seq_len: int = SEQ_LEN,
    # alive registers
    alive_registers_fix: List[int] = ALIVE_REGISTERS_FIX,
    alive_registers_fp: List[int] = ALIVE_REGISTERS_FP,
    # FPSRAM l_old, m_res, m_last addresses
    l_old_base_address: int = FIXED_SRAM_ADDRESS_MAP["l_old_address"],
    m_res_base_address: int = FIXED_SRAM_ADDRESS_MAP["m_res_address"],
    m_last_base_address: int = FIXED_SRAM_ADDRESS_MAP["m_last_address"],
    # Vector SRAM S, PV, O_old addresses
    s_address: int = FIXED_SRAM_ADDRESS_MAP["s_address"],
    pv_result_address: int = FIXED_SRAM_ADDRESS_MAP["pv_result_address"],
    o_old_address: int = FIXED_SRAM_ADDRESS_MAP["o_old_address"],
) -> str:
    generated_code = ""
    q_seq_iteration_number = seq_len // mlen
    k_seq_iteration_number = seq_len // mlen

    # load q from hbm
    generated_code += f"H_PREFETCH_V [rd: gp0, rs1: gp2, rs2: {q_hbm_address}, rstride: 0, precision: activation ];"
    generated_code += f"H_PREFETCH_M [rd: gp0, rs1: gp2, rs2: {k_hbm_address}, rstride: 1, precision: kv ];"
    # loop over different sequence blocks
    for i in range(q_seq_iteration_number):
        for j in range(k_seq_iteration_number):
            generated_code += _general_mlen_mlen_multiply_code(
                mlen=mlen,
                blen=blen,
                alive_registers=alive_registers_fix,
                reduce_size=mlen,
                reduce_unit_size=mlen,
                q_base_address=q_base_address,
                k_base_address=k_base_address,
                smallest_q_block_size_address=FIXED_SRAM_ADDRESS_MAP["q_dot_product_block_size_address"],
                smallest_kt_block_size_address=FIXED_SRAM_ADDRESS_MAP["k_dot_product_block_size_address"],
                whole_kt_block_size_address=FIXED_SRAM_ADDRESS_MAP["k_mm_block_size_address"],
                whole_q_block_size_address=FIXED_SRAM_ADDRESS_MAP["q_mm_block_size_address"],
                s_address=s_address,
            )

            generated_code += _online_softmax_code(
                mlen=mlen,
                alive_registers_fix=alive_registers_fix,
                alive_registers_fp=alive_registers_fp,
                s_address=s_address,
                m_last_address=m_last_base_address,
                m_res_address=m_res_base_address,
                l_old_address=l_old_base_address,
            )

            generated_code += _computing_pv_code(
                mlen=mlen,
                alive_registers_fix=alive_registers_fix,
                alive_registers_fp=alive_registers_fp,
                v_hbm_address=v_hbm_address,
                v_base_address=v_base_address,
                p_base_address=s_address,
                v_block_size_address=FIXED_SRAM_ADDRESS_MAP["v_block_size_address"],
                p_block_size_address=FIXED_SRAM_ADDRESS_MAP["p_block_size_address"],
                head_dim=head_dim,
                blen=blen,
                pv_result_address=pv_result_address,
            )

            generated_code += _computing_o_code(
                mlen=mlen,
                alive_registers_fix=alive_registers_fix,
                alive_registers_fp=alive_registers_fp,
                m_res_base_address=m_res_base_address,
                pv_base_address=pv_result_address,
                o_old_base_address=o_old_address,
                head_dim=head_dim,
            )

            general_address_register = alive_registers_fix[0]
            tmp_fix_register = alive_registers_fix[1]

            # update k base address
            generated_code += f"S_LD_FIX {general_address_register}, gp0, {k_base_address} \n"
            generated_code += f"S_LD_FIX {tmp_fix_register}, gp0, {FIXED_SRAM_ADDRESS_MAP["k_block_size_address"]} \n"
            generated_code += f"S_ADD_FIX {general_address_register}, {general_address_register}, {tmp_fix_register} \n"
            generated_code += f"S_ST_FIX {general_address_register}, gp0, {k_base_address} \n"

            # update s address
            generated_code += f"S_LD_FIX {general_address_register}, gp0, {s_address} \n"
            generated_code += f"S_LD_FIX {tmp_fix_register}, gp0, {FIXED_SRAM_ADDRESS_MAP["s_block_size_address"]} \n"
            generated_code += f"S_ADD_FIX {general_address_register}, {general_address_register}, {tmp_fix_register} \n"
            generated_code += f"S_ST_FIX {general_address_register}, gp0, {s_address} \n"

        generated_code += _computing_row_wise_scaling_code(
            mlen=mlen,
            alive_registers_fix=alive_registers_fix,
            alive_registers_fp=alive_registers_fp,
            o_old_base_address=o_old_address,
            l_old_base_address=l_old_base_address,
        )

        # update q base address
        generated_code += f"S_LD_FIX {general_address_register}, gp0, {q_base_address} \n"
        generated_code += f"S_LD_FIX {tmp_fix_register}, gp0, {FIXED_SRAM_ADDRESS_MAP["q_block_size_address"]} \n"
        generated_code += f"S_ADD_FIX {general_address_register}, {general_address_register}, {tmp_fix_register} \n"
        generated_code += f"S_ST_FIX {general_address_register}, gp0, {q_base_address} \n"
    
    return generated_code