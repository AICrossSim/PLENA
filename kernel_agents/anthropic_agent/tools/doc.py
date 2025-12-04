"""Tool for retrieving ISA and hardware documentation."""

import sys
from typing import Dict, Any, Literal, Optional
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Add tools to path for imports
sys.path.insert(0, str(PROJECT_ROOT / "tools"))


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
        Dict with documentation content for requested topic(s)
    """
    docs = {}

    if topic in (None, "isa"):
        docs["isa"] = _get_isa_doc()

    if topic in (None, "config"):
        docs["config"] = _get_config_doc()

    if topic in (None, "registers"):
        docs["registers"] = _get_register_doc()

    if topic in (None, "memory"):
        docs["memory"] = _get_memory_doc()

    return docs


def _get_isa_doc() -> Dict[str, Any]:
    """Get ISA opcode documentation."""
    from assembler.parser import load_isa_definitions

    isa_path = PROJECT_ROOT / "src" / "definitions" / "operation.svh"

    try:
        opcodes = load_isa_definitions(str(isa_path))
    except Exception as e:
        opcodes = {"error": str(e)}

    return {
        "opcodes": opcodes,
        "description": "PLENA ISA opcodes with hex values",
        "instruction_categories": {
            "Matrix (M_*)": [
                "M_MM - Matrix multiply",
                "M_TMM - Transposed matrix multiply",
                "M_BMM - Batched matrix multiply",
                "M_MM_WO - Matrix multiply write-out",
                "M_MV - Matrix-vector multiply",
                "M_MV_WO - Matrix-vector write-out",
            ],
            "Vector (V_*)": [
                "V_ADD_VV - Vector-vector add",
                "V_ADD_VF - Vector-scalar add",
                "V_SUB_VV - Vector-vector subtract",
                "V_SUB_VF - Vector-scalar subtract",
                "V_MUL_VV - Vector-vector multiply",
                "V_MUL_VF - Vector-scalar multiply",
                "V_EXP_V - Vector exp",
                "V_RECI_V - Vector reciprocal",
                "V_RED_SUM - Vector reduction sum",
                "V_RED_MAX - Vector reduction max",
            ],
            "Scalar FP (S_*_FP)": [
                "S_ADD_FP - Scalar FP add",
                "S_SUB_FP - Scalar FP subtract",
                "S_MUL_FP - Scalar FP multiply",
                "S_EXP_FP - Scalar FP exp",
                "S_RECI_FP - Scalar FP reciprocal",
                "S_SQRT_FP - Scalar FP sqrt",
                "S_LD_FP - Load FP from SRAM",
                "S_ST_FP - Store FP to SRAM",
                "S_MAP_V_FP - Map scalar to vector",
            ],
            "Scalar INT (S_*_INT)": [
                "S_ADD_INT - Scalar INT add",
                "S_ADDI_INT - Scalar INT add immediate",
                "S_SUB_INT - Scalar INT subtract",
                "S_MUL_INT - Scalar INT multiply",
                "S_LUI_INT - Load upper immediate",
                "S_LD_INT - Load INT from SRAM",
                "S_ST_INT - Store INT to SRAM",
            ],
            "HBM (H_*)": [
                "H_PREFETCH_M - Prefetch matrix from HBM",
                "H_PREFETCH_V - Prefetch vector from HBM",
                "H_STORE_V - Store vector to HBM",
            ],
            "Control (C_*)": [
                "C_SET_ADDR_REG - Set address register",
                "C_SET_SCALE_REG - Set scale register",
                "C_SET_STRIDE_REG - Set stride register",
                "C_BREAK - Break/end execution",
            ],
        },
        "instruction_formats": {
            "R-type (3 registers)": "opcode rd, rs1, rs2",
            "I-type (immediate)": "opcode rd, rs1, imm",
            "HBM-type (5 operands)": "opcode rd, rs1, rs2, rstride, funct1",
        },
    }


def _get_config_doc() -> Dict[str, Any]:
    """Get hardware configuration documentation."""
    from utils.load_config import load_svh_settings

    cfg_path = PROJECT_ROOT / "src" / "definitions" / "configuration.svh"

    try:
        settings = load_svh_settings(str(cfg_path))
    except Exception as e:
        settings = {"error": str(e)}

    return {
        "hardware_params": settings,
        "key_parameters": {
            "MLEN": "Matrix dimension (rows/cols in matrix unit)",
            "VLEN": "Vector length (elements in vector unit)",
            "BLEN": "Batch dimension (parallel batches)",
            "MATRIX_SRAM_DEPTH": "Matrix SRAM depth",
            "VECTOR_SRAM_DEPTH": "Vector SRAM depth",
            "HBM_WIDTH": "HBM bus width in bits",
        },
        "typical_values": {
            "MLEN": 64,
            "VLEN": 64,
            "BLEN": 4,
        },
    }


def _get_register_doc() -> Dict[str, Any]:
    """Get register documentation."""
    return {
        "integer_registers": {
            "gp0": "Zero register (always 0, read-only)",
            "gp1-gp15": "General purpose integer registers",
            "usage": "Used for addresses, loop counters, offsets",
        },
        "fp_registers": {
            "f0-f7": "Floating-point scalar registers",
            "usage": "Used for scalar FP values, constants, accumulators",
        },
        "address_registers": {
            "a0-a7": "HBM address base registers",
            "usage": "Set base addresses for HBM prefetch/store operations",
        },
        "special_registers": {
            "scale_reg": "Matrix scale factor (set via C_SET_SCALE_REG)",
            "stride_reg": "Memory stride (set via C_SET_STRIDE_REG)",
        },
        "examples": [
            "S_ADDI_INT gp1, gp0, 100  ; gp1 = 100",
            "S_LD_FP f1, gp0, 1        ; f1 = FP_SRAM[1]",
            "H_PREFETCH_M gp1, gp2, a0, 1, 0  ; prefetch from HBM[a0 + gp2]",
        ],
    }


def _get_memory_doc() -> Dict[str, Any]:
    """Get memory hierarchy documentation."""
    return {
        "memory_types": {
            "HBM": {
                "description": "High Bandwidth Memory - main off-chip storage",
                "usage": "Stores weights, activations, large tensors",
                "access": "Via H_PREFETCH_M, H_PREFETCH_V, H_STORE_V",
            },
            "Matrix_SRAM": {
                "description": "On-chip SRAM for matrix operations",
                "usage": "Stores weight tiles for matrix multiply",
                "access": "Via H_PREFETCH_M, M_MM reads from here",
            },
            "Vector_SRAM": {
                "description": "On-chip SRAM for vector operations",
                "usage": "Stores activation vectors, intermediate results",
                "access": "Via H_PREFETCH_V, H_STORE_V, vector ops",
            },
            "FP_SRAM": {
                "description": "Scalar floating-point register file",
                "access": "Via S_LD_FP, S_ST_FP",
            },
            "INT_SRAM": {
                "description": "Scalar integer register file",
                "access": "Via S_LD_INT, S_ST_INT",
            },
        },
        "addressing": {
            "on_chip": "Linear addressing within SRAM",
            "hbm": "Base + offset addressing (base in a-reg, offset in gp-reg)",
        },
        "data_layout": {
            "matrices": "Row-major, tiled by MLEN x MLEN",
            "vectors": "Contiguous, VLEN elements per access",
        },
    }
