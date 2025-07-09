#!/usr/bin/env python3

# This script tests the fixed point exponential function
import logging, pdb, sys, traceback

from mpmath import ln2, taylor
import torch, math
import numpy as np

from pathlib import Path

import cocotb
from cocotb.log import SimLog
from cocotb.triggers import *

from cfl_cocotb.testbench import Testbench, CombinationalTestbench
from cfl_cocotb.streaming import (
    StreamDriver,
    StreamMonitor,
)
from cfl_cocotb.runner import veri_runner, SRC_PATH
from cfl_cocotb.torch_fp_conversion import fp_2_bin, bin_2_fp
from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware
# from quant.quant_operations.exp import fp_exp

logger = logging.getLogger("testbench")
logger_level = logging.DEBUG
logger.setLevel(logger_level)

src_path = Path(__file__).parent.parent.parent

torch.manual_seed(10)

def hardware_round(x: torch.Tensor):
    """Round to nearest with hardware-like behavior"""
    x_sign = x.sign()
    x_abs = x.abs()
    x_abs_rounded = ((x_abs * 4).floor() / 4).round()
    return x_sign * x_abs_rounded

def hardware_dynamic_shift(x: torch.Tensor, shift_amt: torch.Tensor, out_width):
    """
    Dynamic shift of x by shift_amt
    """
    x_sign = x.sign()
    x_abs = x.abs()
    max_data = 2**(out_width - 1) - 1
    x_abs_shifted = (x_abs * (2** shift_amt)).floor()
    x_abs_shifted = torch.clamp(x_abs_shifted, 0, max_data)
    return x_sign * x_abs_shifted

def fp_exp(signed_exp_in: torch.Tensor, signed_mant_in: torch.Tensor, config: dict):
    """
    Hardware model of the fp_exp.sv module
    
    Algorithm:
    1. Multiply mantissa by log2(e) constant
    2. Apply exponent scaling  
    3. Extract integer and fractional parts
    4. Apply Taylor series to fractional part: 2^f ≈ 1 + ln(2)*f + ln²(2)*f²/2! + ln³(2)*f³/3!
    5. Return integer part as exponent and Taylor result as mantissa
    """
    in_exp_width = config["in_exp_width"]
    in_fix_width = config["in_fix_width"] 
    in_fix_frac_width = config["in_fix_frac_width"]
    out_exp_width = config["out_exp_width"]
    out_fix_width = config["out_fix_width"]
    out_fix_frac_width = config["out_fix_frac_width"]

    # Step 1: Multiply mantissa by MLOG2_E (log2(e) coefficient)
    # MLOG2_E = 92 in hardware (this is log2(e) * 2^6 for Q1.6 format)
    MLOG2_E = 92/2**7
    ELOG2_E = 1
    
    # Convert signed mantissa to unsigned for multiplication
    # Multiply by log2(e) coefficient (fixed point multiplication)
    signed_mant_log2_e = signed_mant_in * MLOG2_E * (2**(in_fix_frac_width))
    signed_mant_log2_e = hardware_round(signed_mant_log2_e) / (2**(in_fix_frac_width))
    logger.debug(f"signed_mant_in: {signed_mant_in}")
    logger.debug(f"signed_mant_log2_e: {signed_mant_log2_e}")
    # Adjust exponent
    signed_exp_log2_e = signed_exp_in + ELOG2_E

    
    # Step 2: Apply exponent scaling (shift mantissa by exponent)
    # This creates fixed point data with integer and fractional parts
    FIXED_POINT_WIDTH = in_fix_width + 10
    FIX_POINT_MAX = (2**(FIXED_POINT_WIDTH - 1)- 1)/2**(in_fix_frac_width)
    FIX_POINT_MIN = -2**(FIXED_POINT_WIDTH - 1)/2**(in_fix_frac_width)

    fixed_point_data = signed_mant_log2_e * (2 ** signed_exp_log2_e)
    fixed_point_data = hardware_dynamic_shift(signed_mant_log2_e*2**(in_fix_frac_width), signed_exp_log2_e, FIXED_POINT_WIDTH)/2**(in_fix_frac_width)
    fixed_point_data = torch.clamp(fixed_point_data, FIX_POINT_MIN, FIX_POINT_MAX)
    
    # Step 3: Extract integer and fractional parts
    fixed_point_int_part = fixed_point_data.floor()
    fixed_point_frac_part = fixed_point_data - fixed_point_int_part
    
    # Step 4: Apply Taylor series to fractional part
    logger.debug(f"fixed_point_int_part: {fixed_point_int_part}, fixed_point_frac_part: {fixed_point_frac_part}")
    taylor_result = taylor_series_hardware(fixed_point_frac_part, config)

    # Step 5: Return results
    # The RTL assigns signed_exp_out = signed_exp_in (pass through)
    # The RTL assigns signed_mant_out = taylor_output
    output_exp = fixed_point_int_part  # Pass through as in RTL
    output_mant = taylor_result
    logger.debug(f"fixed_point_frac_part: {fixed_point_frac_part}, taylor_result: {taylor_result}")
    
    return output_exp, output_mant

