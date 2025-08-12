from typing import Literal, Union

import torch
from torch import Tensor, nn

from ..quantizer.mxfp import MXFPMeta, mxfp_quantizer_sim
from ..quantizer.mxint import MXIntMeta, mxint_quantizer_sim
from ..quantizer.minifloat import MinifloatMeta, minifloat_quantizer_sim
from ..utils import quantize_tensor
from ...rotation.hadamard import OnlineHadamardQuantization

class MXFPLinearPTQ(nn.Module):
    in_features: int
    out_features: int

    def __init__(
        self,
        weight: Tensor,
        bias: Tensor | None,
        x_meta: MXFPMeta | MXIntMeta | None,
        w_meta: Union[MXFPMeta, MXIntMeta, None],
        b_meta: MXFPMeta | MXIntMeta | None,
        layer_type: Literal[
            "XWB", "XWBq", "XWqB", "XWqBq", "XqWB", "XqWBq", "XqWqB", "XqWqBq"
        ],
        w_pre_quantized: bool = False,
        online_rotate: bool = False,
    ):
        super().__init__()
        assert weight.ndim == 2
        assert bias is None or bias.ndim == 1
        assert bias is None or bias.shape[0] == weight.shape[0]

        in_features, out_features = weight.shape[1], weight.shape[0]
        self.in_features = in_features
        self.out_features = out_features
        self.x_meta = x_meta
        self.w_meta = w_meta
        self.b_meta = b_meta
        self.layer_type = layer_type
        self.w_pre_quantized = w_pre_quantized
        self.online_rotate = online_rotate

        self.weight = None
        self.bias = None

        if "Wq" in self.layer_type and not w_pre_quantized:
            self.weight = quantize_tensor(weight, block_dim=1, meta=w_meta, quantile_search=False)
        else:
            self.weight = nn.Parameter(weight, requires_grad=False)

        if "Bq" in self.layer_type:
            if isinstance(bias, Tensor):
                self.bias = quantize_tensor(bias, block_dim=0, meta=b_meta, quantile_search=False)
        else:
            if bias is not None:
                self.bias = nn.Parameter(bias, requires_grad=False)
        
        self.online_rotate_quant = None
        if self.online_rotate:
            self.online_rotate_quant = OnlineHadamardQuantization(in_features, block_dim=-1, meta=self.x_meta)

    @torch.no_grad()
    def forward(self, input: Tensor) -> Tensor:
        if "Xq" in self.layer_type:
            if self.online_rotate_quant is not None:
                input = self.online_rotate_quant(input)
            else:
                input = quantize_tensor(input, block_dim=-1, meta=self.x_meta)

        # print(f"[DEBUG] input dtype: {input.dtype}, weight dtype: {self.weight.dtype}, bias dtype: {self.bias.dtype if self.bias is not None else 'None'}")
        return torch.nn.functional.linear(input, self.weight, self.bias)


    def extra_repr(self) -> str:
        return (
            f"in_features={self.in_features}, out_features={self.out_features}, bias={self.bias is not None}, "
            f"layer_type={self.layer_type}, "
            f"w_meta={self.w_meta}, x_meta={self.x_meta}, "
            f"b_meta={self.b_meta}"
        )

    @classmethod
    def from_linear(
        cls,
        layer: nn.Linear,
        x_meta: MXFPMeta | MXIntMeta | None,
        w_meta: MXFPMeta | MXIntMeta | None,
        b_meta: MXFPMeta | MXIntMeta | None,
        layer_type: Literal[
            "XWB", "XWBq", "XWqB", "XWqBq", "XqWB", "XqWBq", "XqWqB", "XqWqBq"
        ],
        online_rotate: bool,
        clip_search_y: bool = False,
    ):
        """
        Create an MXFPLinearPTQ instance from a PyTorch Linear layer.
        """
        assert isinstance(layer, nn.Linear), "layer must be an instance of nn.Linear"
        with torch.no_grad():
            return cls(
                weight=layer.weight.clone(),
                bias=layer.bias.clone() if layer.bias is not None else None,
                x_meta=x_meta,
                w_meta=w_meta,
                b_meta=b_meta,
                layer_type=layer_type,
                online_rotate=online_rotate
            )
    
    @classmethod
    def from_quantized(
        cls,
        layer: nn.Linear,
        weight_q: Tensor,
        x_meta: MXFPMeta | MXIntMeta | None,
        w_meta: MXFPMeta | MXIntMeta | None,
        b_meta: MXFPMeta | MXIntMeta | None,
        layer_type: Literal[
            "XWB", "XWBq", "XWqB", "XWqBq", "XqWB", "XqWBq", "XqWqB", "XqWqBq"
        ],
        online_rotate: bool
    ):
        """
        Create an MXFPLinearPTQ instance from a PyTorch Linear layer.
        Takes in pre-quantized weights, e.g., from GPTQ.
        """
        assert isinstance(layer, nn.Linear), "layer must be an instance of nn.Linear"
        with torch.no_grad():
            return cls(
                weight=weight_q,
                bias=layer.bias.clone() if layer.bias is not None else None,                               
                x_meta=x_meta,
                w_meta=w_meta,                           
                b_meta=b_meta,
                layer_type=layer_type,
                w_pre_quantized=True,
                online_rotate=online_rotate
            )
