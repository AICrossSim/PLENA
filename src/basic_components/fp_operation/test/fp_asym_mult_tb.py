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
from cfl_cocotb.testbench import Testbench
from cfl_cocotb.streaming import StreamDriver, StreamMonitor, MultiSignalStreamDriver, MultiSignalStreamMonitor
from cfl_cocotb.fp_generation import TorchFpGenerator

from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware

import math
import torch

def fp_asym_mult_hardware(
        exp_a: torch.Tensor,
        mant_a: torch.Tensor,
        exp_b: torch.Tensor,
        mant_b: torch.Tensor,
        OUT_FIX_FRAC_WIDTH: int,
        log,
):
    exp_out = exp_a + exp_b
    intermediate_mant = mant_a * mant_b
    mant_out = (intermediate_mant * 2**(OUT_FIX_FRAC_WIDTH)).floor()
    log.debug(f"software mant_out: {mant_out}")
    mant_out = mant_out / 2**(OUT_FIX_FRAC_WIDTH)

    return exp_out, mant_out


class FPAsymMultTB(Testbench):
    def __init__(self, dut) -> None:
        super().__init__(dut)
        self.log.setLevel(logging.DEBUG)

        # * QKV drivers
        self.a_driver = MultiSignalStreamDriver(
            dut.clk, (dut.exp_a, dut.mant_a), dut.a_in_valid, dut.a_in_ready
        )
        self.b_driver = MultiSignalStreamDriver(
            dut.clk, (dut.exp_b, dut.mant_b), dut.b_in_valid, dut.b_in_ready)

        self.out_monitor = MultiSignalStreamMonitor(
            dut.clk,
            (dut.exp_out, dut.mant_out),
            dut.out_valid,
            dut.out_ready,
            check=False,
        )
    def generate_inputs(self, num):
        config = {
            "IN_EXP_WIDTH_A" : self.dut.IN_EXP_WIDTH_A.value,
            "IN_FIX_WIDTH_A" : self.dut.IN_FIX_WIDTH_A.value,
            "IN_FIX_FRAC_WIDTH_A" : self.dut.IN_FIX_FRAC_WIDTH_A.value,

            "IN_EXP_WIDTH_B" : self.dut.IN_EXP_WIDTH_B.value,
            "IN_FIX_WIDTH_B" : self.dut.IN_FIX_WIDTH_B.value,
            "IN_FIX_FRAC_WIDTH_B" : self.dut.IN_FIX_FRAC_WIDTH_B.value,

            "OUT_EXP_WIDTH" : self.dut.OUT_EXP_WIDTH.value,
            "OUT_FIX_WIDTH" : self.dut.OUT_FIX_WIDTH.value,
            "OUT_FIX_FRAC_WIDTH" : self.dut.OUT_FIX_FRAC_WIDTH.value,

            "FLOOR" : True,
        }
        self.log.debug(f"config: {config}")

        torch.manual_seed(0)
        torch_a = torch.randn(num) * 3 - 1.5
        torch_b = torch.randn(num) * 10 - 5

        width = config["IN_FIX_WIDTH_A"] - 1 + config["IN_EXP_WIDTH_A"]
        exponent_width = config["IN_EXP_WIDTH_A"]

        qa, a_exp, a_mant = _minifloat_ieee_quantize_hardware(torch_a, width, exponent_width)
        qb, b_exp, b_mant = _minifloat_ieee_quantize_hardware(torch_b, width, exponent_width)

        exp_sum, mant_sum = fp_asym_mult_hardware(
            a_exp, 
            a_mant, 
            b_exp, 
            b_mant, 
            config["OUT_FIX_FRAC_WIDTH"], 
            self.log)

        self.inputs = {
            "exp_a": a_exp.int().tolist(),
            "mant_a": (a_mant * 2**config["IN_FIX_FRAC_WIDTH_A"]).int().tolist(),
            "exp_b": b_exp.int().tolist(),
            "mant_b": (b_mant * 2**config["IN_FIX_FRAC_WIDTH_B"]).int().tolist(),
        }

        self.log.debug(f"""
            original_a : 
            {torch_a}, 
            q_a        : 
            {qa}, 
            exp_a      : 
            {a_exp}, 
            mant_a     : 
            {a_mant * 2**config['IN_FIX_FRAC_WIDTH_A']}, 
        """)

        self.log.debug(f"""
            original_b : 
            {torch_b}, 
            q_b        : 
            {qb}, 
            exp_b      : 
            {b_exp}, 
            mant_b     : 
            {b_mant * 2**config['IN_FIX_FRAC_WIDTH_B']}
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
    tb = FPAsymMultTB(dut)
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
def test_fp_asym_mult():
    # Run tests with different params
    veri_runner(
        group = "fp_operation",
        module = "fp_asym_mult",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/buffer")
        ],
        module_param_list=[
            # basic functionality of FP 8 addition
            # {
            #     "IN_EXP_WIDTH_A" : 4, 
            #     "IN_FIX_WIDTH_A" : 5, 
            #     "IN_FIX_FRAC_WIDTH_A" : 3,
            #     "IN_EXP_WIDTH_B" : 4, 
            #     "IN_FIX_WIDTH_B" : 5, 
            #     "IN_FIX_FRAC_WIDTH_B" : 3,
            #     "OUT_FIX_FRAC_WIDTH" : 6,
            # },
            # # Adding one bit in outputto test the function of allowing more underflow
            {
                "IN_EXP_WIDTH_A" : 3, 
                "IN_FIX_WIDTH_A" : 5, 
                "IN_FIX_FRAC_WIDTH_A" : 3,
                "IN_EXP_WIDTH_B" : 4, 
                "IN_FIX_WIDTH_B" : 7, 
                "IN_FIX_FRAC_WIDTH_B" : 5,
                "OUT_FIX_FRAC_WIDTH" : 6,
            },
        ],
        trace = True,
    )


if __name__ == "__main__":
    test_fp_asym_mult()
