#!/usr/bin/env python3

import logging
from re import A
import pytest
import cocotb
import sys
import os

from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock

import torch

from cfl_cocotb import veri_runner
from cfl_cocotb.runner import SRC_PATH
from cfl_cocotb.testbench import Testbench
from cfl_cocotb.fp_generation import TorchFpGenerator
from cfl_cocotb.streaming import StreamMonitor, StreamDriver

from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware
from cfl_cocotb.torch_fp_conversion import pack_fp_to_bin
from cfl_tools.debugger import set_excepthook, get_dut_attributes
from cocotb.log import SimLog

class FPCPReciprocalTB(Testbench):
    def __init__(self, dut) -> None:
        super().__init__(dut, dut.clk, dut.rst)

        if not hasattr(self, "log"):
            self.log = SimLog("%s" % (type(self).__qualname__))
            self.log.setLevel(logging.DEBUG)

        # * QKV drivers
        self.in_driver = StreamDriver(
            dut.clk, dut.data_in, dut.data_in_valid, dut.data_in_ready
        )

        self.out_monitor = StreamMonitor(
            dut.clk,
            dut.data_out,
            dut.data_out_valid,
            dut.data_out_ready,
            check=True,
            unsigned=True,
        )
    def generate_inputs(self, num):
        # seed = torch.randint(0, 1000000, (1,)).item()
        torch.manual_seed(0)
        # self.log.info("seed : {}".format(seed))
        q_config = {
            "in_exp_width" : self.dut.IN_EXP_WIDTH.value,
            "in_mant_width" : self.dut.IN_MANT_WIDTH.value,
            "out_exp_width" : self.dut.OUT_EXP_WIDTH.value,
            "out_mant_width" : self.dut.OUT_MANT_WIDTH.value,
        }

        in_exp_width = q_config["in_exp_width"]
        in_mant_width = q_config["in_mant_width"]
        out_exp_width = q_config["out_exp_width"]
        out_mant_width = q_config["out_mant_width"]

        # Generate random inputs, avoiding values too close to zero to prevent overflow
        torch_x = torch.randn(num) * 10 - 5
        # Replace values too close to zero with reasonable values
        torch_x[torch.abs(torch_x) < 0.1] = torch.sign(torch_x[torch.abs(torch_x) < 0.1]) * 0.5

        in_width = q_config["in_mant_width"] + q_config["in_exp_width"]
        in_exponent_width = q_config["in_exp_width"]

        # Quantize input
        qx, x_exp, x_mant = _minifloat_ieee_quantize_hardware(torch_x, in_width, in_exponent_width)

        out_width = q_config["out_mant_width"] + q_config["out_exp_width"] + 1
        out_exponent_width = q_config["out_exp_width"]

        # Calculate reciprocal: 1/x
        out = 1.0 / qx
        self.log.debug("input : {}".format(qx))
        self.log.debug("reciprocal out : {}".format(out))
        
        # Quantize output
        qout, out_exp, out_mant = _minifloat_ieee_quantize_hardware(out, out_width, out_exponent_width)

        # Pack inputs and outputs to binary format
        inputs_x = pack_fp_to_bin(x_exp, x_mant, q_config["in_exp_width"], q_config["in_mant_width"])
        outputs_out = pack_fp_to_bin(out_exp, out_mant, q_config["out_exp_width"], q_config["out_mant_width"])

        self.inputs = [(int(inputs_x[i])) for i in range(num)]

        self.outputs = [int(outputs_out[i]) for i in range(num)]

    async def run_test(self, us, num):
        await self.reset()
        self.log.info(f"Reset finished")
        self.out_monitor.ready.value = 1

        self.generate_inputs(num)   

        self.in_driver.load_driver(self.inputs)

        self.out_monitor.load_monitor(self.outputs)

        await Timer(us, units="us")
        assert self.out_monitor.exp_queue.empty()

@cocotb.test()
async def test_fp_cp_reciprocal(dut):
    set_excepthook()
    tb = FPCPReciprocalTB(dut)
    tb.log.setLevel(logging.DEBUG)
    await tb.run_test(10, 10)

@pytest.mark.dev
def test_simple_fp_reciprocal():
    # Run tests with different params
    veri_runner(
        group = "fp_operation",
        module = "fp_cp_reciprocal",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/buffer"),
            str(SRC_PATH / "basic_components/cast"),
            str(SRC_PATH / "basic_components/int_operation")
        ],
        module_param_list=[
            {"IN_EXP_WIDTH" : 6, "IN_MANT_WIDTH" : 5, "OUT_EXP_WIDTH" : 6, "OUT_MANT_WIDTH" : 5},
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_simple_fp_reciprocal()
