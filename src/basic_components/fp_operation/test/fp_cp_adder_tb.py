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

import math


import torch

def torch_frexp(x: torch.Tensor):
    if x == 0:
        mantissa, exponent = 0.0, 0
    else:
        exponent = x.abs().log2().floor()
        mantissa = x / (2 ** exponent)
    return mantissa, exponent

def parse_fp_input(x: torch.Tensor, config):
    """
    Currently dont support the inf part
    """
    exp_width = config["EXP_WIDTH"]
    mant_width = config["MANT_WIDTH"]

    exponent_min = -2**(exp_width)
    exponent_max = 2**(exp_width) - 2
    mantissa, exponent = torch_frexp(x)

    sign = torch.sign(x)
    new_exponent = exponent.clamp(exponent_min, exponent_max)

    if (new_exponent == exponent_min):
        mant_max = 2**(mant_width) - 1
        mant_min = 0
    else:
        mant_max = 2**(mant_width + 1) - 1
        mant_min = 0

    if (new_exponent == exponent_min):
        mantissa = mantissa
        mant_min = 0
    else:
        mantissa = mantissa * 2
        new_exponent -= 1

    mantissa = mantissa.clamp(mant_min, mant_max)


    mantissa = (mantissa << mant_width) >> (new_exp - exponent)
    mantissa = max(min(mantissa, mant_max), mant_min)
    mantissa = mantissa >> mant_width

    return new_exp, mantissa
    if exponent != exponent_min:
        exponent -= 1
        mantissa *= 2
    
    exp, mant = clamp(exponent, mantissa, exp_width, mant_width)

    return exp, mant



def fixed_point_cast(
        x: torch.Tensor,
        OUT_WIDTH: int,
        OUT_FRAC_WIDTH: int,
        floor: bool = True,
):
    min_val = -2**(OUT_WIDTH - 1)
    max_val = 2**(OUT_WIDTH) - 1
    if floor:
        x = torch.clamp(x * 2**(OUT_FRAC_WIDTH).floor(), min_val, max_val)
    else:
        x = torch.clamp(x * 2**(OUT_FRAC_WIDTH).round(), min_val, max_val)

    x = x / 2**(OUT_FRAC_WIDTH)

    return x

def fp_add_hardware(
        a_exp: torch.Tensor, 
        a_mant: torch.Tensor, 
        b_exp: torch.Tensor, 
        b_mant: torch.Tensor, 
        config: dict
    ):
    out_mant_width = config["OUT_MANT_WIDTH"]
    out_mant_frac_width = config["OUT_MANT_FRAC_WIDTH"]
    out_exp_width = config["OUT_EXP_WIDTH"]
    floor = config["FLOOR"]

    if a_exp == b_exp:
        exp_sum = a_exp
    elif a_exp > b_exp:
        b_mant = b_mant / 2** (a_exp - b_exp)
        exp_sum = a_exp
    elif a_exp < b_exp:
        a_mant = a_mant / 2** (b_exp - a_exp)
        exp_sum = b_exp
    else:
        raise ValueError("a_exp and b_exp are the same")

    ## avoid loss here
    data_mant_width = out_mant_width - 1
    data_mant_frac_width = out_mant_frac_width
    a_mant = fixed_point_cast(a_mant, data_mant_width, data_mant_frac_width, floor=floor)
    b_mant = fixed_point_cast(b_mant, data_mant_width, data_mant_frac_width, floor=floor)
    mant_sum = a_mant + b_mant
    return exp_sum, mant_sum

class FPAddTB(CombinationalTestbench):
    def generate_inputs(self, num):
        exp_width = self.dut.EXP_WIDTH.value
        mant_width = self.dut.MANT_WIDTH.value
        ext_mant_width = self.dut.EXT_MANT_WIDTH.value
        ext_exp_width = self.dut.EXT_EXP_WIDTH.value

        input_generator = TorchFpGenerator(exp_width, mant_width)
        input_generator.max_val = 2.0
        input_generator.min_val = -2.0
        output_generator = TorchFpGenerator(exp_width + ext_exp_width, mant_width + ext_mant_width)

        fp_outputs = []
        outputs_out = []
        fp_data_in_0, data_in_0 = input_generator.generate_fp_input(num)
        fp_data_in_1, data_in_1 = input_generator.generate_fp_input(num)
        inputs_a = data_in_0
        inputs_b = data_in_1

        for i in range(num):
            fp_outputs.append(fp_data_in_0[i] + fp_data_in_1[i])
            outputs_out.append(output_generator.fp2bin(fp_outputs[i]))

        self.inputs = {
            "data_a": inputs_a,
            "data_b": inputs_b,
        }

        self.log.debug(f"input_0 : {fp_data_in_0}, Converted bin : {data_in_0}")
        self.log.debug(f"input_1 : {fp_data_in_1}, Converted bin : {data_in_1}")
        self.log.debug(f"output : {fp_outputs}, Converted output : {outputs_out}")
        self.outputs = {
            "data_out": outputs_out,
        }

    def check_output(self, input, output):
        self.log.debug(f"Expected result : {input}, got: {int(output)}")

        assert input == output, f"Expected {input}, but got {int(output)}"

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
        module = "fp_cp_adder",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/buffer")
        ],
        module_param_list=[
            {"EXP_WIDTH" : 4, "MANT_WIDTH" : 3, "EXT_MANT_WIDTH" : 0, "EXT_EXP_WIDTH" : 0},
            # {"EXP_WIDTH" : 3, "MANT_WIDTH" : 4, "EXT_MANT_WIDTH" : 0, "EXT_EXP_WIDTH" : 0},
            # {"EXP_WIDTH" : 1, "MANT_WIDTH" : 6, "EXT_MANT_WIDTH" : 0, "EXT_EXP_WIDTH" : 0},
        ],
        trace = False,
    )

if __name__ == "__main__":
    test_simple_fp_addition()
