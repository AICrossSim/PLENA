from functools import partial

import torch
import torch.nn as nn
import torch.nn.functional as F 

from ..quantizer import mxfp_quantizer, minifloat_ieee_quantizer, mx_int_quantizer

class _LinearBase(nn.Linear):
    def __init__(
        self,
        in_features: int,
        out_features: int,
        bias: bool = True,
        device=None,
        dtype=None,
        config: dict = None,
    ) -> None:
        super().__init__(in_features, out_features, bias=bias, device=device, dtype=dtype)

        self.config = config
        self.bypass = config.get("bypass", False)
        self.is_ptq = config.get("is_ptq", False)
        self.weight_requires_quantisation = True if self.is_ptq else False
        self.x_quantizer = None
        self.w_quantizer = None
        self.b_quantizer = None

        if not self.bypass:
            self._setup_quantizers(config)


    def _setup_quantizers(self, config: dict):
        """
        Setup quantizers for input, weight and bias
        """
        raise NotImplementedError

    def forward(self, x):
        if self.bypass:
            # if bypss, there is no quantization
            return F.linear(x, self.weight, self.bias)
        elif self.is_ptq:
            with torch.no_grad():
                x = self.x_quantizer(x)
                if self.weight_requires_quantisation:
                    self.weight.copy_(self.w_quantizer(self.weight.data))
                    if self.bias is not None:
                        self.bias.copy_(self.b_quantizer(self.bias.data))
                    self.weight_requires_quantisation = False
            return F.linear(x, self.weight, self.bias)
        else:
            x = self.x_quantizer(x)
            w = self.w_quantizer(self.weight)
            bias = self.b_quantizer(self.bias) if self.bias is not None else None
            return F.linear(x, w, bias)


    def __repr__(self):
        txt = "{}(in_features={}, out_features={}, bias={}, bypass={}, is_ptq={}, x/w/b-width={}/{}/{})".format(
            self.__class__.__name__,
            self.in_features,
            self.out_features,
            self.bias is not None,
            self.bypass,
            self.is_ptq,
            self.config["data_in_width"],
            self.config["weight_width"],
            self.config.get("bias_width", "NA"),
        )
        return txt

class LinearMXFP(_LinearBase):
    def _setup_quantizers(self, config: dict):
        self.x_quantizer = partial(
            mxfp_quantizer,
            width=config["data_in_width"],
            exponent_width=config["data_in_exponent_width"],
            exponent_bias_width=config["data_in_exponent_bias_width"],
            block_size=config["data_in_block_size"],
            skip_first_dim=True,
        )
        self.w_quantizer = partial(
            mxfp_quantizer,
            width=config["weight_width"],
            exponent_width=config["weight_exponent_width"],
            exponent_bias_width=config["weight_exponent_bias_width"],
            block_size=config["weight_block_size"],
            skip_first_dim=False,
        )
        self.b_quantizer = (
            partial(
                mxfp_quantizer,
                width=config["bias_width"],
                exponent_width=config["bias_exponent_width"],
                exponent_bias_width=config["bias_exponent_bias_width"],
                block_size=config["bias_block_size"],
                skip_first_dim=False,
            )
            if self.bias is not None
            else None
        )

        
class LinearMinifloatIEEE(_LinearBase):
    def _setup_quantizers(self, config: dict):
        self.x_quantizer = partial(
            minifloat_ieee_quantizer,
            width=config["data_in_width"],
            exponent_width=config["data_in_exponent_width"],
            exponent_bias=config["data_in_exponent_bias_width"],
        )
        self.w_quantizer = partial(
            minifloat_ieee_quantizer,
            width=config["weight_width"],
            exponent_width=config["weight_exponent_width"],
            exponent_bias=config["data_in_exponent_bias_width"],
        )
        self.b_quantizer = (
            partial(
                minifloat_ieee_quantizer,
                width=config["bias_width"],
                exponent_width=config["bias_exponent_width"],
                exponent_bias=config["data_in_exponent_bias_width"],
            )
            if self.bias is not None
            else None
        )

class LinearMXINT(_LinearBase):
    def _setup_quantizers(self, config: dict):
        self.x_quantizer = partial(
            mx_int_quantizer,
            width=config["data_in_width"],
            exponent_width=config["data_in_exponent_width"],
            exponent_bias=config["data_in_exponent_bias_width"],
            block_size=config["data_in_block_size"],
            skip_first_dim=True,
        )
        self.w_quantizer = partial(
            mx_int_quantizer,
            width=config["weight_width"],
            exponent_width=config["weight_exponent_width"],
            exponent_bias=config["weight_exponent_bias_width"],
            block_size=config["weight_block_size"],
            skip_first_dim=False,
        )
        self.b_quantizer = (
            partial(
                mx_int_quantizer,
                width=config["bias_width"],
                exponent_width=config["bias_exponent_width"],
                exponent_bias=config["bias_exponent_bias_width"],
                block_size=config["bias_block_size"],
                skip_first_dim=False,
            )
            if self.bias is not None
            else None
        )
