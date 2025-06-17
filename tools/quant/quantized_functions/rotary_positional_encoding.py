from functools import partial
import torch
from typing import Callable, Optional

from ..quantizer import mxfp_quantizer, minifloat_ieee_quantizer


def rotate_half(x: torch.Tensor) -> torch.Tensor:
    """Rotate half the last dimension (for RoPE)."""
    x1 = x[..., : x.shape[-1] // 2]
    x2 = x[..., x.shape[-1] // 2 :]
    return torch.cat((-x2, x1), dim=-1)


def _apply_rope_with_quantizer(
    q: torch.Tensor,
    k: torch.Tensor,
    cos: torch.Tensor,
    sin: torch.Tensor,
    quantizer: Callable[[torch.Tensor], torch.Tensor],
    unsqueeze_dim: int = 1
) -> tuple[torch.Tensor, torch.Tensor]:
    """Applies RoPE with a given quantizer to query/key tensors."""
    cos = quantizer(cos).unsqueeze(unsqueeze_dim)
    sin = quantizer(sin).unsqueeze(unsqueeze_dim)

    seq_len = q.size(-2)
    cos = cos[..., :seq_len, :]
    sin = sin[..., :seq_len, :]

    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)

    return q_embed, k_embed


def apply_rotary_pos_emb_mxfp(
    q: torch.Tensor,
    k: torch.Tensor,
    cos: torch.Tensor,
    sin: torch.Tensor,
    quant_config: dict,
    position_ids: Optional[torch.Tensor] = None,
    unsqueeze_dim: int = 1
) -> tuple[torch.Tensor, torch.Tensor]:
    """Apply Rotary Position Embedding using MXFP quantization."""
    if quant_config.get("bypass", False):
        quantizer = lambda x: x
    else:
        quantizer = partial(
            mxfp_quantizer,
            width=quant_config["data_in_width"],
            exponent_width=quant_config["data_in_exponent_width"],
            exponent_bias_width=quant_config["data_in_exponent_bias_width"],
            block_size=quant_config["data_in_block_size"],
            skip_first_dim=False,
        )

    return _apply_rope_with_quantizer(q, k, cos, sin, quantizer, unsqueeze_dim)


def apply_rotary_pos_emb_minifloat_ieee(
    q: torch.Tensor,
    k: torch.Tensor,
    cos: torch.Tensor,
    sin: torch.Tensor,
    quant_config: dict,
    position_ids: Optional[torch.Tensor] = None,
    unsqueeze_dim: int = 1
) -> tuple[torch.Tensor, torch.Tensor]:
    """Apply Rotary Position Embedding using IEEE minifloat quantization."""
    if quant_config.get("bypass", False):
        quantizer = lambda x: x
    else:
        quantizer = partial(
            minifloat_ieee_quantizer,
            width=quant_config["data_in_width"],
            exponent_width=quant_config["data_in_exponent_width"],
            exponent_bias=quant_config["data_in_exponent_bias_width"],
        )

    return _apply_rope_with_quantizer(q, k, cos, sin, quantizer, unsqueeze_dim)
