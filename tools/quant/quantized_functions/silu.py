import torch.nn.functional as F
from functools import partial

from ..quantizer import minifloat_ieee_quantizer

def silu_minifloat_ieee(x, quant_config=None):
    bypass = quant_config.get("bypass", False)
    if bypass:
        return F.silu(x)
    else:
        x_width = quant_config["data_in_width"]
        x_exponent_width = quant_config["data_in_exponent_width"]
        x_exponent_bias = quant_config["data_in_exponent_bias_width"]

        x_quantizer = partial(
            minifloat_ieee_quantizer,
            width=x_width,
            exponent_width=x_exponent_width,
            exponent_bias=x_exponent_bias,
        )

        return F.silu(x_quantizer(x))
