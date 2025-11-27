import os
from typing import Dict, List, Any, Optional
from pathlib import Path

def patch_embedding_asm(
    patch_size: int,
    num_patches: int,
    hidden_size: int,
    img_height: int,
    img_width: int,
    in_channels: int,
    alive_registers: List[int],
    mlen: int,
    blen: int,
    weight_base_hbm_offset_reg: int,
    img_base_address: int,
    result_base_address: int,
) -> str:
    """
    Generates assembly code for patch embedding operation.

    Converts an image into patch embeddings by:
    1. Dividing the image into patches of size (patch_size x patch_size)
    2. Flattening each patch: (in_channels, patch_size, patch_size) -> (patch_embed_dim,)
    3. Projecting through weight matrix: (patch_embed_dim,) @ (patch_embed_dim, hidden_size) -> (hidden_size,)

    Args:
        patch_size: Size of each square patch (e.g., 16 for 16x16 patches)
        num_patches: Total number of patches (img_height/patch_size * img_width/patch_size)
        hidden_size: Output embedding dimension
        img_height: Height of input image
        img_width: Width of input image
        in_channels: Number of input channels (e.g., 3 for RGB)
        alive_registers: List of available general-purpose registers
        mlen: Matrix dimension parameter for tiling
        blen: Batch dimension parameter for tiling
        weight_base_hbm_offset_reg: Address register index for projection weight matrix
        img_base_address: Base address of input image data
        result_base_address: Base address to write patch embeddings

    Returns:
        str: Generated assembly code for patch embedding operation
    """

    generated_code = "; Patch Embedding ASM Generation \n"

    # Calculate patch embedding dimension (flattened patch size)
    patch_embed_dim = patch_size * patch_size * in_channels

    # Validate dimensions
    assert img_height % patch_size == 0, f"Image height {img_height} must be divisible by patch_size {patch_size}"
    assert img_width % patch_size == 0, f"Image width {img_width} must be divisible by patch_size {patch_size}"
    assert (img_height // patch_size) * (img_width // patch_size) == num_patches, \
        f"num_patches {num_patches} must equal (img_height//patch_size) * (img_width//patch_size)"
    assert hidden_size % mlen == 0, f"hidden_size {hidden_size} must be divisible by mlen {mlen}"
    assert patch_embed_dim % mlen == 0, f"patch_embed_dim {patch_embed_dim} must be divisible by mlen {mlen}"

    # Assign registers
    img_addr_register = alive_registers[0]
    w_actual_register = alive_registers[1]
    w_hbm_offset_register = alive_registers[2]
    result_register = alive_registers[3]

    # Set scale and stride for weight matrix access
    # Weight matrix shape: (hidden_size, patch_embed_dim)
    scale_value = hidden_size * patch_embed_dim
    stride_value = patch_embed_dim
    assert scale_value % 64 == 0, f"Weight matrix scale {scale_value} must be a multiple of 64 for HBM alignment"
    assert stride_value % 64 == 0, f"Weight matrix stride {stride_value} must be a multiple of 64 for HBM alignment"
    generated_code += f"S_ADDI_INT gp{w_hbm_offset_register}, gp0, {scale_value} \n"
    generated_code += f"C_SET_SCALE_REG gp{w_hbm_offset_register} \n"
    generated_code += f"S_ADDI_INT gp{w_hbm_offset_register}, gp0, {stride_value} \n"
    generated_code += f"C_SET_STRIDE_REG gp{w_hbm_offset_register} \n"

    # Initialize registers
    generated_code += f"S_ADDI_INT gp{img_addr_register}, gp0, {img_base_address} \n"
    generated_code += f"S_ADDI_INT gp{result_register}, gp0, {result_base_address} \n"

    # Process each patch
    patches_per_row = img_width // patch_size

    for patch_idx in range(num_patches):
        # Calculate patch position
        patch_row = patch_idx // patches_per_row
        patch_col = patch_idx % patches_per_row

        # Calculate starting address for this patch in the image
        # Image layout: (in_channels, img_height, img_width)
        patch_start_offset = (patch_row * patch_size * img_width + patch_col * patch_size) * in_channels

        # Load patch data into on-chip memory (vector SRAM)
        # The patch is flattened: (in_channels, patch_size, patch_size) -> (patch_embed_dim,)
        # Note: Patches are not contiguous in memory due to 2D layout

        # Prefetch patch data into vector memory
        # Use aligned HBM addresses (round down to 64-byte boundary)
        v_on_chip_addr = 0
        for i in range(patch_embed_dim // mlen):
            # Calculate offset within the patch considering the 2D layout
            row_within_patch = (i * mlen) // (patch_size * in_channels)
            offset_in_img = row_within_patch * img_width * in_channels
            col_offset = (i * mlen) % (patch_size * in_channels)

            # Calculate actual HBM offset
            hbm_offset = patch_start_offset + offset_in_img + col_offset

            # Verify alignment
            assert hbm_offset % 64 == 0, f"HBM offset {hbm_offset} must be 64-byte aligned. Check that img_width * in_channels is a multiple of 64."

            generated_code += f"S_ADDI_INT gp{img_addr_register}, gp0, {v_on_chip_addr} \n"
            generated_code += f"S_ADDI_INT gp{w_hbm_offset_register}, gp0, {hbm_offset} \n"
            generated_code += f"H_PREFETCH_V gp{img_addr_register}, gp{w_hbm_offset_register}, a0, 0, 0 \n"
            v_on_chip_addr += mlen

        # Load weight matrix for projection
        # Weight shape: (hidden_size, patch_embed_dim)
        # Load column by column (mlen elements at a time)
        generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, 0 \n"
        generated_code += f"S_ADDI_INT gp{w_hbm_offset_register}, gp0, 0 \n"

        for k in range(patch_embed_dim // mlen):
            generated_code += f"H_PREFETCH_M gp{w_actual_register}, gp{w_hbm_offset_register}, a{weight_base_hbm_offset_reg}, 1, 0 \n"
            generated_code += f"S_ADDI_INT gp{w_hbm_offset_register}, gp{w_hbm_offset_register}, {mlen * patch_embed_dim} \n"
            generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {mlen * mlen} \n"

        # Perform matrix multiplication: patch_embedding @ weight -> output
        # (patch_embed_dim,) @ (patch_embed_dim, hidden_size) -> (hidden_size,)
        # Reset registers to use on-chip addresses (not HBM addresses)
        generated_code += f"S_ADDI_INT gp{w_actual_register}, gp0, 0 \n"
        generated_code += f"S_ADDI_INT gp{img_addr_register}, gp0, 0 \n"

        for j in range(hidden_size // mlen):
            for i in range(patch_embed_dim // mlen):
                generated_code += f"M_MM 0, gp{w_actual_register}, gp{img_addr_register} \n"
                generated_code += f"S_ADDI_INT gp{w_actual_register}, gp{w_actual_register}, {mlen * mlen} \n"
                generated_code += f"S_ADDI_INT gp{img_addr_register}, gp{img_addr_register}, {mlen} \n"

            # Write output for this chunk of hidden_size
            generated_code += f"M_MM_WO gp{result_register}, gp0, 0 \n"
            generated_code += f"S_ADDI_INT gp{result_register}, gp{result_register}, {mlen} \n"
            # Reset to on-chip address for next iteration
            generated_code += f"S_ADDI_INT gp{img_addr_register}, gp0, 0 \n"

        # Move to next patch output location
        generated_code += f"S_ADDI_INT gp{result_register}, gp0, {result_base_address + (patch_idx + 1) * hidden_size} \n"

    return generated_code