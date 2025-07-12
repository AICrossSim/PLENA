from typing import Literal
import torch
from torch import Tensor, nn
from functools import partial

from transformers.models.llama.modeling_llama import LlamaRMSNorm

from ..quantizer.minifloat import MinifloatMeta, minifloat_ieee_quantizer

def sqrt_newton(x, iters=5):
    x = x.float()
    y = x  # 初始猜测值
    for _ in range(10):
        intermediate = x / y
        intermediate = minifloat_ieee_quantizer(intermediate, MinifloatMeta(element_exp_bits=8, element_frac_bits=7))
        y = 0.5 * (y + intermediate)
    return y

def rms_norm_approx(x: Tensor, quantizer, eps: float = 1e-6) -> Tensor:
    variance = x.pow(2)
    variance = quantizer(variance)
    variance = variance.mean(-1, keepdim=True)
    variance = quantizer(variance)
    variance = variance + eps
    sqrt = sqrt_newton(variance, iters=10)
    sqrt = quantizer(sqrt)
    sqrt = 1 / sqrt
    sqrt = quantizer(sqrt)
    return x * sqrt

class FPRMSNormPTQ(nn.Module):
    def __init__(
        self,
        weight: Tensor,
        x_minifp_meta: MinifloatMeta | None,
        w_minifp_meta: MinifloatMeta | None,
        layer_type: Literal["XW", "XqW", "XWq", "XqWq"],
        eps: float = 1e-6,
    ):
        super().__init__()
        self.eps = eps
        self.layer_type = layer_type
        self.x_minifp_meta = x_minifp_meta
        self.w_minifp_meta = w_minifp_meta

        self.weight = None

        if "Wq" in layer_type:
            self.weight = minifloat_ieee_quantizer(weight, self.w_minifp_meta)
        else:
            self.weight = nn.Parameter(weight, requires_grad=False)

    @torch.no_grad()
    def forward(self, x: Tensor) -> Tensor:
        hidden_dtype = x.dtype
        if "Xq" in self.layer_type:
            assert self.x_minifp_meta is not None
            quantizer = partial(minifloat_ieee_quantizer, meta=self.x_minifp_meta)
            x = quantizer(x)
            x = rms_norm_approx(x, quantizer, self.eps)
            return self.weight * x.to(hidden_dtype)

        x = x.to(torch.float32)
        variance = x.pow(2).mean(-1, keepdim=True)
        x = x * torch.rsqrt(variance + self.eps)

        return self.weight * x.to(hidden_dtype)

    def extra_repr(self) -> str:
        return (
            f"eps={self.eps}"
            f"layer_type={self.layer_type}"
            f"x_minifp_meta={self.x_minifp_meta}, w_minifp_meta={self.w_minifp_meta}"
        )

    @classmethod
    def from_rmsnorm(
        cls,
        layer: LlamaRMSNorm,
        x_minifp_meta: MinifloatMeta | None,
        w_minifp_meta: MinifloatMeta | None,
        layer_type: Literal["XW", "XqW", "XWq", "XqWq"],
    ):
        assert isinstance(layer, LlamaRMSNorm)
        with torch.no_grad():
            return cls(
                weight=layer.weight.clone(),
                eps=getattr(layer, "eps", 1e-6),
                x_minifp_meta=x_minifp_meta,
                w_minifp_meta=w_minifp_meta,
                layer_type=layer_type
            )
