from typing import Literal

import torch
from torch import Tensor
from functools import partial

from ..quantizer.minifloat import MinifloatMeta
from ..quantizer.minifloat.minifloat import minifloat_quantizer_sim
from .hardware_aware_operations import softmax_approx

def softmax_minifloat(
    input: Tensor,
    x_minifp_meta: MinifloatMeta | None,
    func_type: Literal["X", "Xq"],
    dim: int = -1
) -> Tensor:
    if "Xq" in func_type:
        assert x_minifp_meta is not None
        quantizer = partial(minifloat_quantizer_sim, block_dim=None, minifloat_meta=x_minifp_meta)
        input = quantizer(input)
        return softmax_approx(input, quantizer, dim=dim)

    return torch.nn.functional.softmax(input, dim=dim)
