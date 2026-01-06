import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from compiler.asm_templates import patch_embedding_asm, reset_reg_asm, preload_addr_reg_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim
from vision_models import SmolVLMPatchEmbedding
import json


def test_equivalence(model, pixel_values, batch_size, num_patches, hidden_size):
    """Test that Conv2d is equivalent to Im2col + GEMM"""
    print("=" * 70)
    print("Testing Conv2d = Im2col + GEMM Equivalence")
    print("=" * 70)

    with torch.no_grad():
        output_conv2d = model.forward(pixel_values)
        output_im2col_gemm = model.im2col_gemm(pixel_values)

    # Verify equivalence
    max_diff = torch.max(torch.abs(output_conv2d - output_im2col_gemm)).item()
    print(f"\nMax difference between Conv2d and Im2col+GEMM: {max_diff:.6e}")
    print(f"Output shape: {output_conv2d.shape}")
    print(f"Expected: (batch={batch_size}, num_patches={num_patches}, hidden_size={hidden_size})")

    if max_diff < 1e-5:
        print("\nSUCCESS: Conv2d and Im2col+GEMM produce equivalent results!")
    else:
        print(f"\nFAILED: Outputs differ by {max_diff}")

    return output_conv2d


def test_im2col_assembly(model, pixel_values, config, real_data_ratio, fp_preload):
    """Test Im2col assembly generation only (no GEMM)"""
    batch_size = pixel_values.shape[0]
    channels = config["channels"]
    image_height = config["image_height"]
    image_width = config["image_width"]
    patch_size = config["patch_size"]

    num_patches_h = image_height // patch_size
    num_patches_w = image_width // patch_size
    num_patches = num_patches_h * num_patches_w
    patch_elements = channels * patch_size * patch_size

    print("\n" + "=" * 70)
    print("Im2col Assembly Generation Test")
    print("=" * 70)

    print(f"\nGenerating assembly for Im2col only:")
    print(f"  Input:  ({batch_size}, {channels}, {image_height}, {image_width})")
    print(f"  Output: ({batch_size}, {num_patches}, {patch_elements}) - extracted patches")
    print(f"  Patches: {num_patches_h}x{num_patches_w} = {num_patches} patches")
    print(f"  Patch elements: {patch_elements} (C*P*P = {channels}*{patch_size}*{patch_size})")

    # Get expected output from model
    with torch.no_grad():
        expected_patches = model.im2col_only(pixel_values)

    print(f"\nExpected patches shape: {expected_patches.shape}")

    # Prepare input tensors for HBM
    image_flat = pixel_values.reshape(-1, 1)  # Flatten to 2D for memory simulation

    input_tensor = {
        "image": image_flat,  # (batch*C*H*W, 1) - flattened image
    }

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": expected_patches  # (batch_size, num_patches, patch_elements)
    }

    print("\nGenerating Im2col assembly code...")
    gen_assembly_code = "; Im2col-only Assembly Test\n"

    # Calculate HBM offsets
    image_hbm_size = int(batch_size * channels * image_height * image_width * real_data_ratio)

    print(f"\nHBM Memory Layout:")
    print(f"  Image data: 0x0000 - 0x{image_hbm_size:04x} ({image_hbm_size} elements)")

    # Set HBM address registers
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[0],
        available_registers=[1],
        addr_reg_val=[0]
    )

    # Reset scalar registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1, 2, 3, 4, 5, 6]
    )

    # Generate im2col assembly (patch_embedding_asm currently only has im2col)
    activation_base_address = 0  # Store patches at start of VRAM

    gen_assembly_code += patch_embedding_asm(
        mlen=64,
        blen=4,
        batch=batch_size,
        channels=channels,
        image_height=image_height,
        image_width=image_width,
        patch_size=patch_size,
        hidden_size=128,  # Unused for im2col-only, but required parameter
        alive_registers=[1, 2, 3, 4, 5, 6],
        image_hbm_offset_reg=0,
        weight_hbm_offset_reg=1,  # Unused
        activation_base_address=activation_base_address,
        result_base_address=0  # Unused
    )

    # Create simulation environment
    print("\nCreating simulation environment...")
    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    create_mem_for_sim(
        data_size=256,
        mode="behave_sim",
        asm="im2col",
        data=None,
        specified_data_order=["image"]
    )

    # Save comparison parameters for view_mem.py
    vlen = 64
    patch_elements_aligned = ((patch_elements + vlen - 1) // vlen) * vlen
    result_start_row = activation_base_address // vlen
    # Calculate total VRAM used (each patch is aligned to VLEN)
    total_elements = batch_size * num_patches * patch_elements_aligned
    num_result_rows = total_elements // vlen

    comparison_params = {
        "start_row_idx": result_start_row,
        "num_rows": num_result_rows,
        "num_batches": batch_size,
        "num_patches": num_patches,
        "patch_elements": patch_elements,
        "patch_elements_aligned": patch_elements_aligned
    }
    build_dir = Path(__file__).parent / "build"
    build_dir.mkdir(exist_ok=True)
    with open(build_dir / "comparison_params.json", "w") as f:
        json.dump(comparison_params, f, indent=2)

    print("\n" + "=" * 70)
    print("Im2col assembly generation complete!")
    print("=" * 70)
    print(f"\nPatches stored in Vector SRAM:")
    print(f"  Start row: {result_start_row}")
    print(f"  Num rows:  {num_result_rows}")
    print(f"  Patch elements (actual): {patch_elements}")
    print(f"  Patch elements (aligned): {patch_elements_aligned}")
    print(f"  Total patches: {batch_size * num_patches}")
    print("=" * 70)

    return expected_patches


def test_full_assembly(model, pixel_values, config, real_data_ratio, fp_preload):
    """Test full patch embedding assembly (Im2col + GEMM + position encoding)"""
    batch_size = pixel_values.shape[0]
    channels = config["channels"]
    image_height = config["image_height"]
    image_width = config["image_width"]
    patch_size = config["patch_size"]
    hidden_size = config["hidden_size"]

    num_patches_h = image_height // patch_size
    num_patches_w = image_width // patch_size
    num_patches = num_patches_h * num_patches_w
    patch_elements = channels * patch_size * patch_size

    print("\n" + "=" * 70)
    print("Full Patch Embedding Assembly Generation Test")
    print("=" * 70)

    print(f"\nGenerating assembly for full patch embedding:")
    print(f"  Input:  ({batch_size}, {channels}, {image_height}, {image_width})")
    print(f"  Output: ({batch_size}, {num_patches}, {hidden_size})")
    print(f"  Patches: {num_patches_h}x{num_patches_w} = {num_patches} patches")
    print(f"  Patch elements: {patch_elements} (C*P*P = {channels}*{patch_size}*{patch_size})")

    # Get expected output from model
    with torch.no_grad():
        output_conv2d = model.forward(pixel_values)

    # Prepare weights for assembly generation
    print("\nPreparing input tensors for simulation...")
    gemm_weight = model.get_conv_weights_for_gemm()  # (patch_elements, hidden_size)
    position_embeddings = model.position_embedding.weight.data  # (num_patches, hidden_size)

    # Extract patches manually to create input tensor for HBM
    # Note: The assembly will do im2col from raw image, but we provide patches for verification
    patches = []
    for b in range(batch_size):
        for i in range(num_patches_h):
            for j in range(num_patches_w):
                patch = pixel_values[b, :, i*patch_size:(i+1)*patch_size, j*patch_size:(j+1)*patch_size]
                patches.append(patch.reshape(-1))
    patches_tensor = torch.stack(patches).reshape(batch_size, num_patches, patch_elements)
    print(f"Extracted patches: {patches_tensor.shape}")

    # Prepare input tensors for HBM
    # Note: Memory simulation expects 2D tensors, so flatten image to (batch*channels*height*width, 1)
    image_flat = pixel_values.reshape(-1, 1)  # Flatten to 2D for memory simulation

    input_tensor = {
        "image": image_flat,             # (batch*C*H*W, 1) - flattened image
        "weights": gemm_weight,          # (patch_elements, hidden_size)
        "position_embeddings": position_embeddings  # (num_patches, hidden_size)
    }

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": output_conv2d  # (batch_size, num_patches, hidden_size)
    }

    print("\nGenerating assembly code...")
    gen_assembly_code = "; Patch Embedding Assembly Test\n"

    # Calculate HBM offsets
    # Layout in HBM: [image_data | weights | position_embeddings]
    image_hbm_size = int(batch_size * channels * image_height * image_width * real_data_ratio)
    weight_hbm_offset = image_hbm_size

    weight_hbm_size = int(patch_elements * hidden_size * real_data_ratio)
    pos_emb_hbm_offset = weight_hbm_offset + weight_hbm_size

    print(f"\nHBM Memory Layout:")
    print(f"  Image data:         0x0000 - 0x{image_hbm_size:04x} ({image_hbm_size} elements)")
    print(f"  Weights:            0x{weight_hbm_offset:04x} - 0x{weight_hbm_offset + weight_hbm_size:04x} ({weight_hbm_size} elements)")
    print(f"  Position embeddings: 0x{pos_emb_hbm_offset:04x} onwards")

    # Set HBM address registers
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[0, 1, 2],
        available_registers=[1, 2, 3],
        addr_reg_val=[0, weight_hbm_offset, pos_emb_hbm_offset]
    )

    # Reset scalar registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1, 2, 3, 4, 5, 6, 7, 8]
    )

    # Generate patch embedding assembly
    result_vram_offset = 0  # Store results at start of VRAM

    gen_assembly_code += patch_embedding_asm(
        mlen=64,
        blen=4,
        batch=batch_size,
        channels=channels,
        image_height=image_height,
        image_width=image_width,
        patch_size=patch_size,
        hidden_size=hidden_size,
        alive_registers=[1, 2, 3, 4, 5, 6],
        image_hbm_offset_reg=0,
        weight_hbm_offset_reg=1,
        activation_base_address=0,
        result_base_address=result_vram_offset
    )

    # Create simulation environment
    print("\nCreating simulation environment...")
    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    create_mem_for_sim(
        data_size=256,
        mode="behave_sim",
        asm="patch_embedding",
        data=None,
        specified_data_order=["image", "weights", "position_embeddings"]
    )

    # Save comparison parameters for view_mem.py
    vlen = 64
    result_start_row = result_vram_offset // vlen
    num_result_rows = (batch_size * num_patches * hidden_size) // vlen
    comparison_params = {
        "start_row_idx": result_start_row,
        "num_rows": num_result_rows,
        "num_batches": batch_size,
        "elements_per_batch": num_patches * hidden_size
    }
    build_dir = Path(__file__).parent / "build"
    build_dir.mkdir(exist_ok=True)
    with open(build_dir / "comparison_params.json", "w") as f:
        json.dump(comparison_params, f, indent=2)

    print("\n" + "=" * 70)
    print("Assembly generation complete!")
    print("=" * 70)
    print(f"\nOutput location in Vector SRAM:")
    print(f"  Start row: {result_start_row}")
    print(f"  Num rows:  {num_result_rows}")
    print(f"  Total elements: {batch_size * num_patches * hidden_size}")
    print("=" * 70)


