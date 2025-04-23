
import torch

def binarize_torch_fp_conversion(val, config):
    """Convert Python float to custom binary FP format: {sign, exp, mant}"""
    sign = torch.sign(val)

    exp_width = config["exp_width"]
    man_width = config["man_width"]
    # Get raw exponent and mantissa
    exponent = val.abs().log2().floor()
    mantissa_val = val / (2 ** exponent) - 1.0  # remove leading 1

    # Bias the exponent
    bias = (2**(exp_width - 1)) - 1
    exponent_bits = exponent + bias

    # Check if any exponent is out of range
    out_of_range_low = (exponent_bits < 0)
    out_of_range_high = (exponent_bits >= 2**(exp_width))
    if out_of_range_low.any() or out_of_range_high.any():
        raise ValueError("Exponent out of range!")
    # Mantissa
    mantissa_bits = (mantissa_val * 2**man_width).floor()

    # Pack into integer: {sign, exp, mant}
    result = ((sign * 2**(exp_width + man_width)) + 
            exponent_bits * 2**(man_width) + 
            mantissa_bits).int()
    return result