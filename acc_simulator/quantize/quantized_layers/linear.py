from typing import Literal, Union

import torch
from torch import Tensor, nn

from mase_triton.mxfp.functional import quantize_dequantize as mxfp_quantizer_sim
from ..quantizer.mxfp import MXFPMeta
from ..quantizer.mxint import MXIntMeta
from ..quantizer.mxint import mxint_quantizer_sim
from ..quantizer.int import quantize_dequantize as int_quantizer_sim


class MXFPLinearPTQ(nn.Module):
    in_features: int
    out_features: int

    def __init__(
        self,
        weight: Tensor,
        bias: Tensor | None,
        x_mxfp_meta: MXFPMeta | None,
        w_mx_meta: Union[MXFPMeta, MXIntMeta, None],
        b_mxfp_meta: MXFPMeta | None,
        layer_type: Literal[
            "XWB", "XWBq", "XWqB", "XWqBq", "XqWB", "XqWBq", "XqWqB", "XqWqBq"
        ]
    ):
        super().__init__()
        assert weight.ndim == 2
        assert bias is None or bias.ndim == 1
        assert bias is None or bias.shape[0] == weight.shape[0]

        in_features, out_features = weight.shape[1], weight.shape[0]
        self.in_features = in_features
        self.out_features = out_features
        self.x_mxfp_meta = x_mxfp_meta
        self.w_mx_meta = w_mx_meta
        self.b_mxfp_meta = b_mxfp_meta
        self.layer_type = layer_type

        self.weight = None
        self.bias = None

        if "Wq" in self.layer_type:
            self.weight = mxint_quantizer_sim(weight, block_dim=1, mxint_meta=w_mx_meta)
            # self.weight = int_quantizer_sim(weight)
            # self.weight = mxfp_quantizer_sim(weight, block_dim=1, mxfp_meta=w_mx_meta)
        else:
            self.weight = nn.Parameter(weight, requires_grad=False)

        if "Bq" in self.layer_type:
            if isinstance(bias, Tensor):
                self.bias = mxfp_quantizer_sim(bias, block_dim=0, mxfp_meta=b_mxfp_meta)
        else:
            if bias is not None:
                self.bias = nn.Parameter(bias, requires_grad=False)

    @torch.no_grad()
    def forward(self, input: Tensor) -> Tensor:
        if "Xq" in self.layer_type:
            input = mxfp_quantizer_sim(input, block_dim=-1, mxfp_meta=self.x_mxfp_meta)

        # print(f"[DEBUG] input dtype: {input.dtype}, weight dtype: {self.weight.dtype}, bias dtype: {self.bias.dtype if self.bias is not None else 'None'}")
        return torch.nn.functional.linear(input, self.weight, self.bias)


    def extra_repr(self) -> str:
        return (
            f"in_features={self.in_features}, out_features={self.out_features}, bias={self.bias is not None}, "
            f"layer_type={self.layer_type}, "
            f"w_mx_meta={self.w_mx_meta}, x_mxfp_meta={self.x_mxfp_meta}, "
            f"b_mxfp_meta={self.b_mxfp_meta}"
        )

    @classmethod
    def from_linear(
        cls,
        layer: nn.Linear,
        x_mxfp_meta: MXFPMeta | None,
        w_mx_meta: Union[MXFPMeta, MXIntMeta, None],
        b_mxfp_meta: MXFPMeta | None,
        layer_type: Literal[
            "XWB", "XWBq", "XWqB", "XWqBq", "XqWB", "XqWBq", "XqWqB", "XqWqBq"
        ]
    ):
        """
        Create an MXFPLinearPTQ instance from a PyTorch Linear layer.
        """
        assert isinstance(layer, nn.Linear), "layer must be an instance of nn.Linear"
        with torch.no_grad():
            return cls(
                weight=layer.weight.clone(),
                bias=layer.bias.clone() if layer.bias is not None else None,
                x_mxfp_meta=x_mxfp_meta,
                w_mx_meta=w_mx_meta,
                b_mxfp_meta=b_mxfp_meta,
                layer_type=layer_type
            )