if __name__ == "__main__":
    # SmolVLM Vision configuration
    # Using smaller dimensions for initial testing
    channels = 3
    image_height = 64      # Smaller than 384 for testing
    image_width = 64
    patch_size = 16        # 4x4 = 16 patches
    hidden_size = 128      # Smaller than 1152 for testing
    batch_size = 1

    num_patches_h = image_height // patch_size  # 4
    num_patches_w = image_width // patch_size   # 4
    num_patches = num_patches_h * num_patches_w  # 16
    patch_elements = channels * patch_size * patch_size  # 3*16*16 = 768

    real_data_ratio = (8*8 + 8) / (8 * 8)  # MXFP format overhead
    fp_preload = [0.0, 1e-6, 1.0/hidden_size]

    config = {
        "channels": channels,
        "image_height": image_height,
        "image_width": image_width,
        "patch_size": patch_size,
        "hidden_size": hidden_size,
    }

    # Create model and generate test data
    torch.manual_seed(42)
    pixel_values = torch.randn(batch_size, channels, image_height, image_width)
    model = SmolVLMPatchEmbedding(config)
    model.eval()

    # Run tests
    print("\n")
    print("#" * 70)
    print("#  Patch Embedding Test Suite")
    print("#" * 70)

    # Test 1: Equivalence check
    output_conv2d = test_equivalence(model, pixel_values, batch_size, num_patches, hidden_size)

    # Test 2: Im2col assembly generation (TODO)
    expected_patches = test_im2col_assembly(model, pixel_values, config, real_data_ratio, fp_preload)

    # Test 3: Full assembly generation
    # test_full_assembly(model, pixel_values, config, real_data_ratio, fp_preload)

    print("\n")
    print("#" * 70)
    print("#  All tests completed!")
    print("#" * 70)
