import os
from typing import Dict, List, Any, Optional
from pathlib import Path

def patch_embedding_asm(
    mlen: int,
    blen: int,
    batch: int,
    channels: int,
    image_height: int,
    image_width: int,
    patch_size: int,
    hidden_size: int,
    alive_registers: List[int],
    image_hbm_offset_reg: int,
    weight_hbm_offset_reg: int,
    activation_base_address: int,
    result_base_address: int,
) -> str:
    """
    Generates assembly code for patch embedding.
    Implemented as Conv2d layer, which can be broke down into:
        1. Im2col - Use strided H_PREFETCH_V with loops to extract patches
        2. Systolic GEMM (M_MM) - Reusing pattern from project_asm / batched_matmul_asm
    Returns:
        ???
    """


    pass