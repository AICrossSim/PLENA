"""Tool for getting assembly code examples."""

from typing import Literal, List, Dict, Any
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def get_assembly_code_examples(
    mode: Literal["one-shot", "few-shot"] = "one-shot",
    layer_type: str = None,
) -> Dict[str, Any]:
    """
    Get assembly code examples for reference.

    Args:
        mode: 'one-shot' for single example, 'few-shot' for multiple examples
        layer_type: Optional filter for layer type (e.g., 'projection', 'rms', 'attention')

    Returns:
        Dict with:
            - examples: List of assembly code examples
            - count: Number of examples returned
    """
    # TODO: Implement example retrieval
    #
    # Example directories:
    # - test/Instr_Level_Benchmark/*.asm  (instruction-level examples)
    # - test/Layerwise_Benchmark/*.asm    (layer-level examples)
    #
    # Example implementation:
    # instr_dir = PROJECT_ROOT / "test" / "Instr_Level_Benchmark"
    # layer_dir = PROJECT_ROOT / "test" / "Layerwise_Benchmark"
    #
    # examples = []
    # if layer_type:
    #     # Filter by layer type
    #     pattern = f"*{layer_type}*.asm"
    # else:
    #     pattern = "*.asm"
    #
    # for asm_file in layer_dir.glob(pattern):
    #     with open(asm_file) as f:
    #         examples.append({
    #             "name": asm_file.stem,
    #             "code": f.read()
    #         })
    #
    # if mode == "one-shot":
    #     return {"examples": examples[:1], "count": 1}
    # else:
    #     return {"examples": examples[:5], "count": min(5, len(examples))}

    raise NotImplementedError("get_assembly_code_examples not implemented")
