from typing import Literal

import torch
from torch import Tensor

from ..quantizer.minifloat import MinifloatMeta
from ..quantizer.minifloat.minifloat import minifloat_quantizer_sim


def rotate_half(x: Tensor) -> Tensor:
    """Rotate half the last dimension (for RoPE)."""
    x1 = x[..., : x.shape[-1] // 2]
    x2 = x[..., x.shape[-1] // 2 :]
    return torch.cat((-x2, x1), dim=-1)


def rope_minifloat(
    q: Tensor,
    k: Tensor,
    cos: Tensor,
    sin: Tensor,
    x_minifp_meta: MinifloatMeta | None,
    func_type: Literal["X", "Xq"],
    unsqueeze_dim: int = 1,
) -> tuple[Tensor, Tensor]:
    if func_type == "Xq":
        assert x_minifp_meta is not None, "MinifloatMeta must be provided when quantizing input"
        cos = minifloat_quantizer_sim(cos, block_dim=None, minifloat_meta=x_minifp_meta)
        sin = minifloat_quantizer_sim(sin, block_dim=None, minifloat_meta=x_minifp_meta)

    cos = cos.unsqueeze(unsqueeze_dim)
    sin = sin.unsqueeze(unsqueeze_dim)

    seq_len = q.size(-2)
    cos = cos[..., :seq_len, :]
    sin = sin[..., :seq_len, :]

    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)
    return q_embed, k_embed