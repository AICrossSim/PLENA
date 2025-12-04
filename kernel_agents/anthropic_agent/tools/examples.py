"""Tool for getting assembly code examples."""

from typing import Literal, Dict, Any, Optional
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def get_assembly_code_examples(
    mode: Literal["one-shot", "few-shot"] = "one-shot",
    layer_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get assembly code examples for reference.

    Args:
        mode: 'one-shot' for single example, 'few-shot' for multiple examples
        layer_type: Optional filter for layer type (e.g., 'projection', 'rms', 'attention', 'gemm', 'vector')

    Returns:
        Dict with:
            - examples: List of assembly code examples with name and code
            - count: Number of examples returned
    """
    # Example directories
    layer_dir = PROJECT_ROOT / "test" / "Layerwise_Benchmark"
    instr_dir = PROJECT_ROOT / "test" / "Instr_Level_Benchmark"

    examples = []

    # Collect layer-wise examples (higher priority)
    if layer_dir.exists():
        for asm_file in sorted(layer_dir.glob("*.asm")):
            if layer_type and layer_type.lower() not in asm_file.stem.lower():
                continue
            try:
                with open(asm_file) as f:
                    code = f.read()
                examples.append({
                    "name": asm_file.stem,
                    "type": "layerwise",
                    "code": code,
                    "file_path": str(asm_file),
                })
            except Exception as e:
                continue

    # Collect instruction-level examples
    if instr_dir.exists():
        for asm_file in sorted(instr_dir.glob("*.asm")):
            if layer_type and layer_type.lower() not in asm_file.stem.lower():
                continue
            try:
                with open(asm_file) as f:
                    code = f.read()
                examples.append({
                    "name": asm_file.stem,
                    "type": "instruction",
                    "code": code,
                    "file_path": str(asm_file),
                })
            except Exception as e:
                continue

    if not examples:
        return {
            "examples": [],
            "count": 0,
            "message": f"No examples found" + (f" for layer_type='{layer_type}'" if layer_type else ""),
        }

    # Return based on mode
    if mode == "one-shot":
        return {"examples": examples[:1], "count": 1}
    else:
        # few-shot: return up to 5 examples
        return {"examples": examples[:5], "count": min(5, len(examples))}


def list_available_examples() -> Dict[str, Any]:
    """List all available example files without loading content."""
    layer_dir = PROJECT_ROOT / "test" / "Layerwise_Benchmark"
    instr_dir = PROJECT_ROOT / "test" / "Instr_Level_Benchmark"

    result = {
        "layerwise": [],
        "instruction": [],
    }

    if layer_dir.exists():
        result["layerwise"] = [f.stem for f in sorted(layer_dir.glob("*.asm"))]

    if instr_dir.exists():
        result["instruction"] = [f.stem for f in sorted(instr_dir.glob("*.asm"))]

    return result
