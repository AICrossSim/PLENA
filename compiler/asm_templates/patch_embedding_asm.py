import os
from typing import Dict, List, Any, Optional
from pathlib import Path
import math

IMM2_BOUND = 2**18
VLEN = 64  # Vector length - addresses must be multiples of this
PREFETCH_V_AMOUNT = 16  # Number of VLEN-sized chunks per H_PREFETCH_V

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
    Generates assembly code for patch embedding (Conv2d with kernel=stride=patch_size).

    This implements SmolVLM's patch embedding as Im2col + GEMM:
        1. Im2col: Extract non-overlapping patches from image using strided HBM loads
           (B, C, H, W) -> patches loaded into Vector SRAM
        2. GEMM: Matrix multiply patches with projection weights
           (num_patches, C*P*P) @ (C*P*P, hidden_size) -> (num_patches, hidden_size)
    """
    # Compute derived dimensions
    num_patches_h = image_height // patch_size
    num_patches_w = image_width // patch_size
    num_patches = num_patches_h * num_patches_w # H*W
    patch_elements = channels * patch_size * patch_size # C*P*P

    # Image memory layout
    image_channel_stride = image_height * image_width
    image_batch_stride = channels * image_channel_stride

    # Validate dimensions
    assert image_height % patch_size == 0, f"image_height ({image_height}) must be divisible by patch_size ({patch_size})"
    assert image_width % patch_size == 0, f"image_width ({image_width}) must be divisible by patch_size ({patch_size})"
    assert hidden_size % blen == 0, f"hidden_size ({hidden_size}) must be divisible by blen ({blen})"
    assert patch_elements % mlen == 0, f"patch_elements ({patch_elements}) must be divisible by mlen ({mlen})"
    assert hidden_size % mlen == 0, f"hidden_size ({hidden_size}) must be divisible by mlen ({mlen})"
    assert activation_base_address % VLEN == 0, f"activation_base_address must be multiple of VLEN ({VLEN})"
    assert result_base_address % VLEN == 0, f"result_base_address must be multiple of VLEN ({VLEN})"
    assert image_width == VLEN, f"image_width ({image_width}) must equal VLEN ({VLEN}) for efficient im2col"

    generated_code = "; Patch Embedding asm generation \n"
    generated_code += f"; Im2col + GEMM: (B={batch}, C={channels}, H={image_height}, W={image_width}) -> (B={batch}, num_patches={num_patches}, hidden={hidden_size}) \n"
    generated_code += f"; Patch grid: {num_patches_h}x{num_patches_w} = {num_patches} patches, each {patch_elements} elements \n"

    # Register allocation
    patch_addr_reg = alive_registers[0]
    weight_addr_reg = alive_registers[1]
    result_addr_reg = alive_registers[2]
    hbm_offset_reg = alive_registers[3]
    temp_reg = alive_registers[4]
    temp_reg2 = alive_registers[5]

    num_k_tiles = patch_elements // mlen
    num_n_tiles = hidden_size // mlen
    weight_matrix_size = patch_elements * hidden_size

    assert weight_matrix_size < IMM2_BOUND, f"Weight size {weight_matrix_size} exceeds IMM2_BOUND"

    # Phase 1: Setup scale and stride for weight prefetch
    generated_code += f"S_ADDI_INT gp{temp_reg}, gp0, {weight_matrix_size} \n"
    generated_code += f"C_SET_SCALE_REG gp{temp_reg} \n"
    generated_code += f"S_ADDI_INT gp{temp_reg}, gp0, {hidden_size} \n"
    generated_code += f"C_SET_STRIDE_REG gp{temp_reg} \n"

    # Phase 2: Im2col - Extract all patches from images and load into Vector SRAM
    generated_code += "; Phase 2: Im2col - Extract patches from images \n"
    generated_code += f"S_ADDI_INT gp{temp_reg}, gp0, {image_batch_stride * batch} \n"
    generated_code += f"C_SET_SCALE_REG gp{temp_reg} \n"
    generated_code += f"S_ADDI_INT gp{temp_reg}, gp0, {image_width} \n"
    generated_code += f"C_SET_STRIDE_REG gp{temp_reg} \n"

    # Align patch storage to VLEN boundaries
    patch_elements_aligned = ((patch_elements + VLEN - 1) // VLEN) * VLEN
    patches_vram_offset = activation_base_address

    for b in range(batch):
        for ph in range(num_patches_h):
            for pw in range(num_patches_w):
                # Load patch data into Vector SRAM at sequential locations
                generated_code += f"S_ADDI_INT gp{patch_addr_reg}, gp0, {patches_vram_offset} \n"

                for c in range(channels):
                    channel_patch_start = (b * image_batch_stride +
                                          c * image_channel_stride +
                                          ph * patch_size * image_width +
                                          pw * patch_size)

                    rows_to_load = patch_size
                    rows_loaded = 0

                    while rows_loaded < rows_to_load:
                        rows_this_prefetch = min(PREFETCH_V_AMOUNT, rows_to_load - rows_loaded)
                        hbm_offset = channel_patch_start + rows_loaded * image_width

                        generated_code += f"S_ADDI_INT gp{hbm_offset_reg}, gp0, {hbm_offset} \n"
                        generated_code += f"H_PREFETCH_V gp{patch_addr_reg}, gp{hbm_offset_reg}, a{image_hbm_offset_reg}, 1, 0 \n"

                        vram_advance = rows_this_prefetch * VLEN
                        generated_code += f"S_ADDI_INT gp{patch_addr_reg}, gp{patch_addr_reg}, {vram_advance} \n"

                        rows_loaded += rows_this_prefetch

                # Move to next patch location in VRAM (aligned to VLEN)
                patches_vram_offset += patch_elements_aligned

    # Phase 3: GEMM - Matrix multiply patches with projection weights

    return generated_code
