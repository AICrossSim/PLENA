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

from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware, pack_fp_to_bin
from cfl_tools.debugger import set_excepthook, get_dut_attributes


class FPCPAddTB(Testbench):
    def __init__(self, dut) -> None:
        super().__init__(dut, dut.clk, dut.rst)

        if not hasattr(self, "log"):
            self.log = SimLog("%s" % (type(self).__qualname__))
            self.log.setLevel(logging.DEBUG)

        # * QKV drivers
        self.a_driver = MultiSignalStreamDriver(
            dut.clk, (dut.data_a, dut.data_b), dut.data_in_valid, dut.data_in_ready
        )

        self.out_monitor = StreamMonitor(
            dut.clk,
            dut.data_out,
            dut.data_out_valid,
            dut.data_out_ready,
            check=True,
        )

    def generate_inputs(self, num):
        config = {
            "EXP_WIDTH" : self.dut.EXP_WIDTH.value,
            "MANT_WIDTH" : self.dut.MANT_WIDTH.value,
            "EXT_MANT_WIDTH" : self.dut.EXT_MANT_WIDTH.value,
            "EXT_EXP_WIDTH" : self.dut.EXT_EXP_WIDTH.value,

            "OUT_EXP_WIDTH" : self.dut.OUT_EXP_WIDTH.value,
            "OUT_FIX_WIDTH" : self.dut.OUT_FIX_WIDTH.value,
            "OUT_FIX_FRAC_WIDTH" : self.dut.OUT_FIX_FRAC_WIDTH.value,

            "IN_EXP_WIDTH_B" : self.dut.IN_EXP_WIDTH_B.value,
            "IN_FIX_WIDTH_B" : self.dut.IN_FIX_WIDTH_B.value,
            "IN_FIX_FRAC_WIDTH_B" : self.dut.IN_FIX_FRAC_WIDTH_B.value,

            "FLOOR" : True,
        }

        torch.manual_seed(0)
        torch_a = torch.randn(num)
        torch_b = torch.randn(num)

        width_a = config["IN_FIX_FRAC_WIDTH_A"] + config["IN_EXP_WIDTH_A"] + 1
        exponent_width_a = config["IN_EXP_WIDTH_A"]

        width_b = config["IN_FIX_FRAC_WIDTH_B"] + config["IN_EXP_WIDTH_B"] + 1
        exponent_width_b = config["IN_EXP_WIDTH_B"]

        qa, a_exp, a_mant = _minifloat_ieee_quantize_hardware(torch_a, width_a, exponent_width_a)
        qb, b_exp, b_mant = _minifloat_ieee_quantize_hardware(torch_b, width_b, exponent_width_b)

        exp_out, mant_out = fp_asym_mult_hardware(a_exp, a_mant, b_exp, b_mant, config["OUT_FIX_FRAC_WIDTH"], self.log)
        self.a_input = [(int(qa[i]), int(a_mant[i]*2**config["IN_FIX_FRAC_WIDTH_A"])) for i in range(num)]
        self.b_input = [(int(qb[i]), int(b_mant[i]*2**config["IN_FIX_FRAC_WIDTH_B"])) for i in range(num)]
        self.exp_out = [(int(exp_out[i]), int(mant_out[i]*2**config["OUT_FIX_FRAC_WIDTH"])) for i in range(num)]

    async def run_test(self, us, num):
        await self.reset()
        self.log.info(f"Reset finished")
        self.out_monitor.ready.value = 1

        self.generate_inputs(num)   

        self.a_driver.load_driver(self.a_input)
        self.b_driver.load_driver(self.b_input)

        self.out_monitor.load_monitor(self.exp_out)

        await Timer(100, units="ns")

        await Timer(us, units="us")
        assert self.out_monitor.exp_queue.empty()

