from typing import Literal
import torch
from torch import Tensor, nn

from transformers.models.llama.modeling_llama import LlamaRMSNorm

from ..quantizer.mxint import MXIntMeta, mxint_quantizer_sim
from ..quantizer.minifloat import minifloat_quantizer_sim, MinifloatMeta
from ..utils import quantize_tensor


class FPRMSNormPTQ(nn.Module):
    def __init__(
        self,
        weight: Tensor,
        x_meta: MinifloatMeta | MXIntMeta | None,
        w_meta: MinifloatMeta | MXIntMeta | None,
        layer_type: Literal["XW", "XqW", "XWq", "XqWq"],
        eps: float = 1e-6,
    ):
        super().__init__()
        self.eps = eps
        self.layer_type = layer_type
        self.x_meta = x_meta
        self.w_meta = w_meta

        self.weight = None

        if "Wq" in layer_type:
            self.weight = quantize_tensor(weight, block_dim=-1, meta=w_meta)
        else:
            self.weight = nn.Parameter(weight, requires_grad=False)

    @torch.no_grad()
    def forward(self, x: Tensor) -> Tensor:
        hidden_dtype = x.dtype
        if "Xq" in self.layer_type:
            assert self.x_meta is not None
            x = quantize_tensor(x, block_dim=-1, meta=self.x_meta)
        x = x.to(torch.float32)
        variance = x.pow(2).mean(-1, keepdim=True)
        x = x * torch.rsqrt(variance + self.eps)

        return self.weight * x.to(hidden_dtype)

    def extra_repr(self) -> str:
        return (
            f"eps={self.eps}"
            f"layer_type={self.layer_type}"
            f"x_meta={self.x_meta}, w_meta={self.w_meta}"
        )

    @classmethod
    def from_rmsnorm(
        cls,
        layer: LlamaRMSNorm,
        x_meta: MinifloatMeta | MXIntMeta | None,
        w_meta: MinifloatMeta | MXIntMeta | None,
        layer_type: Literal["XW", "XqW", "XWq", "XqWq"],
    ):
        assert isinstance(layer, LlamaRMSNorm)
        with torch.no_grad():
            return cls(
                weight=layer.weight.clone(),
                eps=getattr(layer, "eps", 1e-6),
                x_meta=x_meta,
                w_meta=w_meta,
                layer_type=layer_type
            )
