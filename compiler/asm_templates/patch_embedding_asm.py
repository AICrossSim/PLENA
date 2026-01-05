import os
from typing import Dict, List, Any, Optional
from pathlib import Path
import math

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
    Implemented as Conv2d layer (kernel_size=patch_size, stride=patch_size), which decomposes into:
        1. Im2col - Use H_PREFETCH_V to extract non-overlapping patches from image
        2. Systolic GEMM - Matrix multiply patches with projection weights
        3. Optional: Add position embeddings (handled separately via elementwise_add_asm)

    Args:
        mlen: Matrix tile size (e.g., 64)
        blen: Batch tile size (e.g., 4)
        batch: Batch size
        channels: Input image channels (e.g., 3 for RGB)
        image_height: Image height in pixels
        image_width: Image width in pixels
        patch_size: Patch size (e.g., 16 for 16x16 patches)
        hidden_size: Output embedding dimension
        alive_registers: Available general-purpose registers
        image_hbm_offset_reg: HBM address register for image data (a0-a7)
        weight_hbm_offset_reg: HBM address register for projection weights (a0-a7)
        activation_base_address: Base address in Vector SRAM for intermediate patches
        result_base_address: Base address in Vector SRAM for output embeddings

    Returns:
        str: Generated assembly code for patch embedding

    Memory Layout:
        - Input (HBM): Image data (B, C, H, W) stored in channel-first format
        - Weights (HBM): Projection matrix (C*P*P, hidden_size) in column-major
        - Intermediate (Vector SRAM): Im2col patches (num_patches, C*P*P)
        - Output (Vector SRAM): Embedded patches (num_patches, hidden_size)
    """
    generated_code = "; Patch Embedding Assembly Generation\n"

    # Calculate dimensions
    num_patches_h = image_height // patch_size
    num_patches_w = image_width // patch_size
    num_patches = num_patches_h * num_patches_w
    patch_elements = channels * patch_size * patch_size

    # Validate dimensions
    assert image_height % patch_size == 0, "image_height must be divisible by patch_size"
    assert image_width % patch_size == 0, "image_width must be divisible by patch_size"
    assert patch_elements % mlen == 0, f"patch_elements ({patch_elements}) must be divisible by mlen ({mlen})"
    assert hidden_size % blen == 0, f"hidden_size ({hidden_size}) must be divisible by blen ({blen})"

    generated_code += f"; Image: ({batch}, {channels}, {image_height}, {image_width}) -> Patches: ({batch}, {num_patches}, {patch_elements})\n"
    generated_code += f"; GEMM: ({num_patches}, {patch_elements}) @ ({patch_elements}, {hidden_size}) -> ({num_patches}, {hidden_size})\n"

    # Assign registers
    # For im2col phase
    img_offset_reg = alive_registers[0]      # Current HBM offset for image data
    patch_vram_reg = alive_registers[1]      # Current Vector SRAM address for patches
    patch_row_reg = alive_registers[2]       # Current patch row index
    patch_col_reg = alive_registers[3]       # Current patch col index

    # For GEMM phase
    weight_reg = alive_registers[4]          # Weight matrix offset
    act_reg = alive_registers[5]             # Activation offset
    result_reg = alive_registers[6]          # Result offset
    temp_reg = alive_registers[7]            # Temporary calculations

    # ===== STEP 1: Im2col - Extract patches from image =====
    generated_code += "\n; === Im2col Phase: Extract patches ===\n"

    # For simplicity, we'll implement a basic version that extracts patches sequentially
    # More optimized version would use strided loads and hardware loops

    # Initialize patch VRAM destination
    generated_code += f"S_ADDI_INT gp{patch_vram_reg}, gp0, {activation_base_address} \n"

    # Loop over batches
    for b in range(batch):
        batch_image_offset = b * channels * image_height * image_width

        # Loop over patches in the image
        for patch_row in range(num_patches_h):
            for patch_col in range(num_patches_w):
                patch_idx = patch_row * num_patches_w + patch_col

                # Calculate starting position of this patch in the image
                # For channel-first format: offset = batch_offset + channel*H*W + row*W + col
                patch_start_row = patch_row * patch_size
                patch_start_col = patch_col * patch_size

                # Extract patch for each channel
                for c in range(channels):
                    channel_offset = batch_image_offset + c * image_height * image_width

                    # Extract patch_size x patch_size patch using row-by-row loads
                    for p_row in range(patch_size):
                        # Calculate HBM offset for this row of the patch
                        row_offset = channel_offset + (patch_start_row + p_row) * image_width + patch_start_col

                        # Load one row of the patch (patch_size elements)
                        generated_code += f"S_ADDI_INT gp{img_offset_reg}, gp0, {row_offset} \n"

                        # H_PREFETCH_V loads data from HBM to Vector SRAM
                        # Note: This assumes patch_size <= vlen (typically 64)
                        # For patch_size=16, this loads 16 elements
                        generated_code += f"H_PREFETCH_V gp{patch_vram_reg}, gp{img_offset_reg}, a{image_hbm_offset_reg}, 0, 0 \n"

                        # Advance Vector SRAM pointer by patch_size elements
                        generated_code += f"S_ADDI_INT gp{patch_vram_reg}, gp{patch_vram_reg}, {patch_size} \n"

    # ===== STEP 2: Systolic GEMM - Project patches to hidden_size =====
    generated_code += "\n; === GEMM Phase: Project patches ===\n"

    # Configure scale and stride for weight matrix
    # Weight matrix shape: (patch_elements, hidden_size)
    # Stored in column-major format for our systolic array
    weight_scale = patch_elements * hidden_size

    # GEMM dimensions:
    # Activation: (num_patches, patch_elements)
    # Weight: (patch_elements, hidden_size)
    # Result: (num_patches, hidden_size)

    num_weight_tiles_k = patch_elements // mlen  # Number of tiles along K dimension
    num_output_tiles_n = hidden_size // blen     # Number of tiles along N (output) dimension
    num_patch_tiles_m = math.ceil(num_patches / blen)  # Number of tiles along M (patches) dimension

    generated_code += f"; GEMM tiling: M={num_patch_tiles_m} tiles, K={num_weight_tiles_k} tiles, N={num_output_tiles_n} tiles\n"

    # Initialize result register
    generated_code += f"S_ADDI_INT gp{result_reg}, gp0, {result_base_address} \n"

    # Outer loop: iterate over output columns (N dimension)
    for n_tile in range(num_output_tiles_n):
        # Prefetch weight tiles for this output block
        # Weights for columns [n_tile*blen : (n_tile+1)*blen]
        generated_code += f"\n; Load weights for output columns {n_tile*blen} to {(n_tile+1)*blen}\n"

        for k_tile in range(num_weight_tiles_k):
            # Weight offset: We need columns [n_tile*blen : (n_tile+1)*blen]
            # and rows [k_tile*mlen : (k_tile+1)*mlen]
            # In column-major: offset = n_tile * blen * patch_elements + k_tile * mlen
            weight_hbm_offset = n_tile * blen * patch_elements + k_tile * mlen

            # Matrix SRAM destination: k_tile * mlen * blen (must be aligned)
            mram_dest_addr = k_tile * mlen * blen

            # Set Matrix SRAM destination address
            generated_code += f"S_ADDI_INT gp{temp_reg}, gp0, {mram_dest_addr} \n"
            # Set HBM offset
            generated_code += f"S_ADDI_INT gp{weight_reg}, gp0, {weight_hbm_offset} \n"
            # Load weight tile from HBM to Matrix SRAM
            generated_code += f"H_PREFETCH_M gp{temp_reg}, gp{weight_reg}, a{weight_hbm_offset_reg}, 0, 0 \n"

        # Middle loop: iterate over patches (M dimension)
        for m_tile in range(num_patch_tiles_m):
            # Inner loop: accumulate over K dimension
            for k_tile in range(num_weight_tiles_k):
                # Activation offset in Vector SRAM
                # Patches [m_tile*blen : (m_tile+1)*blen], elements [k_tile*mlen : (k_tile+1)*mlen]
                act_offset = activation_base_address + m_tile * blen * patch_elements + k_tile * mlen

                # Weight offset in Matrix SRAM
                weight_offset_mram = k_tile * mlen * blen

                # M_MM: Accumulate Act @ Weight into systolic array
                generated_code += f"S_ADDI_INT gp{act_reg}, gp0, {act_offset} \n"
                generated_code += f"S_ADDI_INT gp{weight_reg}, gp0, {weight_offset_mram} \n"
                generated_code += f"M_MM 0, gp{weight_reg}, gp{act_reg} \n"

            # Write accumulated result from systolic array to Vector SRAM
            # Result for patches [m_tile*blen : (m_tile+1)*blen],
            # output dimensions [n_tile*blen : (n_tile+1)*blen]
            result_offset = result_base_address + m_tile * blen * hidden_size + n_tile * blen

            generated_code += f"S_ADDI_INT gp{result_reg}, gp0, {result_offset} \n"
            generated_code += f"M_MM_WO gp{result_reg}, 0, 0 \n"

    generated_code += "\n; Patch Embedding complete\n"
    return generated_code
