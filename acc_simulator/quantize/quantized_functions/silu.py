from typing import Literal

import torch
from torch import Tensor

from ..quantizer.minifloat import minifloat_quantizer_sim, MinifloatMeta


def silu_minifloat(
    input: Tensor,
    x_minifp_meta: MinifloatMeta | None,
    func_type: Literal["X", "Xq"]
) -> Tensor:
    if func_type =="Xq":
        assert x_minifp_meta is not None, "MinifloatMeta must be provided for 'Xq' input"
        input = minifloat_quantizer_sim(input, x_minifp_meta)

    return torch.nn.functional.silu(input)