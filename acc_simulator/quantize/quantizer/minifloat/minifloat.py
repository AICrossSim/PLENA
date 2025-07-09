import torch
from torch import Tensor

from .utils import my_clamp, my_round
from .meta import MinifloatMeta


def _minifloat_ieee_quantize(x: Tensor, meta: MinifloatMeta) -> Tensor:
    exponent_width = meta.element_exp_bits
    mantissa_bits = meta.element_frac_bits
    exponent_bias = meta.exponent_bias

    exponent_max = 2 ** exponent_width - 1 - exponent_bias
    exponent_min = -exponent_bias
    shift = 2 ** mantissa_bits
    shifted_mantissa_max = shift - 1
    shifted_mantissa_min = 0

    sign = torch.sign(x + 1e-9)
    value = torch.abs(x)

    # Calculate exponent and clamp
    exponent = torch.floor(torch.log2(value + 1e-9))
    exponent = my_clamp(exponent, exponent_min, exponent_max)

    mantissa = value / (2 ** exponent)

    if isinstance(exponent_bias, (int, float)):
        exponent_bias = torch.tensor(
            [exponent_bias], dtype=exponent.dtype, device=exponent.device
        )

    is_normal = ~torch.isclose(exponent, -exponent_bias)
    # Shifted mantissa depends on normal/subnormal form
    shifted_mantissa = (
        is_normal
        * my_clamp(my_round(mantissa * shift - shift), shifted_mantissa_min, shifted_mantissa_max)
        + (~is_normal)
        * my_clamp(my_round(mantissa * shift / 2), shifted_mantissa_min, shifted_mantissa_max)
    )

    mantissa = (
        is_normal * (1.0 + shifted_mantissa / shift)
        + (~is_normal) * (shifted_mantissa / shift * 2)
    )

    # Handle x == 0 explicitly to preserve gradient
    is_zero = torch.isclose(value, torch.tensor([0.0], dtype=value.dtype, device=value.device))
    quantized = (~is_zero) * (sign * (2 ** exponent) * mantissa) + is_zero * x
    return quantized


class MinifloatIEEEQuantize(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x: Tensor, meta: MinifloatMeta) -> Tensor:
        return _minifloat_ieee_quantize(x, meta)

    @staticmethod
    def backward(ctx, grad_output: Tensor):
        return grad_output.clone(), None


def minifloat_ieee_quantizer(x: Tensor, meta: MinifloatMeta) -> Tensor:
    return MinifloatIEEEQuantize.apply(x, meta)
