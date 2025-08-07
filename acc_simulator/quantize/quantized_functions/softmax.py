from typing import Literal

import torch
from torch import Tensor

from ..quantizer.minifloat import MinifloatMeta
from ..utils import quantize_tensor


def softmax_minifloat(
    input: Tensor,
    x_meta: MinifloatMeta | None,
    func_type: Literal["X", "Xq"],
    dim: int = -1
) -> Tensor:
    if "Xq" in func_type:
        assert x_meta is not None
        input = quantize_tensor(input, block_dim=-1, meta=x_meta)

    # Numerically stable softmax in float32, then cast back
    return torch.nn.functional.softmax(input.to(torch.float32), dim=dim).to(input.dtype)

