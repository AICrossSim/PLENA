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
from cfl_cocotb.streaming import StreamMonitor, MultiSignalStreamDriver

from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware
from cfl_cocotb.torch_fp_conversion import pack_fp_to_bin
from cfl_tools.debugger import set_excepthook, get_dut_attributes
from cocotb.log import SimLog


class FPFixAddTB(Testbench):
    def __init__(self, dut) -> None:
        super().__init__(dut, dut.clk, dut.rst)

        if not hasattr(self, "log"):
            self.log = SimLog("%s" % (type(self).__qualname__))
            self.log.setLevel(logging.DEBUG)

        # * QKV drivers
        self.in_driver = MultiSignalStreamDriver(
            dut.clk, (dut.data_a, dut.data_b), dut.data_in_valid, dut.data_in_ready
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
        q_config = {
            "EXP_WIDTH" : self.dut.EXP_WIDTH.value,
            "MANT_WIDTH" : self.dut.MANT_WIDTH.value,
        }

        torch.manual_seed(0)
        torch_a = torch.randn(num)
        torch_b = torch.randn(num)

        width = q_config["MANT_WIDTH"] + q_config["EXP_WIDTH"] + 1
        exponent_width = q_config["EXP_WIDTH"]

        qa, a_exp, a_mant = _minifloat_ieee_quantize_hardware(torch_a, width, exponent_width)
        qb, b_exp, b_mant = _minifloat_ieee_quantize_hardware(torch_b, width, exponent_width)

        inputs_a = pack_fp_to_bin(a_exp, a_mant, q_config["EXP_WIDTH"], q_config["MANT_WIDTH"])
        inputs_b = pack_fp_to_bin(b_exp, b_mant, q_config["EXP_WIDTH"], q_config["MANT_WIDTH"])

        out = qa + qb

        qout, out_exp, out_mant = _minifloat_ieee_quantize_hardware(out, width, exponent_width)
        outputs_out = pack_fp_to_bin(
            out_exp, out_mant, 
            q_config["EXP_WIDTH"], 
            q_config["MANT_WIDTH"])
        
        self.inputs = [(int(inputs_a[i]), int(inputs_b[i])) for i in range(num)]
        self.outputs = [int(outputs_out[i]) for i in range(num)]

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
    tb = FPFixAddTB(dut)
    tb.log.setLevel(logging.DEBUG)
    await tb.run_test(10, 10)



@pytest.mark.dev
def test_simple_fp_addition():
    # Run tests with different params
    veri_runner(
        group = "fp_operation",
        module = "fp_fix_adder",
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
        definitions_path = [
            str(SRC_PATH / "definitions"), 
        ],
        module_param_list=[
            # {"EXP_WIDTH" : 4, "MANT_WIDTH" : 3, "EXT_MANT_WIDTH" : 0, "EXT_EXP_WIDTH" : 0},
            {"EXP_WIDTH" : 6, "MANT_WIDTH" : 5},
            # {"EXP_WIDTH" : 3, "MANT_WIDTH" : 4, "EXT_MANT_WIDTH" : 0, "EXT_EXP_WIDTH" : 0},
            # {"EXP_WIDTH" : 1, "MANT_WIDTH" : 6, "EXT_MANT_WIDTH" : 0, "EXT_EXP_WIDTH" : 0},
        ],
        trace = False,
    )

if __name__ == "__main__":
    test_simple_fp_addition()