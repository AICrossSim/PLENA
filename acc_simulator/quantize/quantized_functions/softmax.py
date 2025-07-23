from typing import Literal

import torch
from torch import Tensor

from mase_triton.minifloat.functional import quantize_dequantize as minifloat_quantizer_sim
from ..quantizer.minifloat import MinifloatMeta


def softmax_minifloat(
    input: Tensor,
    x_minifp_meta: MinifloatMeta | None,
    func_type: Literal["X", "Xq"],
    dim: int = -1
) -> Tensor:
    if "Xq" in func_type:
        assert x_minifp_meta is not None
        input = minifloat_quantizer_sim(input, x_minifp_meta)

    # Numerically stable softmax in float32, then cast back
    return torch.nn.functional.softmax(input.to(torch.float32), dim=dim).to(input.dtype)

