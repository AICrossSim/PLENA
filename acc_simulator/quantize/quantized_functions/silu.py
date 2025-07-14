from typing import Literal

import torch
from torch import Tensor
from functools import partial

from ..quantizer.minifloat import minifloat_ieee_quantizer, MinifloatMeta
from ..quantizer.mxfp import mxfp_quantizer_sim, OCP_MXFP8_E2M5

from .hardware_aware_operations import silu_approx


def silu_minifloat(
    input: Tensor,
    x_minifp_meta: MinifloatMeta | None,
    func_type: Literal["X", "Xq"]
) -> Tensor:
    if func_type =="Xq":
        assert x_minifp_meta is not None, "MinifloatMeta must be provided for 'Xq' input"
        quantizer = partial(minifloat_ieee_quantizer, meta=x_minifp_meta)
        q_input = quantizer(input)
        output = silu_approx(q_input, quantizer)

        return output

    return torch.nn.functional.silu(input)