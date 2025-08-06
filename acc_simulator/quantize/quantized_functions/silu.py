from typing import Literal

import torch
from torch import Tensor

from ..quantizer.minifloat import minifloat_quantizer_sim, MinifloatMeta
from ..utils import quantize_tensor


def silu_minifloat(
    input: Tensor,
    x_meta: MinifloatMeta | None,
    func_type: Literal["X", "Xq"]
) -> Tensor:
    if func_type =="Xq":
        assert x_meta is not None, "Meta must be provided for 'Xq' input"
        input = quantize_tensor(input, block_dim=-1, meta=x_meta)

    return torch.nn.functional.silu(input)