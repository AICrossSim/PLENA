from typing import Literal

import torch
from torch import Tensor
from functools import partial

from ..quantizer.minifloat import MinifloatMeta
from ..quantizer.minifloat.minifloat import minifloat_quantizer_sim

def reciprocal_approx(x: Tensor, quantizer) -> Tensor:
    reciprocal = 1 / (x+1e-9)
    reciprocal = quantizer(reciprocal)
    return reciprocal

def tayor_exp(x: torch.Tensor, quantizer):
    """
    Taylor series expansion of 2^x for testing
    """
    def range_reduction(x: torch.Tensor):
        """
        Range reduction of x
        """
        MLOG2_E = torch.tensor(92/2**7)
        ELOG2_E = 1
        new_mx = x * MLOG2_E * 2
        new_mx = new_mx.clamp(min=-512, max=512)
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
    taylor_result = taylor_result * 2**integ
    taylor_result = quantizer(taylor_result)
    if torch.isnan(taylor_result).any():
        print("taylor_result is nan")
        breakpoint() 
    return taylor_result

def softmax_approx(x: Tensor, quantizer, dim: int = -1) -> Tensor:
    x_max = x.max(dim=dim, keepdim=True).values
    # x_exp = tayor_exp(x-x_max, quantizer)
    x_exp = torch.exp(x-x_max)
    x_exp = quantizer(x_exp)

    x_exp_sum = x_exp.sum(dim=dim, keepdim=True)
    x_exp_sum = quantizer(x_exp_sum)

    reciprocal = reciprocal_approx(x_exp_sum, quantizer)
    result = x_exp * reciprocal
    if torch.isnan(result).any():
        print("softmax is nan")
        breakpoint() 
    return result

def silu_approx(x: Tensor, quantizer) -> Tensor:
    x_exp = torch.exp(-x)
    x_exp = quantizer(x_exp)
    reciprocal = reciprocal_approx(1 + x_exp, quantizer)
    result = x * reciprocal
    if torch.isnan(result).any():
        print("silu is nan")
        breakpoint()
    return result

def sqrt_newton(x, quantizer, iters=5):
    x = x.float()
    y = x  # 初始猜测值
    for _ in range(iters):
        intermediate = reciprocal_approx(y, quantizer)
        y = 0.5 * (y + x * intermediate)
    return y

def _get_similarity(tensor_raw, tensor_sim, metric=None):
    if metric == "cosine":
        similarity = F.cosine_similarity(tensor_raw, tensor_sim, dim=-1)
    elif metric == "pearson":
        similarity = F.cosine_similarity(
            tensor_raw - torch.mean(tensor_raw, dim=-1, keepdim=True),
            tensor_sim - torch.mean(tensor_sim, dim=-1, keepdim=True),
            dim=-1,
        )
    else:
        if metric == "L1_norm":
            similarity = -torch.abs(tensor_raw - tensor_sim)
        elif metric == "L2_norm" or "l2norm" or "l2":
            similarity = -((tensor_raw - tensor_sim) ** 2)
        elif metric == "linear_weighted_L2_norm":
            similarity = -tensor_raw.abs() * (tensor_raw - tensor_sim) ** 2
        elif metric == "square_weighted_L2_norm":
            similarity = -((tensor_raw * (tensor_raw - tensor_sim)) ** 2)
        else:
            raise NotImplementedError(f"metric {metric} not implemented!")
        similarity = torch.mean(similarity, dim=-1)
    return similarity

def rms_norm_approx(x: Tensor, quantizer, eps: float = 1e-6) -> Tensor:
    variance = x.pow(2)
    variance = quantizer(variance)
    variance = variance.mean(-1, keepdim=True)
    variance = quantizer(variance)
    # variance = variance + eps
    # sqrt = sqrt_newton(variance, quantizer, iters=10)
    sqrt = torch.sqrt(variance + eps)
    sqrt = quantizer(sqrt)

    reciprocal_sqrt = reciprocal_approx(sqrt, quantizer)
    if torch.isnan(reciprocal_sqrt*x).any():
        breakpoint() 
    return x * reciprocal_sqrt