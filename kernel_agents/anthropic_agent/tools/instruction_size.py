"""Tool for getting instruction size/count from assembly code."""

import sys
import tempfile
import os
from typing import Dict, Any
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Add tools to path for imports
sys.path.insert(0, str(PROJECT_ROOT / "tools"))


def get_instruction_size(assembly_code: str) -> Dict[str, Any]:
    """
    Count instructions in assembly code.

    Args:
        assembly_code: PLENA assembly code string

    Returns:
        Dict with:
            - total_instructions: Total instruction count
            - by_type: Dict of instruction counts by opcode type
            - by_category: Dict of counts by instruction category (M, V, S, H, C)
            - lines: Total lines (including comments/blanks)
            - code_lines: Non-empty, non-comment lines
    """
    from assembler.parser import parse_asm_file

    # Write assembly to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.asm', delete=False) as f:
        f.write(assembly_code)
        asm_path = f.name

    try:
        instructions = parse_asm_file(asm_path)

        # Count by opcode type
        by_type = {}
        for instr in instructions:
            opcode = instr.opcode
            by_type[opcode] = by_type.get(opcode, 0) + 1

        # Count by category
        by_category = {
            "Matrix (M_*)": 0,
            "Vector (V_*)": 0,
            "Scalar INT (S_*_INT)": 0,
            "Scalar FP (S_*_FP)": 0,
            "HBM (H_*)": 0,
            "Control (C_*)": 0,
            "Other": 0,
        }

        for instr in instructions:
            opcode = instr.opcode
            if opcode.startswith("M_"):
                by_category["Matrix (M_*)"] += 1
            elif opcode.startswith("V_"):
                by_category["Vector (V_*)"] += 1
            elif opcode.startswith("S_") and "_INT" in opcode:
                by_category["Scalar INT (S_*_INT)"] += 1
            elif opcode.startswith("S_") and "_FP" in opcode:
                by_category["Scalar FP (S_*_FP)"] += 1
            elif opcode.startswith("H_"):
                by_category["HBM (H_*)"] += 1
            elif opcode.startswith("C_"):
                by_category["Control (C_*)"] += 1
            else:
                by_category["Other"] += 1

        # Count lines
        lines = assembly_code.split('\n')
        total_lines = len(lines)
        code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith(';') and not line.strip().startswith('//'))

        return {
            "total_instructions": len(instructions),
            "by_type": by_type,
            "by_category": by_category,
            "lines": total_lines,
            "code_lines": code_lines,
        }

    except Exception as e:
        return {
            "error": str(e),
            "total_instructions": 0,
            "by_type": {},
            "by_category": {},
            "lines": len(assembly_code.split('\n')),
            "code_lines": 0,
        }
    finally:
        # Clean up temp file
        try:
            os.unlink(asm_path)
        except:
            pass
