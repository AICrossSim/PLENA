import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import nn
from compiler.asm_templates import patch_embedding_asm, reset_reg_asm, preload_addr_reg_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim


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

    with torch.no_grad():
        original_output = model.forward(pixel_values)
        manual_output = model.manual_im2col_gemm(pixel_values)

    # Verify equivalence
    max_diff = torch.max(torch.abs(original_output - manual_output)).item()
    print(f"Conv2d vs Im2col+GEMM max difference: {max_diff:.6e}")

    if max_diff < 1e-5:
        print("✅ Conv2d and Im2col+GEMM produce equivalent results!")
    else:
        print(f"❌ Outputs differ by {max_diff}")
        exit(1)

    print(f"\nPatch Embedding: ({batch_size}, {channels}, {image_height}, {image_width}) -> ({batch_size}, {num_patches}, {hidden_size})")
    print("original_output shape:", original_output.shape)

    # Prepare weights for assembly generation
    gemm_weight = model.get_conv_weights_as_gemm_matrix()  # (patch_elements, hidden_size)
    position_embeddings = model.position_embedding.weight.data  # (num_patches, hidden_size)

    print(f"GEMM weight shape: {gemm_weight.shape} (expected: ({patch_elements}, {hidden_size}))")
    print(f"Position embeddings shape: {position_embeddings.shape}")

    # Reshape pixel values to im2col format for input_tensor
    # Extract patches manually to create the input tensor
    patches = []
    for b in range(batch_size):
        for i in range(num_patches_h):
            for j in range(num_patches_w):
                patch = pixel_values[b, :, i*patch_size:(i+1)*patch_size, j*patch_size:(j+1)*patch_size]
                patches.append(patch.reshape(-1))
    patches_tensor = torch.stack(patches).reshape(batch_size, num_patches, patch_elements)

    input_tensor = {
        "patches": patches_tensor,  # (batch_size, num_patches, patch_elements)
        "weights": gemm_weight,     # (patch_elements, hidden_size)
        "position_embeddings": position_embeddings  # (num_patches, hidden_size)
    }

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": original_output  # (batch_size, num_patches, hidden_size)
    }

    gen_assembly_code = "; Patch Embedding Test Generation\n"
    gen_assembly_code += f"; Shape: ({batch_size}, {channels}, {image_height}, {image_width}) -> ({batch_size}, {num_patches}, {hidden_size})\n"

    # Calculate HBM offsets
    # Layout in HBM: [image_data | weights | position_embeddings]
    image_hbm_size = int(batch_size * channels * image_height * image_width * real_data_ratio)
    weight_hbm_offset = image_hbm_size
    weight_hbm_size = int(patch_elements * hidden_size * real_data_ratio)
    pos_emb_hbm_offset = weight_hbm_offset + weight_hbm_size
    pos_emb_hbm_end = pos_emb_hbm_offset + int(num_patches * hidden_size * real_data_ratio)

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
        alive_registers=[1, 2, 3, 4, 5, 6, 7, 8],
        image_hbm_offset_reg=0,
        weight_hbm_offset_reg=1,
        activation_base_address=0,
        result_base_address=result_vram_offset
    )

    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    create_mem_for_sim(data_size=256, mode="behave_sim", asm="patch_embedding", data=None,
                       specified_data_order=["patches", "weights", "position_embeddings"])

    # Save comparison parameters for view_mem.py
    import json
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

    print("================================================")
    print("Finished generating assembly code")
    print(f"Result location: row {result_start_row}, {num_result_rows} rows")
    print(f"Comparison params: {comparison_params}")
    print("================================================")
