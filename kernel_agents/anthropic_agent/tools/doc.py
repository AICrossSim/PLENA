"""Tool for retrieving ISA and hardware documentation."""

from typing import Dict, Any, Literal, Optional
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
COMPILER_DOC_PATH = PROJECT_ROOT / "compiler" / "doc"


def get_doc(topic: Optional[Literal["isa", "attention", "memory", "config", "constraints"]] = None) -> Dict[str, Any]:
    """
    Get ISA or hardware documentation.

    Args:
        topic: Documentation topic. One of:
            - 'isa': Full ISA specification (instructions, formats, opcodes)
            - 'attention': Flash attention implementation notes
            - 'memory': Memory layout (HBM, SRAM regions)
            - 'config': Hardware config (MLEN, VLEN, BLEN)
            - 'constraints': Simulator constraints (alignment, valid ranges)
            - None: Return summary of available docs

    Returns:
        Dict with documentation content for requested topic(s)
    """
    if topic is None:
        return _get_doc_summary()

    if topic == "isa":
        return _get_isa_doc()
    elif topic == "attention":
        return _get_attention_doc()
    elif topic == "memory":
        return _get_memory_doc()
    elif topic == "config":
        return _get_config_doc()
    elif topic == "constraints":
        return _get_constraints_doc()
    else:
        return {"error": f"Unknown topic: {topic}. Use 'isa', 'attention', 'memory', 'config', or 'constraints'"}


def _get_doc_summary() -> Dict[str, Any]:
    """Get summary of available documentation."""
    return {
        "available_topics": {
            "isa": "Full ISA specification - all instructions, formats, opcodes",
            "attention": "Flash attention implementation notes and HBM layout",
            "memory": "Memory hierarchy and SRAM layout",
            "config": "Hardware parameters (MLEN, VLEN, BLEN)",
            "constraints": "Simulator constraints - alignment requirements, valid address ranges",
        },
        "quick_reference": {
            "registers": {
                "gp0-gp15": "Integer registers (gp0 = always 0)",
                "f0-f7": "Floating-point scalar registers",
                "a0-a7": "HBM address base registers",
            },
            "key_instructions": {
                "M_MM": "Matrix multiply: Vector_SRAM @ Matrix_SRAM -> Systolic Array",
                "M_MM_WO": "Write out accumulated result to Vector SRAM",
                "H_PREFETCH_M": "Prefetch matrix from HBM to Matrix SRAM",
                "H_PREFETCH_V": "Prefetch vector from HBM to Vector SRAM",
                "V_ADD_VV": "Vector-vector addition",
                "S_ADDI_INT": "Add immediate to integer register",
                "C_LOOP_START/END": "Loop control",
            },
            "hw_config": {"MLEN": 64, "VLEN": 64, "BLEN": 4},
        },
    }


def _get_isa_doc() -> Dict[str, Any]:
    """Get full ISA specification from plena_isa_spec.md."""
    isa_file = COMPILER_DOC_PATH / "plena_isa_spec.md"

    if not isa_file.exists():
        return {"error": f"ISA spec file not found: {isa_file}"}

    with open(isa_file) as f:
        content = f.read()

    return {
        "format": "markdown",
        "content": content,
        "file_path": str(isa_file),
    }


def _get_attention_doc() -> Dict[str, Any]:
    """Get flash attention implementation notes."""
    attn_file = COMPILER_DOC_PATH / "attention_note.md"

    if not attn_file.exists():
        return {"error": f"Attention doc not found: {attn_file}"}

    with open(attn_file) as f:
        content = f.read()

    return {
        "format": "markdown",
        "content": content,
        "file_path": str(attn_file),
    }


