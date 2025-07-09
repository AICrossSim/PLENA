from quant.quantizer import integer
from sympy import Q
import torch
from torch import Tensor
import math

from quant.quantizer.hardware_quantizer.utils import fixed_point_cast
from torch._refs import to
from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware


def fp_exp(signed_exponent_in: torch.Tensor, signed_mantissa_in: torch.Tensor, config: dict):
    """
    Hardware-compatible exponential function implementation.
    
    Algorithm: exp(x) = 2^t where t = log2(e) * x
    Steps:
    1. Calculate t = log2(e) * x 
    2. Split t into integer i and fractional part f
    3. Calculate 2^i (affects exponent)
    4. Calculate 2^f using Taylor series: 1 + ln(2)*f + ln²(2)*f²/2! + ln³(2)*f³/3! + ...
    5. Combine results: 2^i * 2^f
    """
    # Get configuration parameters
    in_fix_frac_width = config["in_fix_frac_width"]
    out_exp_width = config["out_exp_width"]
    out_fix_width = config["out_fix_width"]
    out_frac_width = config["out_fix_frac_width"]

    # Convert input to floating point value
    input_value = signed_mantissa_in * (2.0 ** signed_exponent_in)
    
    # Step 1: Calculate t = log2(e) * x
    LOG2_E = math.log2(math.e)  # ≈ 1.44269504089
    t = LOG2_E * input_value
    
    # Step 2: Split t into integer and fractional parts
    t_integer = torch.floor(t).long()
    t_fraction = t - t_integer.float()
    
    # Step 3: Integer part becomes part of output exponent
    result_exp_offset = t_integer
    
    # Step 4: Calculate 2^f using Taylor series expansion
    # 2^f ≈ 1 + ln(2)*f + ln²(2)*f²/2! + ln³(2)*f³/3! + ln⁴(2)*f⁴/4!
    LN2 = math.log(2.0)  # ≈ 0.693147180559945
    
    # Taylor series terms
    f = t_fraction
    term1 = LN2 * f
    term2 = (LN2 * f) ** 2 / 2.0
    term3 = (LN2 * f) ** 3 / 6.0  
    term4 = (LN2 * f) ** 4 / 24.0
    
    # Sum Taylor series: 2^f ≈ 1 + term1 + term2 + term3 + term4
    mantissa_factor = 1.0 + term1 + term2 + term3 + term4
    
    # Step 5: Combine results
    result_mantissa = mantissa_factor
    result_exponent = result_exp_offset
    
    # Handle edge cases
    # Very negative inputs should approach 0
    underflow_mask = input_value < -10.0
    result_mantissa = torch.where(underflow_mask, torch.zeros_like(result_mantissa), result_mantissa)
    result_exponent = torch.where(underflow_mask, torch.full_like(result_exponent, -127), result_exponent)
    
    # Very positive inputs might overflow
    overflow_mask = input_value > 10.0
    result_mantissa = torch.where(overflow_mask, torch.ones_like(result_mantissa) * 1.999, result_mantissa)
    result_exponent = torch.where(overflow_mask, torch.full_like(result_exponent, 127), result_exponent)
    
    # Normalize mantissa to [1.0, 2.0) range
    while torch.any(result_mantissa >= 2.0):
        mask = result_mantissa >= 2.0
        result_mantissa = torch.where(mask, result_mantissa / 2.0, result_mantissa)
        result_exponent = torch.where(mask, result_exponent + 1, result_exponent)
    
    while torch.any((result_mantissa < 1.0) & (result_mantissa > 0.0)):
        mask = (result_mantissa < 1.0) & (result_mantissa > 0.0)
        result_mantissa = torch.where(mask, result_mantissa * 2.0, result_mantissa)
        result_exponent = torch.where(mask, result_exponent - 1, result_exponent)
    
    # Clamp exponent to valid range
    exp_min = -(2**(out_exp_width - 1) - 1)
    exp_max = 2**(out_exp_width - 1) - 1
    clamped_exp = torch.clamp(result_exponent, min=exp_min, max=exp_max)
    
    # Adjust mantissa if exponent was clamped
    exp_diff = result_exponent - clamped_exp
    adjusted_mantissa = result_mantissa * (2.0 ** exp_diff.float())
    
    # Convert to fixed-point representation
    mantissa_int = (adjusted_mantissa * (2 ** out_frac_width)).round()
    mantissa_max = 2**(out_fix_width - 1) - 1
    mantissa_min = -(2**(out_fix_width - 1))
    
    clamped_mantissa_int = torch.clamp(mantissa_int, min=mantissa_min, max=mantissa_max)
    output_mantissa = clamped_mantissa_int / (2 ** out_frac_width)
    
    return clamped_exp, output_mantissa

def test_exp():
    """Test exponential function with simple cases."""
    config = {
        "in_exp_width": 4,
        "in_fix_width": 5,
        "in_fix_frac_width": 3,
        "out_exp_width": 4,
        "out_fix_width": 6,
        "out_fix_frac_width": 4,
    }
    
    # Test cases: [0, 1, -1, 2, 0.5, -0.5]
    inputs = torch.tensor([0.0, 1.0, -1.0, 2.0, 0.5, -0.5])
    
    # Quantize inputs
    qdata_in, exp_in, mant_in = _minifloat_ieee_quantize_hardware(
        inputs, 
        config["in_fix_frac_width"] + config["in_exp_width"] + 1, 
        config["in_exp_width"]
    )

    # Get hardware results
    hw_exp, hw_mant = fp_exp(torch.as_tensor(exp_in), torch.as_tensor(mant_in), config)
    hw_result = hw_mant * (2 ** hw_exp)

    # Get PyTorch reference
    ref_result = torch.exp(qdata_in)

    # Display results
    print("Exponential Function Test:")
    print(f"{'Input':<8} {'Reference':<12} {'Hardware':<12} {'Error':<10}")
    print("-" * 50)
    
    for i in range(len(qdata_in)):
        error = abs(ref_result[i] - hw_result[i])
        print(f"{qdata_in[i]:<8.2f} {ref_result[i]:<12.6f} {hw_result[i]:<12.6f} {error:<10.6f}")
    
    # Error analysis
    max_error = torch.max(torch.abs(ref_result - hw_result))
    rel_error = torch.abs(ref_result - hw_result) / (torch.abs(ref_result) + 1e-8)
    max_rel_error = torch.max(rel_error)
    
    print(f"\nError Analysis:")
    print(f"Max absolute error: {max_error:.6f}")
    print(f"Max relative error: {max_rel_error:.6f}")
    
    # Basic checks
    exp_0_idx = torch.where(torch.abs(qdata_in) < 0.1)[0]
    if len(exp_0_idx) > 0:
        exp_0_result = hw_result[exp_0_idx[0]]
        assert 0.8 < exp_0_result < 1.2, f"exp(0) = {exp_0_result}, should be ≈ 1"
    
    assert max_rel_error < 0.4, f"Relative error {max_rel_error} too large"
    print("✅ Test passed!")

if __name__ == "__main__":
    test_exp()