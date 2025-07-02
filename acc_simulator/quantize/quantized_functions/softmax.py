from typing import Literal

import torch
from torch import Tensor

from ..quantizer.minifloat import minifloat_ieee_quantizer, MinifloatMeta


def softmax_minifloat(
    input: Tensor,
    x_minifp_meta: MinifloatMeta | None,
    func_type: Literal["X", "Xq"],
    dim: int = -1
) -> Tensor:
    if "Xq" in func_type:
        assert x_minifp_meta is not None
        input = minifloat_ieee_quantizer(input, x_minifp_meta)

    # Numerically stable softmax in float32, then cast back
    return torch.nn.functional.softmax(input.to(torch.float32), dim=dim).to(input.dtype)

