from typing import Literal

import torch
from torch import Tensor
from functools import partial

from ..quantizer.minifloat import minifloat_ieee_quantizer, MinifloatMeta

def tayor_exp(x: torch.Tensor):
    """
    Taylor series expansion of 2^x for testing
    """
    def range_reduction(x: torch.Tensor):
        """
        Range reduction of x
        """
        MLOG2_E = 92/2**7
        ELOG2_E = 1
        new_mx = x * MLOG2_E * 2
        integ = new_mx.floor()
        frac = new_mx - integ
        return frac, integ

    def taylor_series(frac: torch.Tensor):
        """
        Taylor series expansion of 2^x for testing
        """
        ln2 = 22/2**5
        term0 = 1.0
        term1 = frac * ln2
        term2 = term1 * term1 / 2
        term3 = term2 * term1 / 3
        return term0 + term1 + term2 + term3


    frac, integ = range_reduction(x)
    taylor_result = taylor_series(frac)
    taylor_result[torch.where(x == torch.tensor(-float("inf")))] = 1.0
    return taylor_result * 2**integ

def softmax_approx(x: Tensor, quantizer, dim: int = -1) -> Tensor:
    x_max = x.max(dim=dim, keepdim=True).values
    x_exp = tayor_exp(x-x_max)
    x_exp = quantizer(x_exp)
    x_exp_sum = x_exp.sum(dim=dim, keepdim=True)
    x_exp_sum = quantizer(x_exp_sum)
    reciprocal = 1 / x_exp_sum
    reciprocal = quantizer(reciprocal)
    return x_exp * reciprocal

def softmax_minifloat(
    input: Tensor,
    x_minifp_meta: MinifloatMeta | None,
    func_type: Literal["X", "Xq"],
    dim: int = -1
) -> Tensor:
    quantizer = partial(minifloat_ieee_quantizer, meta=x_minifp_meta)
    if "Xq" in func_type:
        assert x_minifp_meta is not None
        input = quantizer(input)
        return softmax_approx(input, quantizer, dim=dim)

    return torch.nn.functional.softmax(input, dim=dim)

