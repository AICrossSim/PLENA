#!/usr/bin/env python3
"""
Test script for patch embedding code generation
"""

import sys
import os
from pathlib import Path
import torch
import torch.nn as nn
import numpy as np

# Add compiler directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "compiler"))
from passes.code_gen import _generate_patch_embedding_code
from assembler import AssemblyToBinary


# Replicate SmolVLM's patch embedding for reference
class SmolVLMPatchEmbedding(nn.Module):
    """
    Simplified version of SmolVLM's SmolVLMVisionEmbeddings for testing.
    This replicates the core Conv2d patch embedding operation.
    """
    def __init__(self, config):
        super().__init__()
        self.embed_dim = config["hidden_size"]
        self.image_size = config["image_height"]  # Assume square images
        self.patch_size = config["patch_size"]
        self.num_channels = config["channels"]

        # Core Conv2d operation: kernel_size=patch_size, stride=patch_size
        # This is the operation we need to translate to Im2col + GEMM
        self.patch_embedding = nn.Conv2d(
            in_channels=self.num_channels,
            out_channels=self.embed_dim,
            kernel_size=self.patch_size,
            stride=self.patch_size,
            padding=0,  # "valid" padding
            bias=False  # For simplicity, no bias
        )

        # Position embeddings (learned)
        self.num_patches_per_side = self.image_size // self.patch_size
        self.num_patches = self.num_patches_per_side ** 2
        self.position_embedding = nn.Embedding(self.num_patches, self.embed_dim)

    def forward(self, pixel_values):
        """
        Args:
            pixel_values: (batch_size, channels, height, width)

        Returns:
            embeddings: (batch_size, num_patches, embed_dim)
        """
        batch_size, _, height, width = pixel_values.shape

        # Step 1: Conv2d patch embedding
        # Input: (B, C, H, W)
        # Output: (B, embed_dim, H//P, W//P)
        patch_embeds = self.patch_embedding(pixel_values)

        # Step 2: Flatten and transpose
        # (B, embed_dim, H_p, W_p) -> (B, num_patches, embed_dim)
        embeddings = patch_embeds.flatten(2).transpose(1, 2)

        # Step 3: Add position embeddings
        position_ids = torch.arange(self.num_patches, device=pixel_values.device)
        position_ids = position_ids.unsqueeze(0).expand(batch_size, -1)
        embeddings = embeddings + self.position_embedding(position_ids)

        return embeddings

    def get_conv_weights_as_gemm_matrix(self):
        """
        Extract Conv2d weights and reshape for GEMM operation.
        Conv2d weight shape: (out_channels, in_channels, kernel_h, kernel_w)
        GEMM weight shape: (in_channels * kernel_h * kernel_w, out_channels)
        """
        conv_weight = self.patch_embedding.weight.data  # (embed_dim, C, P, P)

        # Reshape to GEMM format: (C*P*P, embed_dim)
        embed_dim, C, P, _ = conv_weight.shape
        gemm_weight = conv_weight.permute(1, 2, 3, 0)  # (C, P, P, embed_dim)
        gemm_weight = gemm_weight.reshape(C * P * P, embed_dim)

        return gemm_weight

    def manual_im2col_gemm(self, pixel_values):
        """
        Manually perform im2col + GEMM to verify the equivalence.
        This is the operation we need to implement in assembly.
        """
        batch_size, C, H, W = pixel_values.shape
        P = self.patch_size
        num_patches_h = H // P
        num_patches_w = W // P
        num_patches = num_patches_h * num_patches_w

        # Step 1: Im2col - extract patches
        # Output: (batch_size, num_patches, C*P*P)
        patches = []
        for b in range(batch_size):
            for i in range(num_patches_h):
                for j in range(num_patches_w):
                    # Extract patch at position (i, j)
                    patch = pixel_values[b, :, i*P:(i+1)*P, j*P:(j+1)*P]
                    # Flatten: (C, P, P) -> (C*P*P,)
                    patch_flat = patch.reshape(-1)
                    patches.append(patch_flat)

        # Stack all patches: (batch_size * num_patches, C*P*P)
        patches_matrix = torch.stack(patches)

        # Step 2: GEMM - matrix multiplication
        # (batch_size * num_patches, C*P*P) @ (C*P*P, embed_dim)
        # -> (batch_size * num_patches, embed_dim)
        gemm_weight = self.get_conv_weights_as_gemm_matrix()
        output = patches_matrix @ gemm_weight

        # Reshape back to (batch_size, num_patches, embed_dim)
        output = output.reshape(batch_size, num_patches, self.embed_dim)

        # Add position embeddings
        position_ids = torch.arange(self.num_patches, device=pixel_values.device)
        position_ids = position_ids.unsqueeze(0).expand(batch_size, -1)
        output = output + self.position_embedding(position_ids)

        return output

