import torch
from torch import Tensor

from .utils import my_clamp, my_round


def _minifloat_denorm_quantize_hardware(
    x: Tensor,
    width: int,
    exponent_width: int,
    exponent_bias: int = None,
):
    """
    - Converts IEEE FP32/64 to minifloat without the implicit leading bit in mantissas.
    - No representation for +/-inf or NaN. Large IEEE FP32/64 values will saturate.

    ---
    - forward: convert IEEE FP32/64 to minifloat (mantissa has no implicit leading bit)
    - backward: STE

    ---
    width: the bit width of minifloat
    exponent_width: the number of exponent bits in the minifloat
    exponent_bias: the value of the exponent bias. If None, the default bias will be (2**exponent_bits - 1) >> 1.

    ---
    For example:
    a minifloat(bits=8, exponent_bits=4, mantissa_bits=3) number,
    1 0111 011, is equal to (-1)**1 * 2**(7-15) * (3/8) = -0.00146484375

    ---
    Tested extreme values: large values to saturate, small values close to zero (precision), and 0
    """
    mantissa_bits = width - exponent_width - 1

    # default bias value
    if exponent_bias in (None, "none", "None"):
        exponent_bias = 2 ** (exponent_width - 1) - 1

    exponent_max = 2**exponent_width - 1 - exponent_bias
    exponent_min = -exponent_bias
    # if the mantissa is an integer, the max mantissa value will be (2**mantissa_bits -1)
    shifted_mantissa_max = 2**mantissa_bits - 1
    shifted_mantissa_min = 0

    sign = torch.sign(x + 1e-9)

    value = torch.abs(x)
    # ceiling ensures mantissa in the range of [0, 1)
    exponent = torch.ceil(torch.log2(value + 1e-9))
    exponent = my_clamp(exponent, exponent_min, exponent_max)

    # divide value by clipped exponent. this ensures the simulated minifloat value is correct
    # when x is too large (minifloat will saturate) or too close to 0.
    mantissa = value / 2**exponent
    shift = 2**mantissa_bits
    shifted_mantissa = my_round(mantissa * shift)
    # clip the integer mantissa.
    shifted_mantissa = my_clamp(
        shifted_mantissa, shifted_mantissa_min, shifted_mantissa_max
    )
    mantissa = shifted_mantissa / shift
    # fmt: off
    # this `is_close_to_0` helps the grad keeps 1 if input x is 0, or the zero-initialized value will be trapped in 0
    is_close_to_0 = torch.isclose(value, torch.tensor([0.0], dtype=value.dtype, device=value.device))
    minifloat_denorm_x = (~is_close_to_0)*(sign*(2**exponent)*mantissa) + is_close_to_0*x
    # fmt: on
    return minifloat_denorm_x, exponent, sign * mantissa