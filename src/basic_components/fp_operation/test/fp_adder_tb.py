#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os

from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock

from cfl_cocotb import veri_runner
from cfl_cocotb.runner import SRC_PATH
from cfl_cocotb.testbench import CombinationalTestbench
from cfl_cocotb.fp_generation import TorchFpGenerator

from quant.quantizer.hardware_quantizer import _minifloat_denorm_quantize_hardware

import math


import torch

def frexp(x: torch.Tensor, config: dict):
    exp_width = config["EXP_WIDTH"]
    mant_width = config["MANT_WIDTH"]

    if x == 0:
        return 0, 0

    exponent = x.abs().log2().floor()
    mantissa = x / (2 ** exponent)

    if x == 0:
        mantissa, exponent = 0.0, 0
    else:
        exponent = x.abs().log2().floor()
        mantissa = x / (2 ** exponent)

    
    return exponent, mantissa

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

def fp_add_hardware(
        a_exp: torch.Tensor, 
        a_mant: torch.Tensor, 
        b_exp: torch.Tensor, 
        b_mant: torch.Tensor, 
        config: dict
    ):
    out_fix_width = config["OUT_FIX_WIDTH"]
    out_fix_frac_width = config["OUT_FIX_FRAC_WIDTH"]
    out_exp_width = config["OUT_EXP_WIDTH"]
    floor = config["FLOOR"]

    a_greater = a_exp > b_exp
    # Calculate aligned exponent
    exp_sum = torch.where(a_greater, a_exp, b_exp)
    a_mant_shifted = a_mant / 2** (exp_sum - a_exp)
    b_mant_shifted = b_mant / 2** (exp_sum - b_exp)

    ## avoid loss here
    data_fix_width = out_fix_width - 1
    data_fix_frac_width = out_fix_frac_width
    a_mant_casted = fixed_point_cast(a_mant_shifted, data_fix_width, data_fix_frac_width, floor=floor)
    b_mant_casted = fixed_point_cast(b_mant_shifted, data_fix_width, data_fix_frac_width, floor=floor)

    mant_sum = a_mant_casted + b_mant_casted
    return exp_sum, mant_sum

## questions, why - ?
## questions, why 
class FPAddTB(CombinationalTestbench):
    def generate_inputs(self, num):
        config = {
            "IN_EXP_WIDTH" : self.dut.IN_EXP_WIDTH.value,
            "IN_FIX_WIDTH" : self.dut.IN_FIX_WIDTH.value,
            "IN_FIX_FRAC_WIDTH" : self.dut.IN_FIX_FRAC_WIDTH.value,

            "OUT_EXP_WIDTH" : self.dut.OUT_EXP_WIDTH.value,
            "OUT_FIX_WIDTH" : self.dut.OUT_FIX_WIDTH.value,
            "OUT_FIX_FRAC_WIDTH" : self.dut.OUT_FIX_FRAC_WIDTH.value,

            "FLOOR" : True,
        }

        torch_a = torch.randn(num)
        torch_b = torch.randn(num)

        width = config["IN_FIX_WIDTH"] + config["IN_EXP_WIDTH"]
        exponent_width = config["IN_EXP_WIDTH"]

        qa, a_exp, a_mant = _minifloat_denorm_quantize_hardware(torch_a, width, exponent_width)
        qb, b_exp, b_mant = _minifloat_denorm_quantize_hardware(torch_b, width, exponent_width)


        exp_sum, mant_sum = fp_add_hardware(a_exp, a_mant, b_exp, b_mant, config)

        self.inputs = {
            "exp_a": a_exp.to(torch.int8).tolist(),
            "mant_a": (a_mant * 2**config["IN_FIX_FRAC_WIDTH"]).to(torch.int8).tolist(),
            "exp_b": b_exp.to(torch.int8).tolist(),
            "mant_b": (b_mant * 2**config["IN_FIX_FRAC_WIDTH"]).to(torch.int8).tolist(),
        }

        self.log.debug(f"""
            original_a : 
            {torch_a}, 
            q_a        : 
            {qa}, 
            exp_a      : 
            {a_exp}, 
            mant_a     : 
            {a_mant * 2**config['IN_FIX_FRAC_WIDTH']}, 
        """)
        self.log.debug(f"""
            original_b : 
            {torch_b}, 
            q_b        : 
            {qb}, 
            exp_b      : 
            {b_exp}, 
            mant_b     : 
            {b_mant * 2**config['IN_FIX_FRAC_WIDTH']}
        """)

        self.outputs = {
            "exp_out": exp_sum.to(torch.int8).tolist(),
            "mant_out": (mant_sum * 2**config["OUT_FIX_FRAC_WIDTH"]).to(torch.int8).tolist(),
        }

    def check_output(self, input, output):
        self.log.debug(f"Expected result : {input}, got: {int(output)}")

        # assert input == output, f"Expected {input}, but got {int(output)}"

@cocotb.test()
async def test(dut):
    tb = FPAddTB(dut)
    tb.log.setLevel(logging.DEBUG)
    await tb.run_test(10)
    # try:
    #     tb = FPExpTB(dut)
    #     await tb.run_test(10)
    # except Exception as e:
    #     print("\nEntering debugger...")
    #     pdb.post_mortem(sys.exc_info()[2])
# @cocotb.test()



@pytest.mark.dev
def test_simple_fp_addition():
    # Run tests with different params
    veri_runner(
        group = "fp_operation",
        module = "fp_adder",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/buffer")
        ],
        module_param_list=[
            {
                "IN_EXP_WIDTH" : 4, 
                "IN_FIX_WIDTH" : 3, # sign bit + mant_width 
                "IN_FIX_FRAC_WIDTH" : 2,

                "OUT_EXP_WIDTH" : 4, 
                "OUT_FIX_WIDTH" : 5,
                "OUT_FIX_FRAC_WIDTH" : 3,
            },
        ],
        trace = True,
    )


if __name__ == "__main__":
    torch.manual_seed(0)
    test_simple_fp_addition()
