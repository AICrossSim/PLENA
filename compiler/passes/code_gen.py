"""
Code generation pass for LLM symbolic graph to assembly transformation.

This module transforms the symbolic graph representation of a LLM model
into assembly code using predefined templates for different operation types.
"""

import os
from typing import Dict, List, Any, Optional
from pathlib import Path


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
    breakpoint()

    dims = node["dimensions"]
    hidden_size = dims["hidden_size"]
    num_heads = dims["num_attention_heads"]
    head_dim = dims["head_dim"]

    # TODO: break flash attention down into multiple smaller templates for loop
    # TODO: Templates in asm_templates/flash_attention_tr_loop.asm + asm_templates/flash_attention_tc_loop.asm
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

from passes.code_gen_op import _generate_vector_op, _load_hardware_config

def _generate_normalization_code(node: Dict[str, Any]) -> str:
    """Generate assembly code for normalization operations."""
    hardware_config = _load_hardware_config()
    VLEN = hardware_config["VLEN"]
    dims = node["dimensions"]
    normalized_shape = dims["normalized_shape"]
    eps = dims["eps"]
    _n_offset = "TODO"
    _eps_offset = "TODO"
    
    square_code = _generate_vector_op(
        {
            "name": "VMultVv",
            "type": "vector",
            "reg_in_0": "i0",
            "reg_in_1": "i0",
            "reg_out": "i1",
            "loops": normalized_shape // VLEN
        })
    reduction_code = _generate_vector_op(
        {
            "name": "VRedSum",
            "type": "vector",
            "reg_in_0": "i1",
            "reg_out": "f0",
            "loops": normalized_shape // VLEN
        })
    code = f"""
; RMS Normalization: normalized_shape={normalized_shape}, eps={eps}
; Compute RMS and normalize
; initialize reg
LDI i0, 0
SAddiInt i0, i0, 0
SAddiInt i1, i0, 0
; compute square x^2
{square_code}

; compute reduction sum, output to f0
{reduction_code}

; compute load 1/n to f1
SAddiInt i3, i0, {_n_offset}
SLdFp f1, i3, 0

; compute variance
SMulInt f0, f0, f1

; eps + variance
SAddiInt i3, i0, {_eps_offset}
SLdFp f1, i3, 0
SAddFp f0, f0, f1

; compute RMS
SSqrtFp f0, f0
SReciFp f0, f0

; load 1/n to f1
SAddiInt i3, i0, {_n_offset}
SLdFp f1, i3, 0

; normalize

; store result
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