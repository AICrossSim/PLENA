"""Tool for retrieving assembly templates."""

import inspect
import sys
from typing import Dict, Any, Literal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Add compiler to path for imports
sys.path.insert(0, str(PROJECT_ROOT / "compiler"))


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
            - description: Brief description from docstring
            - file_path: Path to the template file
    """
    from asm_templates import (
        ffn_asm,
        flash_attn_asm,
        projection_asm,
        rms_norm_asm,
        embedding_asm,
        elementwise_add_asm,
    )

    # Map layer names to template functions (these are already the functions)
    templates = {
        "ffn": ffn_asm,
        "attention": flash_attn_asm,
        "projection": projection_asm,
        "rms_norm": rms_norm_asm,
        "embedding": embedding_asm,
        "elementwise_add": elementwise_add_asm,
    }

    # Map layer names to file paths
    file_paths = {
        "ffn": PROJECT_ROOT / "compiler" / "asm_templates" / "ffn_asm.py",
        "attention": PROJECT_ROOT / "compiler" / "asm_templates" / "flash_attn_asm.py",
        "projection": PROJECT_ROOT / "compiler" / "asm_templates" / "projection_asm.py",
        "rms_norm": PROJECT_ROOT / "compiler" / "asm_templates" / "normalization_asm.py",
        "embedding": PROJECT_ROOT / "compiler" / "asm_templates" / "embedding_asm.py",
        "elementwise_add": PROJECT_ROOT / "compiler" / "asm_templates" / "elementwise_add_asm.py",
    }

    if layer_name not in templates:
        return {
            "error": f"Unknown layer: {layer_name}. Available: {list(templates.keys())}"
        }

    func = templates[layer_name]
    file_path = file_paths[layer_name]

    try:
        source = inspect.getsource(func)
        signature = str(inspect.signature(func))
        docstring = func.__doc__ or "No description available"

        return {
            "source": source,
            "signature": f"{func.__name__}{signature}",
            "description": docstring.strip(),
            "file_path": str(file_path),
        }
    except Exception as e:
        return {"error": f"Failed to get template: {e}"}


def list_available_templates() -> list:
    """List all available template layer names."""
    return ["ffn", "attention", "projection", "rms_norm", "embedding", "elementwise_add"]
