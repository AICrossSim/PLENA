import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import nn
from compiler.asm_templates import patch_embedding_asm, reset_reg_asm, preload_addr_reg_asm
from create_sim_env import create_sim_env
from sim_env_utils import build_sim_env
from asm_perf_tracker import AsmPerfTracker


class PatchEmbedding(nn.Module):
    """
    Vision Transformer Patch Embedding layer.
    Converts an image into patch embeddings.
    """
    def __init__(
        self,
        img_height: int = 224,
        img_width: int = 224,
        patch_size: int = 16,
        in_channels: int = 3,
        hidden_size: int = 768,
    ):
        super().__init__()
        self.img_height = img_height
        self.img_width = img_width
        self.patch_size = patch_size
        self.in_channels = in_channels
        self.hidden_size = hidden_size

        # Calculate number of patches
        self.num_patches = (img_height // patch_size) * (img_width // patch_size)

        # Projection layer: (in_channels * patch_size * patch_size) -> hidden_size
        self.projection = nn.Linear(
            in_channels * patch_size * patch_size,
            hidden_size,
            bias=False
        )

    def forward(self, x):
        """
        Args:
            x: Input tensor of shape (batch_size, in_channels, img_height, img_width)

        Returns:
            Patch embeddings of shape (batch_size, num_patches, hidden_size)
        """
        batch_size = x.shape[0]

        # Reshape image into patches
        # (batch_size, in_channels, img_height, img_width) -> (batch_size, num_patches, patch_size*patch_size*in_channels)
        x = x.unfold(2, self.patch_size, self.patch_size).unfold(3, self.patch_size, self.patch_size)
        x = x.contiguous().view(batch_size, self.in_channels, -1, self.patch_size, self.patch_size)
        x = x.permute(0, 2, 1, 3, 4).contiguous()
        x = x.view(batch_size, self.num_patches, -1)

        # Apply linear projection
        x = self.projection(x)

        return x


if __name__ == "__main__":
    # Test parameters - using smaller dimensions for testing
    # NOTE: For HBM alignment, we need:
    # 1. img_width * in_channels must be a multiple of 64
    # 2. patch_size * in_channels must be a multiple of mlen
    img_height = 64
    img_width = 64
    patch_size = 16
    in_channels = 4  # Use 4 channels (RGBA) instead of 3 (RGB) for alignment
    hidden_size = 192  # Use 192 instead of 256 to keep scale_value < 2^18
    batch_size = 1  # Single image for testing
    mlen = 64
    blen = 4

    num_patches = (img_height // patch_size) * (img_width // patch_size)
    patch_embed_dim = patch_size * patch_size * in_channels

    print(f"Image size: {img_height}x{img_width}")
    print(f"Patch size: {patch_size}x{patch_size}")
    print(f"Number of patches: {num_patches}")
    print(f"Patch embedding dim: {patch_embed_dim}")
    print(f"Hidden size: {hidden_size}")

    # Validate dimensions
    assert hidden_size % mlen == 0, f"hidden_size must be divisible by mlen"
    assert patch_embed_dim % mlen == 0, f"patch_embed_dim must be divisible by mlen"

    real_data_ratio = (8*8 + 8) / (8 * 8)
    fp_preload = [0.0, 1e-6, 1/hidden_size]

    # Generate random test data
    torch.manual_seed(42)

    # Input image: (batch_size, in_channels, img_height, img_width)
    img_tensor = torch.randn(batch_size, in_channels, img_height, img_width)

    # Create patch embedding layer
    patch_embed_layer = PatchEmbedding(
        img_height=img_height,
        img_width=img_width,
        patch_size=patch_size,
        in_channels=in_channels,
        hidden_size=hidden_size
    )

    weights = patch_embed_layer.state_dict()

    # Get golden output
    original_output = patch_embed_layer(img_tensor)

    print(f"\nInput image shape: {img_tensor.shape}")
    print(f"Output embeddings shape: {original_output.shape}")
    print(f"Weight shape: {weights['projection.weight'].shape}")

    # Flatten image for simulation (C, H, W) layout
    # The assembly expects data in (in_channels, img_height, img_width) layout
    img_flat = img_tensor[0].reshape(-1)  # Take first batch element and flatten

    input_tensor = {
        "img_tensor": img_flat,
        "weights": weights['projection.weight'].t(),  # Transpose to (patch_embed_dim, hidden_size)
    }

    # Flatten output for comparison (num_patches, hidden_size)
    output_flat = original_output[0]  # Take first batch element

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": output_flat
    }

    # Initialize performance tracker
    perf = AsmPerfTracker("Patch Embedding Test")
    perf.assembly_code = "; Patch Embedding Test Generation \n"

    # Calculate memory offsets
    img_size = in_channels * img_height * img_width
    weight_size = patch_embed_dim * hidden_size
    weight_offset = int(img_size * real_data_ratio)

    # Set the addr offset for image, weight, and result
    perf.add_section("preload_addr_reg_asm", preload_addr_reg_asm(
        addr_reg_to_set=[0, 1, 2],
        available_registers=[1, 2, 3],
        addr_reg_val=[0, weight_offset, img_size]  # Image at 0, weights after image, results at img_size (same as result_base_address)
    ))

    # Reset the registers
    perf.add_section("reset_reg_asm", reset_reg_asm(
        alive_registers=[1, 2, 3, 4]
    ))

    # Generate patch embedding assembly
    perf.add_section("patch_embedding_asm", patch_embedding_asm(
        patch_size=patch_size,
        num_patches=num_patches,
        hidden_size=hidden_size,
        img_height=img_height,
        img_width=img_width,
        in_channels=in_channels,
        alive_registers=[1, 2, 3, 4],
        mlen=mlen,
        blen=blen,
        weight_base_hbm_offset_reg=1,
        img_base_address=0,
        result_base_address=img_size
    ))

    # Write performance stats
    perf.write_stats()

    create_sim_env(input_tensor, perf.get_code(), golden_result, fp_preload)
    build_sim_env(
        data_size=512,
        mode="behave_sim",
        asm="patch_embedding",
        data=None,
        specified_data_order=["img_tensor", "weights"]
    )

    print("\n================================================")
    print("Finished generating assembly code for patch embedding")
    print("================================================")