def taylor_series_hardware(x: torch.Tensor, config: dict):
    """
    Taylor series expansion of 2^x for testing
    """
    in_exp_width = config["in_exp_width"]
    in_fix_width = config["in_fix_width"]
    in_fix_frac_width = config["in_fix_frac_width"]
    out_exp_width = config["out_exp_width"]
    out_fix_width = config["out_fix_width"]
    out_fix_frac_width = config["out_fix_frac_width"]

    # ln(2) coefficient in fixed point (Q7.5 format)
    ln2 = torch.tensor(22) * (2**(in_fix_frac_width - 5)) / 2**5
    
    # Calculate Taylor series terms: 2^x ≈ 1 + ln(2)*x + ln²(2)*x²/2! + ln³(2)*x³/3!
    term0 = 1.0

    term1 = x * ln2 * (2**(in_fix_frac_width))
    term1 = hardware_round(term1) / (2**(in_fix_frac_width))
    
    term2 = (term1 * term1 * 2**(in_fix_frac_width)) 
    term2 = hardware_round(term2) //2 / (2**(in_fix_frac_width))
    term3_inter = ((term2 * term1 )*2**(in_fix_frac_width)) 
    term3_inter = hardware_round(term3_inter) / 2**(in_fix_frac_width)
    term3 = term3_inter / 3 * 2**(in_fix_frac_width)
    term3 = hardware_round(term3) / (2**(in_fix_frac_width))
    logger.debug(f"term0: {term0 * 2**(in_fix_frac_width)}, term1: {term1 * 2**(in_fix_frac_width)}, term2: {term2 * 2**(in_fix_frac_width)}, term3: {term3 * 2**(in_fix_frac_width)}")
    return term0 + term1 + term2 + term3


class FPExpTB(CombinationalTestbench):
    def generate_inputs(self, num):
        torch.manual_seed(0)
        q_config = {
            "in_exp_width": self.dut.IN_EXP_WIDTH.value,
            "in_fix_width": self.dut.IN_FIX_WIDTH.value,
            "in_fix_frac_width": self.dut.IN_FIX_FRAC_WIDTH.value,
            "out_exp_width": self.dut.OUT_EXP_WIDTH.value,
            "out_fix_width": self.dut.OUT_FIX_WIDTH.value,
            "out_fix_frac_width": self.dut.OUT_FIX_FRAC_WIDTH.value,
        }
        
        # Generate test inputs
        a = torch.randn(num) * 3
        qa, a_exp, a_mant = _minifloat_ieee_quantize_hardware(a, q_config["in_fix_frac_width"] + q_config["in_exp_width"] + 1, q_config["in_exp_width"])
        
        # Generate mantissa values
        mant = torch.rand(num) * 2 - 1  # Range [-1, 1]
        int_mant = (mant * 2**(q_config["in_fix_frac_width"])).round().long()
        
        # Calculate expected outputs using hardware model
        expected_exp, expected_mant = fp_exp(a_exp, a_mant, q_config)

        self.inputs = {
            "signed_exp_in": a_exp.int().tolist(),
            "signed_mant_in": (a_mant*2**(q_config["in_fix_frac_width"])).int().tolist(),
        }
        self.outputs = {
            "signed_exp_out": expected_exp.int().tolist(),
            "signed_mant_out": (expected_mant * 2**(q_config["out_fix_frac_width"])).int().tolist(),
        }
    
    def check_output(self, expected_output, hardware_output):
        self.log.debug(f"----------------{self.dut}---------")
        from cfl_tools.debugger import get_dut_attributes
        # get_dut_attributes(self.dut, self.log, 'signed_integer')
        get_dut_attributes(self.dut, self.log)
        self.log.debug(f"expected_output: {expected_output}, hardware_output: {int(hardware_output.signed_integer)}")
        get_dut_attributes(self.dut.taylor_series_expansion_inst, self.log, 'integer')
        
        assert expected_output == hardware_output.signed_integer, f"Expected {expected_output}, but got {int(hardware_output.signed_integer)}"


@cocotb.test()
async def test(dut):
    tb = FPExpTB(dut)
    tb.log.setLevel(logger_level)
    await tb.run_test(20)


if __name__ == "__main__":
    veri_runner(
        trace=True, 
        module="fp_exp",
        group="fp_operation",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/int_operation"),
            str(SRC_PATH / "basic_components/buffer"),
        ],
        module_param_list=[
            {
                "IN_EXP_WIDTH": 8,
                "IN_FIX_WIDTH": 7,
                "IN_FIX_FRAC_WIDTH": 5,
                "OUT_EXP_WIDTH": 8,
                "OUT_FIX_WIDTH": 8,
                "OUT_FIX_FRAC_WIDTH": 5
            }
        ]
    )