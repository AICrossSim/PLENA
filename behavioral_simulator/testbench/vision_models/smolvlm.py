"""
SmolVLM Vision Encoder reference implementations for testing.

Contains:
- SmolVLMVisionEmbeddings: Full HuggingFace implementation with dynamic position embeddings
- SmolVLMPatchEmbedding: Simplified version for testing patch embedding (Conv2d) only
"""

import torch
from torch import nn


class SmolVLMVisionConfig:
    """Configuration for SmolVLM vision encoder"""
    def __init__(
        self,
        hidden_size=1152,
        image_size=384,
        patch_size=16,
        num_channels=3,
        **kwargs
    ):
        self.hidden_size = hidden_size
        self.image_size = image_size
        self.patch_size = patch_size
        self.num_channels = num_channels
        # Additional fields can be added as needed
        for key, value in kwargs.items():
            setattr(self, key, value)


class SmolVLMVisionEmbeddings(nn.Module):
    """
    Taken from https://github.com/huggingface/transformers/blob/main/src/transformers/models/smolvlm/modeling_smolvlm.py

    This is a modified version of `siglip.modelign_siglip.SiglipVisionEmbeddings` to enable images of variable
    resolution.

    The modifications are adapted from [Patch n' Pack: NaViT, a Vision Transformer for any Aspect Ratio and Resolution](https://huggingface.co/papers/2307.06304)
    which allows treating images in their native aspect ratio and without the need to resize them to the same
    fixed size. In particular, we start from the original pre-trained SigLIP model
    (which uses images of fixed-size square images) and adapt it by training on images of variable resolutions.
    """

    def __init__(self, config: SmolVLMVisionConfig):
        super().__init__()
        self.embed_dim = config.hidden_size
        self.image_size = config.image_size
        self.patch_size = config.patch_size

        self.patch_embedding = nn.Conv2d(
            in_channels=config.num_channels,
            out_channels=self.embed_dim,
            kernel_size=self.patch_size,
            stride=self.patch_size,
            padding="valid",
        )

        self.num_patches_per_side = self.image_size // self.patch_size
        self.num_patches = self.num_patches_per_side**2
        self.num_positions = self.num_patches
        self.position_embedding = nn.Embedding(self.num_positions, self.embed_dim)

    def forward(self, pixel_values: torch.FloatTensor, patch_attention_mask: torch.BoolTensor) -> torch.Tensor:
        batch_size, _, max_im_h, max_im_w = pixel_values.shape

        patch_embeds = self.patch_embedding(pixel_values)
        embeddings = patch_embeds.flatten(2).transpose(1, 2)

        max_nb_patches_h, max_nb_patches_w = max_im_h // self.patch_size, max_im_w // self.patch_size
        boundaries = torch.arange(
            1 / self.num_patches_per_side, 1.0, 1 / self.num_patches_per_side, device=pixel_values.device
        )
        position_ids = torch.full(
            size=(batch_size, max_nb_patches_h * max_nb_patches_w), fill_value=0, device=pixel_values.device
        )

        for batch_idx, p_attn_mask in enumerate(patch_attention_mask):
            nb_patches_h = p_attn_mask[:, 0].sum()
            nb_patches_w = p_attn_mask[0].sum()

            step_h = 1.0 / nb_patches_h
            step_w = 1.0 / nb_patches_w

            h_indices = torch.arange(nb_patches_h, device=position_ids.device, dtype=torch.float32)
            w_indices = torch.arange(nb_patches_w, device=position_ids.device, dtype=torch.float32)
            fractional_coords_h = h_indices * step_h
            fractional_coords_w = w_indices * step_w

            fractional_coords_h = torch.clamp(fractional_coords_h, max=(1.0 - 1e-6))
            fractional_coords_w = torch.clamp(fractional_coords_w, max=(1.0 - 1e-6))

            fractional_coords_h = fractional_coords_h.to(pixel_values.dtype)
            fractional_coords_w = fractional_coords_w.to(pixel_values.dtype)

            bucket_coords_h = torch.bucketize(fractional_coords_h, boundaries, right=True)
            bucket_coords_w = torch.bucketize(fractional_coords_w, boundaries, right=True)

            pos_ids = (bucket_coords_h[:, None] * self.num_patches_per_side + bucket_coords_w).flatten()
            position_ids[batch_idx][p_attn_mask.view(-1)] = pos_ids

        embeddings = embeddings + self.position_embedding(position_ids)
        return embeddings


