"""
Utility functions for parsing system design space TOML files.
"""

import toml
from dataclasses import dataclass
from typing import List, Optional, Union, Dict, Any


@dataclass
class ComputeConfig:
    """Configuration for compute-related parameters."""
    core_num: int
    core_num_range: List[int]
    blen: int
    blen_range: List[int]
    mlen: int
    mlen_range: List[int]
    vlen: int
    vlen_range: List[int]


@dataclass
class MemorySpec:
    """Specification for a memory type."""
    capacity_default: Optional[int] = None
    capacity_range: Optional[List[int]] = None
    bandwidth_default: Optional[int] = None
    bandwidth_range: Optional[List[int]] = None
    cost: Optional[int] = None
    power: Optional[int] = None


@dataclass
class MemoryTypeConfig:
    """Configuration for a memory type selection."""
    type: Optional[str] = None
    default: Optional[str] = None
    range: Optional[List[str]] = None


@dataclass
class MatrixSRAMConfig:
    """Configuration for Matrix SRAM."""
    type: MemoryTypeConfig
    sram: Optional[MemorySpec] = None
    stacked_3d: Optional[MemorySpec] = None  # 3D_STACKED


@dataclass
class VectorSRAMConfig:
    """Configuration for Vector SRAM."""
    type: MemoryTypeConfig
    sram: Optional[MemorySpec] = None


@dataclass
class OffChipStorageConfig:
    """Configuration for off-chip storage."""
    type: MemoryTypeConfig
    hbm: Optional[MemorySpec] = None
    ddr: Optional[MemorySpec] = None


@dataclass
class MemoryConfig:
    """Configuration for all memory-related parameters."""
    matrix_sram: MatrixSRAMConfig
    vector_sram: VectorSRAMConfig
    off_chip_storage: OffChipStorageConfig


@dataclass
class DataTypeConfig:
    """Configuration for a data type."""
    type: str
    sign: bool
    exponent: int
    mantissa: int


@dataclass
class PrecisionTypeConfig:
    """Configuration for a precision type."""
    format: Optional[str] = None
    block: Optional[int] = None
    type: Optional[str] = None
    sign: Optional[bool] = None
    exponent: Optional[int] = None
    mantissa: Optional[int] = None
    data_type: Optional[DataTypeConfig] = None
    elem: Optional[DataTypeConfig] = None
    scale: Optional[DataTypeConfig] = None


@dataclass
class PrecisionConfig:
    """Configuration for all precision-related parameters."""
    matrix_sram_type: PrecisionTypeConfig
    vector_sram_type: PrecisionTypeConfig
    offchip_m_weight_type: PrecisionTypeConfig
    offchip_m_kv_type: PrecisionTypeConfig
    offchip_v_act_type: PrecisionTypeConfig
    offchip_v_kv_type: PrecisionTypeConfig
    scalar_fp: PrecisionTypeConfig


@dataclass
class FFNConfig:
    """Configuration for FFN execution."""
    execution_order: Dict[str, Any]
    on_chip_storage_priority: Dict[str, Any]


@dataclass
class FlashAttentionConfig:
    """Configuration for Flash Attention."""
    execution_order: Dict[str, Any]
    soft_tiling_size: Dict[str, Any]
    on_chip_storage_priority: Dict[str, Any]