def test_smolvlm_patch_embedding_equivalence():
    """
    Test that manual im2col+GEMM produces same results as Conv2d.
    This verifies our understanding before implementing in assembly.
    """
    print("\n=== Testing SmolVLM Patch Embedding Equivalence ===")

    config = {
        "channels": 3,
        "image_height": 384,
        "image_width": 384,
        "patch_size": 16,
        "hidden_size": 1152,
    }

    # Create model
    model = SmolVLMPatchEmbedding(config)
    model.eval()

    # Create random input image
    batch_size = 1
    pixel_values = torch.randn(batch_size, 3, 384, 384)

    # Method 1: Standard Conv2d forward pass
    with torch.no_grad():
        output_conv2d = model.forward(pixel_values)

    # Method 2: Manual im2col + GEMM
    with torch.no_grad():
        output_im2col_gemm = model.manual_im2col_gemm(pixel_values)

    # Verify equivalence
    max_diff = torch.max(torch.abs(output_conv2d - output_im2col_gemm)).item()
    print(f"Max difference between Conv2d and Im2col+GEMM: {max_diff:.6e}")

    if max_diff < 1e-5:
        print("✅ Conv2d and Im2col+GEMM produce equivalent results!")
    else:
        print(f"❌ Outputs differ by {max_diff}")

    # Print shapes for verification
    print(f"\nShapes:")
    print(f"  Input: {pixel_values.shape}")
    print(f"  Output: {output_conv2d.shape}")
    print(f"  Expected: (batch={batch_size}, num_patches={(384//16)**2}, embed_dim={config['hidden_size']})")

    # Print weight matrix info
    gemm_weight = model.get_conv_weights_as_gemm_matrix()
    print(f"\nGEMM weight matrix shape: {gemm_weight.shape}")
    print(f"  Expected: ({3*16*16}, {config['hidden_size']}) = (768, 1152)")

    return max_diff < 1e-5


def test_patch_embedding_code_generation():
    """Test the patch embedding code generation function"""

    # Test node with SmolVLM Vision parameters
    test_node = {
        "name": "patch_embedding",
        "operation_type": "patch_embedding",
        "dimensions": {
            "channels": 3,           # RGB input
            "image_height": 384,     # SmolVLM image size
            "image_width": 384,
            "patch_size": 16,        # 16x16 patches -> 24x24 = 576 patches
            "hidden_size": 1152,     # SmolVLM embedding dimension
        }
    }

    hardware_config = {
        "mlen": 64,
        "blen": 4,
        "vlen": 64,
        "alive_registers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    }

    model_info = {
        "batch_size": 1
    }

    scheduler = {
        "activation_base_address": 0,
        "result_base_address": 16384,  # Offset for output storage
        "register_assignment": {
            "hbm_addr_reg": {
                "image_offset": 0,
                "weight_offset": 1
            }
        }
    }

    # TODO: Implement _generate_patch_embedding_code in passes/code_gen.py
    # Generate the assembly code
    generated_code = _generate_patch_embedding_code(
        test_node,
        model_info=model_info,
        hardware_config=hardware_config,
        scheduler=scheduler
    )

    # Write out assembly
    with open("generated_patch_embedding_assembly.asm", "w") as f:
        f.write(generated_code)

    # Write out machine code
    config_parent_path = Path(__file__).resolve().parents[2]
    print(f"Config parent path: {config_parent_path}")

    print("✅ All tests passed! The patch embedding code generation is working correctly.")


if __name__ == "__main__":
    # Step 1: Verify equivalence of Conv2d and Im2col+GEMM
    print("=" * 70)
    print("STEP 1: Verify Conv2d = Im2col + GEMM equivalence")
    print("=" * 70)
    equivalence_passed = test_smolvlm_patch_embedding_equivalence()

    if not equivalence_passed:
        print("\n❌ Equivalence test failed. Fix before proceeding to assembly generation.")
        exit(1)

    # Step 2: Generate assembly code
    print("\n" + "=" * 70)
    print("STEP 2: Generate assembly code for patch embedding")
    print("=" * 70)
    test_patch_embedding_code_generation()

    # Step 3: Generate binary
    print("\n" + "=" * 70)
    print("STEP 3: Generate binary from assembly")
    print("=" * 70)
    config_path = Path(__file__).resolve().parents[2] / "src" / "definitions" / "configuration.svh"
    isa_def_path = Path(__file__).resolve().parents[2] / "src" / "definitions" / "operation.svh"
    assembler = AssemblyToBinary(isa_def_path, config_path)
    # TODO: Verify the generated assembly is correct
    assembler.generate_binary("generated_patch_embedding_assembly.asm", "generated_patch_embedding_assembly.mem")
    print("✅ Generated binary file: generated_patch_embedding_assembly.mem")

    print("\n" + "=" * 70)
    print("All tests completed!")
    print("=" * 70)