class SmolVLMPatchEmbedding(nn.Module):
    """
    Simplified version of SmolVLM's SmolVLMVisionEmbeddings for testing.
    This replicates the core Conv2d patch embedding operation without the
    (learned) positional encoding.

    Uses static (sequential) position embeddings for easier verification.
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

        # Conv2d patch embedding
        # Input: (B, C, H, W)
        # Output: (B, embed_dim, H//P, W//P)
        patch_embeds = self.patch_embedding(pixel_values)

        # Flatten and transpose into sequence format
        # (B, embed_dim, H_p, W_p) -> (B, num_patches, embed_dim)
        embeddings = patch_embeds.flatten(2).transpose(1, 2)

        # Add position encodings (static sequential)
        position_ids = torch.arange(self.num_patches, device=pixel_values.device)
        position_ids = position_ids.unsqueeze(0).expand(batch_size, -1)
        embeddings = embeddings + self.position_embedding(position_ids)

        return embeddings

    def get_conv_weights_for_gemm(self):
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

    def im2col_only(self, pixel_values):
        """
        Extract patches from images using im2col (no GEMM, no position encoding).

        Args:
            pixel_values: (batch_size, channels, height, width)

        Returns:
            patches: (batch_size, num_patches, C*P*P) - extracted patches
        """
        batch_size, C, H, W = pixel_values.shape
        P = self.patch_size
        num_patches_h = H // P
        num_patches_w = W // P
        num_patches = num_patches_h * num_patches_w

        # Im2col - extract patches
        # Output: (batch_size, num_patches, C*P*P)
        patches = []
        for b in range(batch_size):
            batch_patches = []
            for i in range(num_patches_h):
                for j in range(num_patches_w):
                    # Extract patch at position (i, j)
                    patch = pixel_values[b, :, i*P:(i+1)*P, j*P:(j+1)*P]
                    # Flatten: (C, P, P) -> (C*P*P,)
                    patch_flat = patch.reshape(-1)
                    batch_patches.append(patch_flat)
            patches.append(torch.stack(batch_patches))

        # Stack: (batch_size, num_patches, C*P*P)
        return torch.stack(patches)

    def im2col_gemm(self, pixel_values):
        """
        Manually perform im2col + GEMM to verify equivalence to Conv2D.
        """
        batch_size, C, H, W = pixel_values.shape
        P = self.patch_size
        num_patches_h = H // P
        num_patches_w = W // P
        num_patches = num_patches_h * num_patches_w

        # Im2col - extract patches
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

        # GEMM
        # (batch_size * num_patches, C*P*P) @ (C*P*P, embed_dim)
        # -> (batch_size * num_patches, embed_dim)
        gemm_weight = self.get_conv_weights_for_gemm()
        output = patches_matrix @ gemm_weight

        # Reshape back to (batch_size, num_patches, embed_dim)
        output = output.reshape(batch_size, num_patches, self.embed_dim)

        # Add (simple) position embeddings
        position_ids = torch.arange(self.num_patches, device=pixel_values.device)
        position_ids = position_ids.unsqueeze(0).expand(batch_size, -1)
        output = output + self.position_embedding(position_ids)

        return output

class SmolVLMPositionalEncoding(nn.Module):
    pass

class SmolLM1DRoPE(nn.Module):
    pass
