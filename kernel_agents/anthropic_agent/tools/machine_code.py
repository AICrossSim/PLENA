"""Tool for generating machine code from assembly."""

import sys
import re
from typing import Dict, Any, List
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BUILD_PATH = PROJECT_ROOT / "behavioral_simulator" / "testbench" / "build"

# Add tools to path for imports
sys.path.insert(0, str(PROJECT_ROOT / "tools"))


def _validate_assembly_syntax(assembly_code: str) -> List[str]:
    """
    Pre-validate assembly syntax before assembling.
    Returns list of errors with line numbers.
    """
    errors = []
    lines = assembly_code.strip().split('\n')

    # Valid opcodes (subset - add more as needed)
    valid_opcodes = {
        'S_ADDI_INT', 'S_ADD_INT', 'S_SUB_INT', 'S_MUL_INT', 'S_LUI_INT',
        'S_LD_INT', 'S_ST_INT',
        'S_ADD_FP', 'S_SUB_FP', 'S_MUL_FP', 'S_MAX_FP', 'S_EXP_FP',
        'S_RECI_FP', 'S_SQRT_FP', 'S_LD_FP', 'S_ST_FP', 'S_MAP_V_FP',
        'M_MM', 'M_TMM', 'M_BMM', 'M_BTMM', 'M_MM_WO', 'M_BMM_WO',
        'M_MV', 'M_TMV', 'M_MV_WO',
        'V_ADD_VV', 'V_ADD_VF', 'V_SUB_VV', 'V_SUB_VF', 'V_MUL_VV', 'V_MUL_VF',
        'V_EXP_V', 'V_RECI_V', 'V_RED_SUM', 'V_RED_MAX',
        'H_PREFETCH_M', 'H_PREFETCH_V', 'H_STORE_V',
        'C_SET_ADDR_REG', 'C_SET_SCALE_REG', 'C_SET_STRIDE_REG',
        'C_SET_V_MASK_REG', 'C_LOOP_START', 'C_LOOP_END', 'C_BREAK',
    }

    for line_num, line in enumerate(lines, 1):
        # Remove comments
        line_clean = line.split('//')[0].split(';')[0].strip()
        if not line_clean:
            continue

        parts = line_clean.split()
        if not parts:
            continue

        opcode = parts[0]

        # Check opcode is valid
        if opcode not in valid_opcodes:
            errors.append(f"Line {line_num}: Unknown opcode '{opcode}' in: {line.strip()}")
            continue

        # Get operands
        operand_str = ' '.join(parts[1:])
        operands = [op.strip() for op in operand_str.split(',') if op.strip()]

        # Check register format
        for i, op in enumerate(operands):
            op_clean = op.strip()
            # Skip if it's a number (immediate)
            if re.match(r'^-?\d+$', op_clean):
                continue
            # Check register names
            if not re.match(r'^(gp\d+|f\d+|a\d+)$', op_clean):
                # Could be immediate, check if it looks like garbage
                if not re.match(r'^-?\d+$', op_clean) and not op_clean.startswith(('gp', 'f', 'a')):
                    if ' ' in op_clean or any(c.isalpha() and c not in 'gpfa' for c in op_clean[:2]):
                        errors.append(
                            f"Line {line_num}: Invalid operand '{op_clean}' (operand {i+1}) - "
                            f"expected register (gp0-gp15, f0-f7, a0-a7) or integer. "
                            f"Full line: {line.strip()}"
                        )

    return errors


