from typing import Literal

import torch
from torch import Tensor

from ..quantizer.minifloat import MinifloatMeta
from ..quantizer.mxint import MXIntMeta
from ..quantizer.mxfp import MXFPMeta
from ..utils import quantize_tensor


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
    x_meta: MinifloatMeta | MXFPMeta | MXIntMeta | None,
    func_type: Literal["X", "Xq"],
    unsqueeze_dim: int = 1,
) -> tuple[Tensor, Tensor]:
    if func_type == "Xq":
        assert x_meta is not None, "Meta must be provided when quantizing input"
        cos = quantize_tensor(cos, block_dim=-1, meta=x_meta)
        sin = quantize_tensor(sin, block_dim=-1, meta=x_meta)

    cos = cos.unsqueeze(unsqueeze_dim)
    sin = sin.unsqueeze(unsqueeze_dim)

    seq_len = q.size(-2)
    cos = cos[..., :seq_len, :]
    sin = sin[..., :seq_len, :]

    q_embed = (q * cos) + (rotate_half(q) * sin)
    k_embed = (k * cos) + (rotate_half(k) * sin)
    return q_embed, k_embed