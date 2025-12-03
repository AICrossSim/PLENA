"""Tool for retrieving assembly templates."""

from typing import Dict, Any, Literal


def get_template(
    layer_name: Literal["ffn", "attention", "projection", "rms_norm", "embedding", "elementwise_add"]
) -> Dict[str, Any]:
    """
    Get Python assembly template source code for a layer type.

    Args:
        layer_name: One of 'ffn', 'attention', 'projection', 'rms_norm', 'embedding', 'elementwise_add'

    Returns:
        Dict with:
            - source: Template source code
            - signature: Function signature with parameters
            - description: Brief description
    """
    # TODO: Implement template retrieval
    #
    # Template files are in: compiler/asm_templates/
    # - ffn_asm.py
    # - flash_attn_asm.py
    # - projection_asm.py
    # - normalization_asm.py
    # - embedding_asm.py
    # - elementwise_add_asm.py
    #
    # Example implementation:
    # import inspect
    # from compiler.asm_templates import (
    #     ffn_asm, flash_attn_asm, projection_asm,
    #     rms_norm_asm, embedding_asm, elementwise_add_asm
    # )
    #
    # templates = {
    #     "ffn": ffn_asm,
    #     "attention": flash_attn_asm,
    #     "projection": projection_asm,
    #     "rms_norm": rms_norm_asm,
    #     "embedding": embedding_asm,
    #     "elementwise_add": elementwise_add_asm,
    # }
    #
    # func = templates.get(layer_name)
    # if not func:
    #     raise ValueError(f"Unknown layer: {layer_name}. Available: {list(templates.keys())}")
    #
    # return {
    #     "source": inspect.getsource(func),
    #     "signature": str(inspect.signature(func)),
    #     "description": func.__doc__ or ""
    # }

    raise NotImplementedError("get_template not implemented")
