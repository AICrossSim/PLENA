"""Tool for getting instruction size/count from assembly code."""

from typing import Dict, Any
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def get_instruction_size(assembly_code: str) -> Dict[str, Any]:
    """
    Count instructions in assembly code.

    Args:
        assembly_code: PLENA assembly code string

    Returns:
        Dict with:
            - total_instructions: Total instruction count
            - by_type: Dict of instruction counts by opcode type
            - lines: Total lines (including comments/blanks)
    """
    # TODO: Implement instruction counting
    #
    # Uses: tools/assembler/parser.py
    #
    # Example implementation:
    # import tempfile
    # from assembler.parser import parse_asm_file
    #
    # with tempfile.NamedTemporaryFile(mode='w', suffix='.asm', delete=False) as f:
    #     f.write(assembly_code)
    #     asm_path = f.name
    #
    # instructions = parse_asm_file(asm_path)
    #
    # by_type = {}
    # for instr in instructions:
    #     opcode = instr.opcode
    #     by_type[opcode] = by_type.get(opcode, 0) + 1
    #
    # return {
    #     "total_instructions": len(instructions),
    #     "by_type": by_type,
    #     "lines": len(assembly_code.strip().split('\n'))
    # }

    raise NotImplementedError("get_instruction_size not implemented")
