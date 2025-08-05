import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from tools import load_svh_settings

'''
VAddVv { rd: u8, rs1: u8, rs2: u8 },
    VAddVf { rd: u8, rs1: u8, rs2: u8 },
    VSubVv { rd: u8, rs1: u8, rs2: u8 },
    VSubVf { rd: u8, rs1: u8, rs2: u8 },
    VMulVv { rd: u8, rs1: u8, rs2: u8 },
    VMulVf { rd: u8, rs1: u8, rs2: u8 },
    VExpV { rd: u8, rs1: u8 },
    VReciV { rd: u8, rs1: u8, imm: u8 },
    VLdF { rd: u8, rs1: u8, rs2: u8 },
    VRedSum { rd: u8, rs1: u8, imm: u8 },
    VRedMax { rd: u8, rs1: u8, imm: u8 },

    SAddFp { rd: u8, rs1: u8, rs2: u8 },
    SSubFp { rd: u8, rs1: u8, rs2: u8 },
    SMaxFp { rd: u8, rs1: u8, rs2: u8 },
    SMulFp { rd: u8, rs1: u8, rs2: u8 },
    SExpFp { rd: u8, rs1: u8 },
    SReciFp { rd: u8, rs1: u8 },
    SSqrtFp { rd: u8, rs1: u8 },
    SLdFp { rd: u8, rs1: u8, imm: u8 },
    SStFp { rd: u8, rs1: u8, imm: u8 },
    SMapVFp { rd: u8, rs1: u8, imm: u8 },

    SAddInt { rd: u8, rs1: u8, rs2: u8 },
    SAddiInt { rd: u8, rs1: u8, imm: u8 },
    SSubInt { rd: u8, rs1: u8, rs2: u8 },
    SMulInt { rd: u8, rs1: u8, rs2: u8 },
    SLuiInt { rd: u8, imm: u8 },
    SLdInt { rd: u8, rs1: u8, imm: u8 },
    SStInt { rd: u8, rs1: u8, imm: u8 },
'''
OP_TYPE = {
    # Vector operations - vector outputs (2 vector inputs, 1 vector output)
    "VAddVv": "vector",
    "VSubVv": "vector", 
    "VMulVv": "vector",
    
    # Vector + Float operations - vector outputs (1 vector + 1 float input, 1 vector output)
    "VAddVf": "vector",
    "VSubVf": "vector",
    "VMulVf": "vector",
    
    # Single vector operations - vector outputs (1 vector input, 1 vector output)
    "VExpV": "vector",
    "VReciV": "vector",
    
    # Vector operations - scalar outputs (reductions)
    "VRedSum": "vector",
    "VRedMax": "vector",
    
    # Scalar floating point operations (2 float inputs, 1 float output)
    "SAddFp": "scalar",
    "SSubFp": "scalar",
    "SMaxFp": "scalar",
    "SMulFp": "scalar",
    
    # Scalar floating point operations (1 float input, 1 float output)
    "SExpFp": "scalar",
    "SReciFp": "scalar",
    "SSqrtFp": "scalar",
    
    # Scalar floating point load/store/map operations
    "SLdFp": "scalar",
    "SStFp": "scalar",
    "SMapVFp": "scalar",
    
    # Scalar integer operations (2 integer inputs, 1 integer output)
    "SAddInt": "scalar",
    "SSubInt": "scalar", 
    "SMulInt": "scalar",
    
    # Scalar integer operations (1 integer + immediate, 1 integer output)
    "SAddiInt": "scalar",
    
    # Scalar integer operations (immediate only)
    "SLuiInt": "scalar",
    
    # Scalar integer load/store operations
    "SLdInt": "load_scalar_int",
    "SStInt": "store_scalar_int",
}

def _check_op(op_name: str, op_type: str) -> bool:
    """Validate that the operation name and type match according to OP_TYPE dictionary.
    
    Raises:
        ValueError: If op_name is not found in OP_TYPE dictionary
    """
    if op_name not in OP_TYPE:
        raise ValueError(f"Unknown operation name: {op_name}. "
                        f"Available operations: {list(OP_TYPE.keys())}")
    
    expected_type = OP_TYPE[op_name]
    return expected_type == op_type