class FPCPAddTB(CombinationalTestbench):
    def generate_inputs(self, num):
        # seed = torch.randint(0, 1000000, (1,)).item()
        torch.manual_seed(0)
        # self.log.info(f"seed : {seed}")
        q_config = {
            "exp_width" : self.dut.EXP_WIDTH.value,
            "mant_width" : self.dut.MANT_WIDTH.value,
            "ext_mant_width" : self.dut.EXT_MANT_WIDTH.value,
            "ext_exp_width" : self.dut.EXT_EXP_WIDTH.value,
        }

        exp_width = q_config["exp_width"]
        mant_width = q_config["mant_width"]
        ext_mant_width = q_config["ext_mant_width"]
        ext_exp_width = q_config["ext_exp_width"]

        torch_a = torch.randn(num) * 10 - 5
        torch_b = torch.randn(num) * 10 - 5

        width = q_config["mant_width"] + q_config["exp_width"]
        exponent_width = q_config["exp_width"]

        qa, a_exp, a_mant = _minifloat_ieee_quantize_hardware(torch_a, width, exponent_width)
        qb, b_exp, b_mant = _minifloat_ieee_quantize_hardware(torch_b, width, exponent_width)

        out_width = q_config["mant_width"] + q_config["exp_width"] + q_config["ext_mant_width"] + q_config["ext_exp_width"] + 1
        out_exponent_width = q_config["exp_width"] + q_config["ext_exp_width"]

        out = qa + qb
        self.log.debug(f"out : {out}")
        debug_out, debug_exp, debug_mant = _minifloat_ieee_quantize_hardware(out, 5 + 8 + 1, 5)
        debug_out_bin = pack_fp_to_bin(debug_exp, debug_mant, 5, 8)
        self.log.debug(f"debug_out_bin : {debug_out_bin}")
        self.log.debug(f"debug_out : {debug_out}")
        self.log.debug(f"debug_exp : {debug_exp}")
        self.log.debug(f"debug_mant : {debug_mant}")

        qout, out_exp, out_mant = _minifloat_ieee_quantize_hardware(out, out_width, out_exponent_width)

        inputs_a = pack_fp_to_bin(a_exp, a_mant, q_config["exp_width"], q_config["mant_width"])
        inputs_b = pack_fp_to_bin(b_exp, b_mant, q_config["exp_width"], q_config["mant_width"])

        outputs_out = pack_fp_to_bin(out_exp, out_mant, q_config["exp_width"] + q_config["ext_exp_width"], q_config["mant_width"] + q_config["ext_mant_width"])

        self.inputs = {
            "data_a": inputs_a.int().tolist(),
            "data_b": inputs_b.int().tolist(),
        }

        self.log.debug(f"input_0 : {qa}, Converted bin : {inputs_a}")
        self.log.debug(f"input_1 : {qb}, Converted bin : {inputs_b}")
        self.log.debug(f"output : {qout}, Converted output : {outputs_out}")
        self.outputs = {
            "data_out": outputs_out.int().tolist(),
        }

    def check_output(self, input, output):
        self.log.debug(f"Expected result : {input}, got: {int(output)}")
        self.log.debug(f"----------------{self.dut}---------")
        get_dut_attributes(self.dut, self.log, "signed_integer")
        # self.log.debug(f"----------------{self.dut.fp_ieee_exponent_casting_inst}---------")
        # get_dut_attributes(self.dut.fp_ieee_exponent_casting_inst, self.log, None)
        # self.log.debug(f"----------------{self.dut.fp_ieee_mantissa_casting_inst}---------")
        # get_dut_attributes(self.dut.fp_ieee_mantissa_casting_inst, self.log, None)

        assert input == output, f"Expected {input}, but got {int(output)}"

@cocotb.test()
async def test(dut):
    tb = FPCPAddTB(dut)
    tb.log.setLevel(logging.DEBUG)
    await tb.run_test(10)
    # try:
    #     tb = FPCPAddTB(dut)
    #     tb.log.setLevel(logging.INFO)
    #     await tb.run_test(10)
    # except Exception or AssertionError as e:
    #     set_excepthook()



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