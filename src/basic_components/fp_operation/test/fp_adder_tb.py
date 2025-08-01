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
from cocotb.log import SimLog

from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware
from quant.quant_operations.add import fp_add_hardware

import math
import torch

class FPAddTB(Testbench):
    def __init__(self, dut) -> None:
        super().__init__(dut, dut.clk, dut.rst)

        if not hasattr(self, "log"):
            self.log = SimLog("%s" % (type(self).__qualname__))
            self.log.setLevel(logging.DEBUG)

        # * QKV drivers
        self.input_driver = MultiSignalStreamDriver(
            dut.clk, (dut.exp_a, dut.mant_a, dut.exp_b, dut.mant_b), dut.data_in_valid, dut.data_in_ready
        )

        self.out_monitor = MultiSignalStreamMonitor(
            dut.clk,
            (dut.exp_out, dut.mant_out),
            dut.data_out_valid,
            dut.data_out_ready,
            check=True,
        )

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

        torch.manual_seed(0)
        torch_a = torch.randn(num)
        torch_b = torch.randn(num)

        width = config["IN_FIX_FRAC_WIDTH"] + config["IN_EXP_WIDTH"] + 1
        exponent_width = config["IN_EXP_WIDTH"]

        qa, a_exp, a_mant = _minifloat_ieee_quantize_hardware(torch_a, width, exponent_width)
        qb, b_exp, b_mant = _minifloat_ieee_quantize_hardware(torch_b, width, exponent_width)

        exp_sum, mant_sum = fp_add_hardware(a_exp, a_mant, b_exp, b_mant, config)
        self.inputs = [(int(a_exp[i]), int(a_mant[i]*2**config["IN_FIX_FRAC_WIDTH"]), int(b_exp[i]), int(b_mant[i]*2**config["IN_FIX_FRAC_WIDTH"])) for i in range(num)]
        self.exp_out = [(int(exp_sum[i]), int(mant_sum[i]*2**config["OUT_FIX_FRAC_WIDTH"])) for i in range(num)]

    async def run_test(self, us, num):
        await self.reset()
        self.log.info(f"Reset finished")
        self.out_monitor.ready.value = 1

        self.generate_inputs(num)   

        self.input_driver.load_driver(self.inputs)

        self.out_monitor.load_monitor(self.exp_out)

        await Timer(100, units="ns")

        await Timer(us, units="us")
        assert self.out_monitor.exp_queue.empty()


@cocotb.test()
async def test(dut):
    tb = FPAddTB(dut)
    tb.log.setLevel(logging.DEBUG)
    await tb.run_test(10, 10)
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
            # basic functionality of FP 8 addition
            {
                "IN_EXP_WIDTH" : 6, 
                "IN_FIX_WIDTH" : 7, 
                "IN_FIX_FRAC_WIDTH" : 5,

                "OUT_EXP_WIDTH" : 6, 
                "OUT_FIX_WIDTH" : 8,
                "OUT_FIX_FRAC_WIDTH" : 5,
            },
            # Adding one bit in outputto test the function of allowing more underflow
            # {
            #     "IN_EXP_WIDTH" : 4, 
            #     "IN_FIX_WIDTH" : 5, # sign bit + mant_width 
            #     "IN_FIX_FRAC_WIDTH" : 3,

            #     "OUT_EXP_WIDTH" : 4, 
            #     "OUT_FIX_WIDTH" : 6,
            #     "OUT_FIX_FRAC_WIDTH" : 3, # adding one bit to test the 
            # },
        ],
        trace = True,
    )


if __name__ == "__main__":
    test_simple_fp_addition()
