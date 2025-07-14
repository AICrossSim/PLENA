from typing import Literal

import torch
from torch import Tensor
from functools import partial

from ..quantizer.minifloat import minifloat_ieee_quantizer, MinifloatMeta, FP10_E6M3
from .hardware_aware_operations import softmax_approx

def softmax_minifloat(
    input: Tensor,
    x_minifp_meta: MinifloatMeta | None,
    func_type: Literal["X", "Xq"],
    dim: int = -1
) -> Tensor:
    if "Xq" in func_type:
        assert x_minifp_meta is not None
        quantizer = partial(minifloat_ieee_quantizer, meta=x_minifp_meta)
        input = quantizer(input)
        return softmax_approx(input, quantizer, dim=dim)

    return torch.nn.functional.softmax(input, dim=dim)
