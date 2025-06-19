import torch
from torch import Tensor

def fixed_point_cast(
        x: torch.Tensor,
        OUT_WIDTH: int,
        OUT_FRAC_WIDTH: int,
        floor: bool = True,
):
    min_val = -2**(OUT_WIDTH - 1)
    max_val = 2**(OUT_WIDTH) - 1
    if floor:
        x = torch.clamp((x * 2**(OUT_FRAC_WIDTH)).floor(), min_val, max_val)
    else:
        x = torch.clamp((x * 2**(OUT_FRAC_WIDTH)).round(), min_val, max_val)

    x = x / 2**(OUT_FRAC_WIDTH)
    return x

def hardware_round(x: Tensor, round_bits: int = 2):
    x = x * 2**round_bits
    x = torch.floor(x)
    x = x / 2**round_bits
    return x.round()

def pack_fp_to_bin(signed_exponent, signed_mantissa, exp_width, man_width):
    exp_shape = signed_exponent.shape
    man_shape = signed_mantissa.shape
    signed_exponent = signed_exponent.reshape(-1)
    signed_mantissa = signed_mantissa.reshape(-1)

    sign = signed_mantissa.sign()
    sign_bit = torch.where(sign < 0, torch.tensor(1), torch.tensor(0))

    exponent_bias = (2**(exp_width - 1)) - 1
    exponent_bit = signed_exponent + exponent_bias

    for item in exponent_bit:
        assert item >= 0 and item < (2**exp_width - 1), "Exponent out of range!"

    mantissa = torch.where(signed_mantissa < 0, -signed_mantissa, signed_mantissa)
    mantissa_bit = torch.where(exponent_bit == 0, mantissa, mantissa - 1)

    mantissa_bit = mantissa_bit * 2**(man_width)

    result = ((sign_bit * 2**(exp_width + man_width)) + 
            exponent_bit * 2**(man_width) + 
            mantissa_bit).int()
    
    result = result.reshape(exp_shape)

    return result

def fixed_point_cast(
        x: Tensor,
        OUT_WIDTH: int,
        OUT_FRAC_WIDTH: int,
        floor: bool = True,
):
    min_val = -2**(OUT_WIDTH - 1)
    max_val = 2**(OUT_WIDTH) - 1
    if floor:
        x = torch.clamp((x * 2**(OUT_FRAC_WIDTH)).floor(), min_val, max_val)
    else:
        x = torch.clamp((x * 2**(OUT_FRAC_WIDTH)).round(), min_val, max_val)

    x = x / 2**(OUT_FRAC_WIDTH)
    return x