def machine_code_generation(assembly_code: str) -> Dict[str, Any]:
    """
    Generate machine code from assembly code.

    Only returns syntax errors to Claude (not the binary data).
    Machine code is saved to disk for run_simulator to use.

    Args:
        assembly_code: PLENA assembly code string

    Returns:
        Dict with:
            - success: bool
            - instruction_count: Number of instructions (if successful)
            - machine_code_path: Path to .mem file (if successful)
            - syntax_errors: List of instruction-level syntax errors with line numbers
    """
    from assembler.assembly_to_binary import AssemblyToBinary

    BUILD_PATH.mkdir(parents=True, exist_ok=True)
    asm_path = BUILD_PATH / "generated_asm_code.asm"
    mem_path = BUILD_PATH / "generated_machine_code.mem"

    # Write assembly to file
    with open(asm_path, "w") as f:
        f.write(assembly_code)

    # Pre-validate syntax
    syntax_errors = _validate_assembly_syntax(assembly_code)
    if syntax_errors:
        return {
            "success": False,
            "instruction_count": 0,
            "machine_code_path": None,
            "syntax_errors": syntax_errors
        }

    try:
        isa_path = PROJECT_ROOT / "src" / "definitions" / "operation.svh"
        cfg_path = PROJECT_ROOT / "src" / "definitions" / "configuration.svh"

        assembler = AssemblyToBinary(str(isa_path), str(cfg_path))

        # Parse instructions first to enable line-by-line error tracking
        from assembler.parser import parse_asm_file
        instructions = parse_asm_file(str(asm_path))

        # Map parsed instructions back to source lines for error reporting
        source_lines = assembly_code.strip().split('\n')
        instr_to_line = []
        instr_idx = 0
        for line_num, line in enumerate(source_lines, 1):
            line_clean = line.split('//')[0].split(';')[0].strip()
            if line_clean and not line_clean.startswith(';'):
                parts = line_clean.split()
                if parts and parts[0] in {
                    'S_ADDI_INT', 'S_ADD_INT', 'S_SUB_INT', 'S_MUL_INT', 'S_LUI_INT',
                    'S_LD_INT', 'S_ST_INT', 'S_ADD_FP', 'S_SUB_FP', 'S_MUL_FP',
                    'S_MAX_FP', 'S_EXP_FP', 'S_RECI_FP', 'S_SQRT_FP', 'S_LD_FP',
                    'S_ST_FP', 'S_MAP_V_FP', 'M_MM', 'M_TMM', 'M_BMM', 'M_BTMM',
                    'M_MM_WO', 'M_BMM_WO', 'M_MV', 'M_TMV', 'M_MV_WO',
                    'V_ADD_VV', 'V_ADD_VF', 'V_SUB_VV', 'V_SUB_VF', 'V_MUL_VV',
                    'V_MUL_VF', 'V_EXP_V', 'V_RECI_V', 'V_RED_SUM', 'V_RED_MAX',
                    'H_PREFETCH_M', 'H_PREFETCH_V', 'H_STORE_V',
                    'C_SET_ADDR_REG', 'C_SET_SCALE_REG', 'C_SET_STRIDE_REG',
                    'C_SET_V_MASK_REG', 'C_LOOP_START', 'C_LOOP_END', 'C_BREAK',
                }:
                    instr_to_line.append((line_num, line.strip()))

        # Try to convert each instruction, catching errors with line info
        binary_instructions = []
        for idx, instr in enumerate(instructions):
            try:
                binary_instruction = assembler._convert_to_binary(instr)
                binary_instructions.append(binary_instruction)
            except TypeError as e:
                # This catches "unsupported operand type(s) for <<: 'NoneType' and 'int'"
                if idx < len(instr_to_line):
                    line_num, line_text = instr_to_line[idx]
                    # Analyze which operand is None
                    missing = []
                    if instr.rd is None: missing.append('rd')
                    if instr.rs1 is None and instr.opcode not in ['C_SET_SCALE_REG', 'C_SET_STRIDE_REG', 'C_SET_V_MASK_REG', 'C_LOOP_END', 'S_LUI_INT', 'C_LOOP_START']:
                        missing.append('rs1')
                    if instr.imm is None and instr.opcode in ['S_ADDI_INT', 'S_LUI_INT', 'C_LOOP_START']:
                        missing.append('imm')
                    if instr.rstride is None and instr.opcode in ['H_PREFETCH_M', 'H_PREFETCH_V', 'H_STORE_V']:
                        missing.append('rstride')
                    if instr.funct1 is None and instr.opcode in ['H_PREFETCH_M', 'H_PREFETCH_V', 'H_STORE_V']:
                        missing.append('funct1')

                    error_detail = f"missing operand(s): {', '.join(missing)}" if missing else str(e)
                    return {
                        "success": False,
                        "instruction_count": 0,
                        "machine_code_path": None,
                        "syntax_errors": [f"Line {line_num}: {error_detail} in: {line_text}"]
                    }
                raise

        # Write binary to file
        assembler.write_binary_to_file(binary_instructions, str(mem_path))

        return {
            "success": True,
            "instruction_count": len(binary_instructions),
            "machine_code_path": str(mem_path),
            "syntax_errors": []
        }
    except KeyError as e:
        # Try to find the line with the unknown opcode
        opcode = str(e).strip("'\"")
        lines = assembly_code.strip().split('\n')
        for line_num, line in enumerate(lines, 1):
            if opcode in line:
                return {
                    "success": False,
                    "instruction_count": 0,
                    "machine_code_path": None,
                    "syntax_errors": [f"Line {line_num}: Unknown opcode '{opcode}' in: {line.strip()}"]
                }
        return {
            "success": False,
            "instruction_count": 0,
            "machine_code_path": None,
            "syntax_errors": [f"Unknown opcode: {e}"]
        }
    except Exception as e:
        # Try to extract line info from error message
        error_str = str(e)
        lines = assembly_code.strip().split('\n')

        # Search for problematic content in the error
        for line_num, line in enumerate(lines, 1):
            line_clean = line.split('//')[0].split(';')[0].strip()
            if line_clean and any(part in error_str for part in line_clean.split()):
                return {
                    "success": False,
                    "instruction_count": 0,
                    "machine_code_path": None,
                    "syntax_errors": [f"Line {line_num}: {error_str} in: {line.strip()}"]
                }

        return {
            "success": False,
            "instruction_count": 0,
            "machine_code_path": None,
            "syntax_errors": [error_str]
        }
