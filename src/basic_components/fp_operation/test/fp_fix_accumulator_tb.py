#!/usr/bin/env python3

import logging
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
import cocotb
from cocotb.result import TestSuccess


def hardware_accumulate(a, width, exponent_width):
    out = 0
    out_list = []
    for item in a:
        out += item
        out, _, _ = _minifloat_ieee_quantize_hardware(out, width, exponent_width)
        out_list.append(out)
    return out_list

class FPFixAccumulatorTB(Testbench):
    def __init__(self, dut) -> None:
        super().__init__(dut, dut.clk, dut.rst)

        cocotb.start_soon(self.stop())
        if not hasattr(self, "log"):
            self.log = SimLog("%s" % (type(self).__qualname__))
            self.log.setLevel(logging.DEBUG)

        # * QKV drivers
        self.in_driver = StreamDriver(
            dut.clk, 
            dut.data_in, 
            dut.data_in_valid, 
            dut.data_in_ready,
        )

        self.out_monitor = StreamMonitor(
            dut.clk,
            dut.data_out,
            dut.data_out_valid,
            dut.data_out_ready,
            check=False,
            unsigned=True,
        )
        self.in_driver.log.setLevel(logging.DEBUG)
        self.out_monitor.log.setLevel(logging.DEBUG)

    def generate_inputs(self, num):
        q_config = {
            "EXP_WIDTH" : self.dut.EXP_WIDTH.value,
            "MANT_WIDTH" : self.dut.MANT_WIDTH.value,
        }

        torch.manual_seed(0)
        torch_a = torch.randn(num)

        width = q_config["MANT_WIDTH"] + q_config["EXP_WIDTH"] + 1
        exponent_width = q_config["EXP_WIDTH"]

        qa, a_exp, a_mant = _minifloat_ieee_quantize_hardware(torch_a, width, exponent_width)

        inputs_a = pack_fp_to_bin(a_exp, a_mant, q_config["EXP_WIDTH"], q_config["MANT_WIDTH"])

        out_list = hardware_accumulate(qa, width, exponent_width)

        qout, out_exp, out_mant = _minifloat_ieee_quantize_hardware(torch.tensor(out_list), width, exponent_width)
        outputs_out = pack_fp_to_bin(
            out_exp, out_mant, 
            q_config["EXP_WIDTH"], 
            q_config["MANT_WIDTH"])
        
        self.inputs = [int(inputs_a[i])for i in range(num)]
        self.outputs = [int(outputs_out[i]) for i in range(num)]

    async def stop(self):
        await Timer(100, units="ns")
        if self.out_monitor.exp_queue.empty():
            self.log.info("Test passed")
            raise TestSuccess("Test completed successfully")

    async def run_test(self, us, num):
        await self.reset()
        self.log.info(f"Reset finished")
        self.out_monitor.ready.value = 1

        self.generate_inputs(num)   

        self.in_driver.load_driver(self.inputs)

        self.out_monitor.load_monitor(self.outputs)

        await Timer(100, units="ns")

        await Timer(us, units="us")
        assert self.out_monitor.exp_queue.empty()

@cocotb.test()
async def test(dut):
    tb = FPFixAccumulatorTB(dut)
    tb.log.setLevel(logging.DEBUG)
    await tb.run_test(10, 10)


async def check_signal_values(dut):
    while True:
        await RisingEdge(dut.clk)
        if dut.data_in_valid.value == 1:
            print(dut.data_in.value)
            print(dut.data_in_valid.value)

@pytest.mark.dev
def test_simple_fp_addition():
    # Run tests with different params
    veri_runner(
        group = "fp_operation",
        module = "fp_fix_accumulator",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/buffer"),
            str(SRC_PATH / "basic_components/fp_operation"),
            str(SRC_PATH / "basic_components/int_operation"),
            str(SRC_PATH / "basic_components/synopsis_ip_inst"),
            str(SRC_PATH / "basic_components/synopsis")
        ],
        module_param_list=[
            {"EXP_WIDTH" : 6, "MANT_WIDTH" : 5},
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_simple_fp_addition()