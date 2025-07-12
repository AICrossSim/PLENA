from typing import Literal

import torch
from torch import Tensor
from functools import partial

from ..quantizer.minifloat import minifloat_ieee_quantizer, MinifloatMeta

def reciprocal_approx(x: Tensor, quantizer) -> Tensor:
    reciprocal = 1 / (x+1e-6)
    reciprocal = quantizer(reciprocal)
    return reciprocal

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
    taylor_result[torch.where(x == torch.tensor(-float("inf")))] = 0.0
    return taylor_result * 2**integ

def softmax_approx(x: Tensor, quantizer, dim: int = -1) -> Tensor:
    x_max = x.max(dim=dim, keepdim=True).values
    x_exp = tayor_exp(x-x_max)
    x_exp = quantizer(x_exp)
    x_exp_sum = x_exp.sum(dim=dim, keepdim=True)
    x_exp_sum = quantizer(x_exp_sum)
    reciprocal = reciprocal_approx(x_exp_sum, quantizer)
    return x_exp * reciprocal

def silu_approx(x: Tensor, quantizer) -> Tensor:
    x_exp = tayor_exp(-x)
    x_exp = quantizer(x_exp)
    reciprocal = reciprocal_approx(1 + x_exp, quantizer)
    return x * reciprocal

def sqrt_newton(x, quantizer, iters=5):
    x = x.float()
    y = x  # 初始猜测值
    for _ in range(10):
        intermediate = reciprocal_approx(y, quantizer)
        y = 0.5 * (y + intermediate)
    return y


def rms_norm_approx(x: Tensor, quantizer, eps: float = 1e-6) -> Tensor:
    variance = x.pow(2)
    variance = quantizer(variance)
    variance = variance.mean(-1, keepdim=True)
    variance = quantizer(variance)
    variance = variance + eps
    sqrt = sqrt_newton(variance, quantizer, iters=10)
    sqrt = quantizer(sqrt)
    sqrt = reciprocal_approx(sqrt, quantizer)
    return x * sqrt