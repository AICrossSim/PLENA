"""
Code generation pass for LLM symbolic graph to assembly transformation.

This module transforms the symbolic graph representation of a LLM model
into assembly code using predefined templates for different operation types.
"""

import os
from typing import Dict, List, Any, Optional
from pathlib import Path



# required register number 
# reduce size
# reduce unit size
# base address 1
# base address 2
# target address 1

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

MLEN = 16
def _online_softmax_code(
    mlen: int,
    alive_registers_fix: List[int],
    alive_registers_fp: List[int],
    s_address: int,
    m_last_address: int = MLEN,
    m_res_address: int = 2*MLEN,
    l_old_address: int = 3*MLEN,
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
    v_base_address: int,
    p_base_address: int,
    v_actual_address: int,
    p_actual_address: int,
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

    generated_code = ""
    for i in range(v_head_dim_iteration_number):
        pv_result_address = pv_result_address + i * mlen * mlen
        v_actual_address = v_base_address + mlen * mlen
        p_actual_address = p_base_address

        generated_code += _general_mlen_mlen_multiply_code(
            mlen=mlen,
            blen=blen,
            alive_registers=alive_registers_fix,
            reduce_size=mlen,
            reduce_unit_size=mlen,
            q_base_address=v_actual_address,
            k_base_address=p_actual_address,
            smallest_q_block_size_address=v_block_size_address,
            smallest_kt_block_size_address=p_block_size_address,
            whole_kt_block_size_address=v_block_size_address,
            whole_q_block_size_address=p_block_size_address,
            s_address=pv_result_address,
        )
        # ;<<<< -------Complete PV------- >>>>
    return generated_code


    

def _load_template(template_name: str) -> str:
    """Load assembly template from file."""
    templates_dir = Path(__file__).parent.parent / "asm_templates"
    template_path = templates_dir / f"{template_name}.asm"

    if not template_path.exists():
        raise FileNotFoundError(f"Template {template_name}.asm not found in {templates_dir}")

    with open(template_path, "r") as f:
        return f.read()


def _generate_embedding_code(node: Dict[str, Any]) -> str:
    """Generate assembly code for embedding operations."""
    vocab_size = node["dimensions"]["num_embeddings"]
    embedding_dim = node["dimensions"]["embedding_dim"]

    code = f"""
; Embedding lookup: vocab_size={vocab_size}, embedding_dim={embedding_dim}
; Input: token_ids, Output: embedded_vectors
TODO: fill me
"""
    return code.strip()


def _generate_attention_code(node: Dict[str, Any]) -> str:
    """Generate assembly code for attention operations."""
    projection_template = _load_template("fake_projection")
    flash_attention_template = _load_template("flash_attention")

    dims = node["dimensions"]
    hidden_size = dims["hidden_size"]
    num_heads = dims["num_attention_heads"]
    head_dim = dims["head_dim"]

    # TODO: break flash attention down into multiple smaller templates for loop
    code = f"""
; Self-attention: hidden_size={hidden_size}, num_heads={num_heads}, head_dim={head_dim}
; Q, K, V projections and attention computation
{projection_template}

; Flash Attention Implementation
{flash_attention_template}
"""
    return code.strip()


def _generate_ffn_code(node: Dict[str, Any]) -> str:
    """Generate assembly code for FFN/MLP operations."""
    template = _load_template("projection")

    dims = node["dimensions"]
    hidden_size = dims["hidden_size"]
    intermediate_size = dims["intermediate_size"]
    activation = dims["activation"]

    code = f"""
; FFN/MLP: hidden_size={hidden_size}, intermediate_size={intermediate_size}, activation={activation}
; Gate and Up projections
{template}
; FFN operations
TODO: fill me
{template}
"""
    return code.strip()


def _generate_normalization_code(node: Dict[str, Any]) -> str:
    """Generate assembly code for normalization operations."""
    dims = node["dimensions"]
    normalized_shape = dims["normalized_shape"]
    eps = dims["eps"]

    code = f"""
; RMS Normalization: normalized_shape={normalized_shape}, eps={eps}
; Compute RMS and normalize
TODO: fill me
"""
    return code.strip()


def _generate_elementwise_add_code(node: Dict[str, Any]) -> str:
    """Generate assembly code for elementwise addition (residual connections)."""
    dims = node["dimensions"]
    shape = dims["shape"]

    code = f"""
; Elementwise addition (residual connection): shape={shape}
; Add two tensors element-wise
TODO: fill me
"""
    return code.strip()


def _generate_node_code(node: Dict[str, Any]) -> str:
    """Generate assembly code for a single symbolic graph node."""
    operation_type = node["operation_type"]
    node_name = node["name"]

    header = f"\n; === {node_name} ({operation_type}) ===\n"

    if operation_type == "embedding":
        return header + _generate_embedding_code(node)
    elif operation_type == "attention":
        return header + _generate_attention_code(node)
    elif operation_type == "ffn":
        return header + _generate_ffn_code(node)
    elif operation_type == "normalization":
        return header + _generate_normalization_code(node)
    elif operation_type == "elementwise_add":
        return header + _generate_elementwise_add_code(node)
    else:
        raise ValueError(f"Unknown operation type: {operation_type}")


def _generate_program_header(model_info: Dict[str, Any]) -> str:
    """Generate program header with model information."""
    return f"""
; Generated assembly code for LLM model
; Model: {model_info.get("model_name", "Unknown")}
; Architecture: {model_info.get("architecture", "Unknown")}
; Hidden size: {model_info.get("hidden_size", "Unknown")}
; Number of layers: {model_info.get("num_layers", "Unknown")}
; Generated by LLM Compiler
"""


def _generate_program_footer() -> str:
    """Generate program footer."""
    return """
    ; Program termination
"""


def code_gen_pass(symbolic_graph: Dict[str, Any], model_info: Dict[str, Any]) -> str:
    """
    Transform the complete symbolic graph into assembly code.

    Args:
        symbolic_graph: The symbolic graph from LLMModelParser
        model_info: Model metadata for header generation

    Returns:
        Complete assembly program as string
    """
    # Generate program header
    asm_code = [_generate_program_header(model_info)]

    # Process each node in execution order
    nodes = symbolic_graph["nodes"]
    execution_order = symbolic_graph["execution_order"]

    # Create a mapping from node names to nodes for efficient lookup
    node_map = {node["name"]: node for node in nodes}

    # Generate code for each node in execution order
    for node_name in execution_order:
        if node_name in node_map:
            node = node_map[node_name]
            node_code = _generate_node_code(node)
            asm_code.append(node_code)

    # Add program footer
    asm_code.append(_generate_program_footer())

    return "\n".join(asm_code)