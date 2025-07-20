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
from cfl_cocotb.streaming import StreamMonitor, MultiSignalStreamDriver


from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware
from cfl_cocotb.torch_fp_conversion import pack_fp_to_bin
from cfl_tools.debugger import set_excepthook, get_dut_attributes
from cocotb.log import SimLog

class FPCPAsymMultTB(Testbench):
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
            "EXP_WIDTH_A" : self.dut.EXP_WIDTH_A.value,
            "MANT_WIDTH_A" : self.dut.MANT_WIDTH_A.value,
            "EXP_WIDTH_B" : self.dut.EXP_WIDTH_B.value,
            "MANT_WIDTH_B" : self.dut.MANT_WIDTH_B.value,
            "EXT_MANT_WIDTH" : self.dut.EXT_MANT_WIDTH.value,
            "EXT_EXP_WIDTH" : self.dut.EXT_EXP_WIDTH.value,
            "OUT_EXP_WIDTH" : self.dut.OUT_EXP_WIDTH.value,
            "OUT_MANT_WIDTH" : self.dut.OUT_MANT_WIDTH.value,
        }

        torch.manual_seed(0)
        torch_a = torch.randn(num)
        torch_b = torch.randn(num)

        width_a = q_config["MANT_WIDTH_A"] + q_config["EXP_WIDTH_A"] + 1
        exponent_width_a = q_config["EXP_WIDTH_A"]
        mantissa_width_a = q_config["MANT_WIDTH_A"]
        width_b = q_config["MANT_WIDTH_B"] + q_config["EXP_WIDTH_B"] + 1
        exponent_width_b = q_config["EXP_WIDTH_B"]
        mantissa_width_b = q_config["MANT_WIDTH_B"]

        out_exponent_width = q_config["OUT_EXP_WIDTH"] + q_config["EXT_EXP_WIDTH"]
        out_mantissa_width = q_config["OUT_MANT_WIDTH"] + q_config["EXT_MANT_WIDTH"]
        out_width = out_mantissa_width + out_exponent_width + 1

        qa, a_exp, a_mant = _minifloat_ieee_quantize_hardware(torch_a, width_a, exponent_width_a)
        qb, b_exp, b_mant = _minifloat_ieee_quantize_hardware(torch_b, width_b, exponent_width_b)

        inputs_a = pack_fp_to_bin(
            a_exp, 
            a_mant, 
            exponent_width_a, 
            mantissa_width_a)
        inputs_b = pack_fp_to_bin(
            b_exp, 
            b_mant, 
            exponent_width_b, 
            mantissa_width_b)

        out = qa * qb

        qout, out_exp, out_mant = _minifloat_ieee_quantize_hardware(
            out, 
            out_width, 
            out_exponent_width)

        outputs_out = pack_fp_to_bin(
            out_exp, out_mant, 
            out_exponent_width, 
            out_mantissa_width)
        breakpoint()
        
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
    set_excepthook()
    tb = FPCPAsymMultTB(dut)
    tb.log.setLevel(logging.DEBUG)
    await tb.run_test(10, 10)
    # try:
    #     tb = FPCPMultTB(dut)
    #     tb.log.setLevel(logging.DEBUG)
    #     await tb.run_test(10)
    # except Exception or AssertionError or AttributeError:
    #     set_excepthook()



@pytest.mark.dev
def test_fp_cp_asym_mult():
    # Run tests with different params
    veri_runner(
        group = "fp_operation",
        module = "fp_cp_asym_mult",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/buffer"),
            str(SRC_PATH / "basic_components/int_operation"),
        ],
        module_param_list=[
            # {"EXP_WIDTH" : 4, "MANT_WIDTH" : 3, "EXT_MANT_WIDTH" : 0, "EXT_EXP_WIDTH" : 0},
            {
                "EXP_WIDTH_A" : 4, 
                "MANT_WIDTH_A" : 3, 
                "EXP_WIDTH_B" : 4, 
                "MANT_WIDTH_B" : 3, 
                "EXT_MANT_WIDTH" : 3, 
                "EXT_EXP_WIDTH" : 1,
            },
            # {"EXP_WIDTH" : 1, "MANT_WIDTH" : 6, "EXT_MANT_WIDTH" : 0, "EXT_EXP_WIDTH" : 0},
        ],
        trace = False,
    )

if __name__ == "__main__":
    test_fp_cp_asym_mult()