def _get_memory_doc() -> Dict[str, Any]:
    """Get memory hierarchy documentation."""
    return {
        "memory_types": {
            "HBM": {
                "description": "High Bandwidth Memory - main off-chip storage",
                "usage": "Stores weights, activations, KV cache",
                "access": "Via H_PREFETCH_M, H_PREFETCH_V, H_STORE_V",
                "addressing": "Base (a0-a7) + offset (gp register)",
            },
            "Matrix_SRAM": {
                "description": "On-chip SRAM for matrix operations",
                "size": "HBM_M_Prefetch_Amount × MLEN entries",
                "usage": "Weight tiles for M_MM, M_TMM",
                "access": "Loaded via H_PREFETCH_M, read by M_MM",
            },
            "Vector_SRAM": {
                "description": "On-chip SRAM for vector/activation data",
                "size": "HBM_V_Prefetch_Amount × VLEN entries",
                "usage": "Activations, intermediate results",
                "access": "H_PREFETCH_V, H_STORE_V, vector ops (V_*)",
            },
            "FP_SRAM": {
                "description": "Scalar floating-point memory",
                "size": "512 entries",
                "access": "S_LD_FP, S_ST_FP, S_MAP_V_FP",
                "usage": "FP constants, softmax accumulators (m, l)",
            },
            "INT_SRAM": {
                "description": "Scalar integer memory",
                "size": "32 entries",
                "access": "S_LD_INT, S_ST_INT",
                "usage": "Loop counters, address offsets",
            },
        },
        "data_layout": {
            "MXFP_format": "Blocks and scales stored separately",
            "matrices": "Row-major, tiled by MLEN × MLEN",
            "vectors": "Contiguous, VLEN elements per access",
            "stride_mode": "Interleaved batches for vectorization",
        },
        "addressing_examples": [
            "C_SET_ADDR_REG a1, gp0, gp1  ; a1 = {gp0, gp1} (concatenated)",
            "H_PREFETCH_M gp2, gp3, a1, 1, 0  ; Matrix_SRAM[gp2] = HBM[a1 + gp3]",
            "C_SET_STRIDE_REG gp4  ; Set stride for strided access",
            "C_SET_SCALE_REG gp5   ; Set scale offset for MXFP",
        ],
    }


def _get_constraints_doc() -> Dict[str, Any]:
    """Get simulator constraints documentation."""
    constraints_file = COMPILER_DOC_PATH / "simulator_constraints.md"

    if not constraints_file.exists():
        return {"error": f"Constraints doc not found: {constraints_file}"}

    with open(constraints_file) as f:
        content = f.read()

    return {
        "format": "markdown",
        "content": content,
        "file_path": str(constraints_file),
    }


def _get_config_doc() -> Dict[str, Any]:
    """Get hardware configuration documentation."""
    # Try to load from plena_settings.toml
    settings_file = PROJECT_ROOT / "src" / "definitions" / "plena_settings.toml"

    hw_params = {}
    if settings_file.exists():
        try:
            import tomllib

            with open(settings_file, "rb") as f:
                hw_params = tomllib.load(f)
        except Exception:
            pass

    return {
        "tile_dimensions": {
            "MLEN": {"value": 64, "description": "Matrix tile dimension (systolic array size)"},
            "VLEN": {"value": 64, "description": "Vector length (elements per vector op)"},
            "BLEN": {"value": 4, "description": "Batch tile size (parallel batches)"},
            "HLEN": {"value": 16, "description": "Head dimension tile for attention"},
        },
        "hbm_prefetch": {
            "HBM_M_Prefetch_Amount": "Number of MLEN rows fetched per H_PREFETCH_M",
            "HBM_V_Prefetch_Amount": "Number of VLEN rows fetched per H_PREFETCH_V",
        },
        "precision": {
            "weights": "MXFP (block floating point) - blocks + scales",
            "activations": "MXFP high precision",
            "kv_cache": "MXFP lower precision",
        },
        "typical_computation": {
            "matmul_tile": "Process (BLEN, MLEN) @ (MLEN, MLEN) -> accumulate in systolic array",
            "writeout": "M_MM_WO writes (BLEN, BLEN) result to Vector SRAM",
        },
        "settings_file": str(settings_file) if settings_file.exists() else None,
        "loaded_params": hw_params if hw_params else "Could not load settings file",
    }