def _load_hardware_config() -> str:
    """Load hardware config from file."""
    config_dir = Path(__file__).parent.parent / "src/definitions"
    config_path = templates_dir / f"configuration.svh"

    if not template_path.exists():
        raise FileNotFoundError(f"configuration.svh not found in {templates_dir}")

    return load_svh_settings(config_path)

def _generate_vin_vin_vout_op(op_name: str, reg_in_0: str, reg_in_1: str, reg_out: str, loops: int) -> str:
    code = f"""
; {op_name} Op, input_from {reg_in_0}, {reg_in_1}, output_from {reg_out}
"""
    assert reg_in_0.startswith("i")
    assert reg_in_1.startswith("i")
    assert reg_out.startswith("i")
    for i in range(loops):
        code += f"""
{op_name} {reg_out}, {reg_in_0}, {reg_in_1};
SADDI {reg_in_0}, {reg_in_0}, 4;
SADDI {reg_in_1}, {reg_in_1}, 4;
SADDI {reg_out}, {reg_out}, 4;
"""
    return code.strip()

def _generate_vin_fin_vout_op(op_name: str, reg_in_0: str, reg_in_1: str, reg_out: str, loops: int) -> str:
    code = f"""
; {op_name} Op, input_from {reg_in_0}, {reg_in_1}, output_from {reg_out}
"""
    assert reg_in_0.startswith("i")
    assert reg_in_1.startswith("f")
    assert reg_out.startswith("i")
    for i in range(loops):
        code += f"""
{op_name} {reg_out}, {reg_in_0}, {reg_in_1};
SADDI {reg_in_0}, {reg_in_0}, 4;
SADDI {reg_out}, {reg_out}, 4;
"""
    return code.strip()

def _generate_vin_vout_op(op_name: str, reg_in_0: str, reg_out: str, loops: int) -> str:
    code = f"""
; {op_name} Op, input_from {reg_in_0}, output_from {reg_out}
"""
    assert reg_in_0.startswith("i")
    assert reg_out.startswith("i")
    for i in range(loops):
        code += f"""
{op_name} {reg_out}, {reg_in_0};
SADDI {reg_in_0}, {reg_in_0}, 4;
SADDI {reg_out}, {reg_out}, 4;
"""
    return code.strip()

def _generate_vin_reduction_op(op_name: str, reg_in_0: str, reg_out: str, loops: int, imm: int = 0) -> str:
    code = f"""
; {op_name} Op, input_from {reg_in_0}, output_from {reg_out}
"""
    assert reg_in_0.startswith("i")
    assert reg_out.startswith("f")
    for i in range(loops):
        code += f"""
{op_name} {reg_out}, {reg_in_0}, {imm};
SADDI {reg_in_0}, {reg_in_0}, 4;
"""
    return code.strip()

def _generate_vector_op(op_config: Dict[str, Any]) -> str:
    """Generate assembly code for vector operations.
    Args:
        op_config: operation config containing name, registers, and loops
        node: node information
    """
    op_name = op_config.get("name", None)
    reg_in_0 = op_config.get("reg_in_0", None)
    reg_in_1 = op_config.get("reg_in_1", None)
    reg_out = op_config.get("reg_out", None)
    loops = op_config.get("loops", 1)
    if op_name.endswith("Vv"):
        return _generate_vin_vin_vout_op(op_name, reg_in_0, reg_in_1, reg_out, loops)
    elif op_name.endswith("Vf"):
        return _generate_vin_fin_vout_op(op_name, reg_in_0, reg_in_1, reg_out, loops)
    elif op_name.endswith("V"):
        return _generate_vin_vout_op(op_name, reg_in_0, reg_out, loops)
    elif "Red" in op_name:
        return _generate_vin_reduction_op(op_name, reg_in_0, reg_out, loops, op_config.get("imm", 0))
    else:
        raise ValueError(f"Unknown operation name: {op_name}")