def parse_toml_file(file_path: str) -> Dict[str, Any]:
    """
    Parse a TOML design space file and return a hierarchical dictionary
    with class-based configurations.
    
    Args:
        file_path: Path to the TOML file
        
    Returns:
        Dictionary with 'compute', 'memory', 'precision', 'ffn', and 
        'flash_attention' keys containing class instances
    """
    with open(file_path, 'r') as f:
        data = toml.load(f)
    
    # Parse COMPUTE section
    compute_config = ComputeConfig(
        core_num=data.get('COMPUT', {}).get('CORE_NUM', {}).get('default', 1),
        core_num_range=data.get('COMPUT', {}).get('CORE_NUM', {}).get('range', []),
        blen=data.get('COMPUTE', {}).get('BLEN', {}).get('default', 4),
        blen_range=data.get('COMPUTE', {}).get('BLEN', {}).get('range', []),
        mlen=data.get('COMPUTE', {}).get('MLEN', {}).get('default', 64),
        mlen_range=data.get('COMPUTE', {}).get('MLEN', {}).get('range', []),
        vlen=data.get('COMPUTE', {}).get('VLEN', {}).get('default', 64),
        vlen_range=data.get('COMPUTE', {}).get('VLEN', {}).get('range', []),
    )
    
    # Parse MEMORY section
    memory_data = data.get('MEMORY', {})
    
    # Matrix SRAM
    matrix_sram_data = memory_data.get('MATRIX_SRAM', {})
    matrix_sram_type = MemoryTypeConfig(
        type=matrix_sram_data.get('TYPE', {}).get('type'),
        range=matrix_sram_data.get('TYPE', {}).get('range', [])
    )
    
    matrix_sram_spec = None
    if 'SRAM' in matrix_sram_data:
        sram_data = matrix_sram_data['SRAM']
        matrix_sram_spec = MemorySpec(
            capacity_default=sram_data.get('capacity_default'),
            capacity_range=sram_data.get('capacity_range'),
            bandwidth_default=sram_data.get('bandwidth_default'),
            bandwidth_range=sram_data.get('bandwidth_range'),
            cost=sram_data.get('cost'),
            power=sram_data.get('power')
        )
    
    matrix_sram_3d = None
    if '3D_STACKED' in matrix_sram_data:
        stacked_data = matrix_sram_data['3D_STACKED']
        matrix_sram_3d = MemorySpec(
            capacity_default=stacked_data.get('capacity_default'),
            capacity_range=stacked_data.get('capacity_range'),
            bandwidth_default=stacked_data.get('bandwidth_default'),
            bandwidth_range=stacked_data.get('bandwidth_range'),
            cost=stacked_data.get('cost'),
            power=stacked_data.get('power')
        )
    
    matrix_sram_config = MatrixSRAMConfig(
        type=matrix_sram_type,
        sram=matrix_sram_spec,
        stacked_3d=matrix_sram_3d
    )
    
    # Vector SRAM
    vector_sram_data = memory_data.get('VECTOR_SRAM', {})
    vector_sram_type = MemoryTypeConfig(
        default=vector_sram_data.get('TYPE', {}).get('default'),
        range=vector_sram_data.get('TYPE', {}).get('range', [])
    )
    
    vector_sram_spec = None
    if 'SRAM' in vector_sram_data:
        sram_data = vector_sram_data['SRAM']
        vector_sram_spec = MemorySpec(
            capacity_default=sram_data.get('capacity_default'),
            capacity_range=sram_data.get('capacity_range'),
            bandwidth_default=sram_data.get('bandwidth_default'),
            bandwidth_range=sram_data.get('bandwidth_range'),
            cost=sram_data.get('cost'),
            power=sram_data.get('power')
        )
    
    vector_sram_config = VectorSRAMConfig(
        type=vector_sram_type,
        sram=vector_sram_spec
    )
    
    # Off-chip Storage
    offchip_data = data.get('OFF_CHIP_STORAGE', {})
    offchip_type = MemoryTypeConfig(
        type=offchip_data.get('TYPE', {}).get('type'),
        range=offchip_data.get('TYPE', {}).get('range', [])
    )
    
    hbm_spec = None
    if 'HBM' in offchip_data:
        hbm_data = offchip_data['HBM']
        hbm_spec = MemorySpec(
            capacity_default=hbm_data.get('capacity_default'),
            capacity_range=hbm_data.get('capacity_range'),
            bandwidth_default=hbm_data.get('bandwidth_default'),
            bandwidth_range=hbm_data.get('bandwidth_range'),
            cost=hbm_data.get('cost'),
            power=hbm_data.get('power')
        )
    
    ddr_spec = None
    if 'DDR' in offchip_data:
        ddr_data = offchip_data['DDR']
        ddr_spec = MemorySpec(
            capacity_default=ddr_data.get('capacity_default'),
            capacity_range=ddr_data.get('capacity_range'),
            bandwidth_default=ddr_data.get('bandwidth_default'),
            bandwidth_range=ddr_data.get('bandwidth_range'),
            cost=ddr_data.get('cost'),
            power=ddr_data.get('power')
        )
    
    offchip_config = OffChipStorageConfig(
        type=offchip_type,
        hbm=hbm_spec,
        ddr=ddr_spec
    )
    
    memory_config = MemoryConfig(
        matrix_sram=matrix_sram_config,
        vector_sram=vector_sram_config,
        off_chip_storage=offchip_config
    )
    
    # Parse PRECISION section
    precision_data = data.get('PRECISION', {})
    
    def parse_precision_type(key: str) -> PrecisionTypeConfig:
        """Helper to parse a precision type configuration."""
        prec_data = precision_data.get(key, {})
        
        # Check for nested DATA_TYPE, ELEM, or SCALE
        data_type_config = None
        if 'DATA_TYPE' in prec_data:
            dt_data = prec_data['DATA_TYPE']
            data_type_config = DataTypeConfig(
                type=dt_data.get('type'),
                sign=dt_data.get('sign'),
                exponent=dt_data.get('exponent'),
                mantissa=dt_data.get('mantissa')
            )
        
        elem_config = None
        if 'ELEM' in prec_data:
            elem_data = prec_data['ELEM']
            elem_config = DataTypeConfig(
                type=elem_data.get('type'),
                sign=elem_data.get('sign'),
                exponent=elem_data.get('exponent'),
                mantissa=elem_data.get('mantissa')
            )
        
        scale_config = None
        if 'SCALE' in prec_data:
            scale_data = prec_data['SCALE']
            scale_config = DataTypeConfig(
                type=scale_data.get('type'),
                sign=scale_data.get('sign'),
                exponent=scale_data.get('exponent'),
                mantissa=scale_data.get('mantissa')
            )
        
        return PrecisionTypeConfig(
            format=prec_data.get('format'),
            block=prec_data.get('block'),
            type=prec_data.get('type'),
            sign=prec_data.get('sign'),
            exponent=prec_data.get('exponent'),
            mantissa=prec_data.get('mantissa'),
            data_type=data_type_config,
            elem=elem_config,
            scale=scale_config
        )
    
    precision_config = PrecisionConfig(
        matrix_sram_type=parse_precision_type('MATRIX_SRAM_TYPE'),
        vector_sram_type=parse_precision_type('VECTOR_SRAM_TYPE'),
        offchip_m_weight_type=parse_precision_type('OFFCHIP_M_WEIGHT_TYPE'),
        offchip_m_kv_type=parse_precision_type('OFFCHIP_M_KV_TYPE'),
        offchip_v_act_type=parse_precision_type('OFFCHIP_V_ACT_TYPE'),
        offchip_v_kv_type=parse_precision_type('OFFCHIP_V_KV_TYPE'),
        scalar_fp=parse_precision_type('SCALAR_FP')
    )
    
    # Parse FFN section
    ffn_data = data.get('FFN', {})
    ffn_config = FFNConfig(
        execution_order=ffn_data.get('EXECUTION_ORDER', {}),
        on_chip_storage_priority=ffn_data.get('ON_CHIP_STORAGE_PRIORITY', {})
    )
    
    # Parse FLASH_ATTENTION section
    flash_attn_data = data.get('FLASH_ATTENTION', {})
    flash_attn_config = FlashAttentionConfig(
        execution_order=flash_attn_data.get('EXECUTION_ORDER', {}),
        soft_tiling_size=flash_attn_data.get('SOFT_TILING_SIZE', {}),
        on_chip_storage_priority=flash_attn_data.get('ON_CHIP_STORAGE_PRIORITY', {})
    )
    
    return {
        'compute': compute_config,
        'memory': memory_config,
        'precision': precision_config,
        'ffn': ffn_config,
        'flash_attention': flash_attn_config
    }



if __name__ == "__main__":
    config = parse_toml_file("plena_sys_design_space.toml")
    print(config)