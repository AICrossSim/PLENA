"""Tool for retrieving ISA and hardware documentation."""

from typing import Dict, Any, Literal, Optional
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def get_doc(topic: Optional[Literal["isa", "registers", "memory", "config"]] = None) -> Dict[str, Any]:
    """
    Get ISA or hardware documentation.

    Args:
        topic: Documentation topic. One of:
            - 'isa': Instruction set opcodes and formats
            - 'registers': Register descriptions (gp, f, a registers)
            - 'memory': Memory hierarchy (HBM, SRAM, VRAM)
            - 'config': Hardware config (MLEN, VLEN, BLEN)
            - None: Return all documentation

    Returns:
        Dict with documentation content
    """
    # TODO: Implement documentation retrieval
    #
    # Key documentation sources:
    # - src/definitions/operation.svh  (ISA opcodes)
    # - src/definitions/configuration.svh (hardware params)
    # - src/definitions/precision.svh (data type widths)
    #
    # Example implementation:
    # from utils.load_config import load_svh_settings
    # from assembler.parser import load_isa_definitions
    #
    # docs = {}
    #
    # if topic in (None, "isa"):
    #     isa_path = PROJECT_ROOT / "src" / "definitions" / "operation.svh"
    #     docs["isa"] = {
    #         "opcodes": load_isa_definitions(str(isa_path)),
    #         "description": "PLENA ISA opcodes"
    #     }
    #
    # if topic in (None, "config"):
    #     cfg_path = PROJECT_ROOT / "src" / "definitions" / "configuration.svh"
    #     docs["config"] = load_svh_settings(str(cfg_path))
    #
    # if topic in (None, "registers"):
    #     docs["registers"] = {
    #         "gp0-gp15": "General purpose integer registers (gp0 = 0)",
    #         "f0-f7": "Floating-point registers",
    #         "a0-a7": "HBM address registers",
    #     }
    #
    # if topic in (None, "memory"):
    #     docs["memory"] = {
    #         "HBM": "High Bandwidth Memory - main data storage",
    #         "MRAM": "Matrix SRAM - for matrix operations",
    #         "VRAM": "Vector SRAM - for vector operations",
    #     }
    #
    # return docs

    raise NotImplementedError("get_doc not implemented")
