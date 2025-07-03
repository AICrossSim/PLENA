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

from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware

import math
import torch

def fp_mult_hardware(
        exp_a: torch.Tensor,
        mant_a: torch.Tensor,
        exp_b: torch.Tensor,
        mant_b: torch.Tensor,
        IN_FIX_FRAC_WIDTH: int,
        OUT_FIX_FRAC_WIDTH: int,
        log,
):
    exp_out = exp_a + exp_b
    intermediate_mant = mant_a * mant_b
    mant_out = (intermediate_mant * 2**(OUT_FIX_FRAC_WIDTH)).floor()
    log.debug(f"software mant_out: {mant_out}")
    mant_out = mant_out / 2**(OUT_FIX_FRAC_WIDTH)

    return exp_out, mant_out


## questions, why 
class FPMultTB(CombinationalTestbench):
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
        self.log.debug(f"config: {config}")

        torch.manual_seed(0)
        torch_a = torch.randn(num) * 10 - 5
        torch_b = torch.randn(num) * 10 - 5

        width = config["IN_FIX_WIDTH"] - 1 + config["IN_EXP_WIDTH"]
        exponent_width = config["IN_EXP_WIDTH"]

        qa, a_exp, a_mant = _minifloat_ieee_quantize_hardware(torch_a, width, exponent_width)
        qb, b_exp, b_mant = _minifloat_ieee_quantize_hardware(torch_b, width, exponent_width)

        exp_sum, mant_sum = fp_mult_hardware(
            a_exp, 
            a_mant, 
            b_exp, 
            b_mant, 
            config["IN_FIX_FRAC_WIDTH"], 
            config["OUT_FIX_FRAC_WIDTH"], 
            self.log)

        self.inputs = {
            "exp_a": a_exp.int().tolist(),
            "mant_a": (a_mant * 2**config["IN_FIX_FRAC_WIDTH"]).int().tolist(),
            "exp_b": b_exp.int().tolist(),
            "mant_b": (b_mant * 2**config["IN_FIX_FRAC_WIDTH"]).int().tolist(),
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
            "exp_out": exp_sum.int().tolist(),
            "mant_out": (mant_sum * 2**config["OUT_FIX_FRAC_WIDTH"]).int().tolist(),
        }
        self.log.debug(f"inputs: {self.inputs}")
        self.log.debug(f"outputs: {self.outputs}")

    def check_output(self, input, output):
        from cfl_tools.debugger import get_dut_attributes
        self.log.debug(f"Expected result : {input}, got: {int(output.signed_integer)}")
        get_dut_attributes(self.dut, self.log, "signed_integer")
        # get_dut_attributes(self.dut.fp_mult_inst, self.log, None)
        assert input == int(output.signed_integer), f"Expected {input}, but got {int(output.signed_integer)}"

@cocotb.test()
async def test(dut):
    tb = FPMultTB(dut)
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
        module = "fp_mult",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/buffer")
        ],
        module_param_list=[
            # basic functionality of FP 8 addition
            {
                "IN_EXP_WIDTH" : 4, 
                "IN_FIX_WIDTH" : 5, 
                "IN_FIX_FRAC_WIDTH" : 3,

                "OUT_FIX_FRAC_WIDTH" : 6,
            },
            # Adding one bit in outputto test the function of allowing more underflow
            {
                "IN_EXP_WIDTH" : 4, 
                "IN_FIX_WIDTH" : 5, # sign bit + mant_width 
                "IN_FIX_FRAC_WIDTH" : 3,

                "OUT_FIX_FRAC_WIDTH" : 5, # adding one bit to test the 
            },
        ],
        trace = True,
    )


if __name__ == "__main__":
    test_simple_fp_addition()
