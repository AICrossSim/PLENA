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
from cfl_cocotb.testbench import CombinationalTestbench

from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware, pack_fp_to_bin
from cfl_tools.debugger import set_excepthook, get_dut_attributes
from lut_generation import GenerateSVLutFP


class FPHashExpTB(CombinationalTestbench):
    def generate_inputs(self, num):
        # seed = torch.randint(0, 1000000, (1,)).item()
        torch.manual_seed(0)
        # self.log.info(f"seed : {seed}")
        q_config = {
            "in_exp_width" : self.dut.IN_EXP_WIDTH.value,
            "in_mant_width" : self.dut.IN_MANT_WIDTH.value,
            "out_exp_width" : self.dut.OUT_EXP_WIDTH.value,
            "out_mant_width" : self.dut.OUT_MANT_WIDTH.value,
        }

        torch_a = torch.randn(num) * 10 - 5
        in_width = q_config["in_mant_width"] + q_config["in_exp_width"] + 1
        out_width = q_config["out_mant_width"] + q_config["out_exp_width"] + 1
        qa, a_exp, a_mant = _minifloat_ieee_quantize_hardware(torch_a, in_width, q_config["in_exp_width"])
        exp_a = torch.exp(qa)
        qout, out_exp, out_mant = _minifloat_ieee_quantize_hardware(exp_a, out_width, q_config["out_exp_width"])

        inputs_a = pack_fp_to_bin(a_exp, a_mant, q_config["in_exp_width"], q_config["in_mant_width"])
        outputs_out = pack_fp_to_bin(out_exp, out_mant, q_config["out_exp_width"], q_config["out_mant_width"])

        self.inputs = {
            "data_in": inputs_a.int().tolist(),
        }
        self.outputs = {
            "data_out": outputs_out.int().tolist(),
        }

    def check_output(self, input, output):
        self.log.debug(f"Expected result : {input}, got: {int(output)}")
        self.log.debug(f"----------------{self.dut}---------")
        get_dut_attributes(self.dut, self.log, None)
        # self.log.debug(f"----------------{self.dut.fp_casting}---------")
        # get_dut_attributes(self.dut.fp_casting, self.log, None)
        # self.log.debug(f"----------------{self.dut.fp_casting.fp_ieee_exponent_casting_inst}---------")
        # get_dut_attributes(self.dut.fp_casting.fp_ieee_exponent_casting_inst, self.log, None)
        # self.log.debug(f"----------------{self.dut.fp_casting.fp_ieee_mantissa_casting_inst}---------")
        # get_dut_attributes(self.dut.fp_casting.fp_ieee_mantissa_casting_inst, self.log, None)
        # self.log.debug(f"----------------{self.dut.fp_casting.fp_ieee_mantissa_casting_inst.round_to_nearest_even_inst}---------")
        # get_dut_attributes(self.dut.fp_casting.fp_ieee_mantissa_casting_inst.round_to_nearest_even_inst, self.log, None)

        assert input == output, f"Expected {input}, but got {int(output)}"

@cocotb.test()
async def test_fp_hash_exp(dut):
    set_excepthook()
    tb = FPHashExpTB(dut)
    tb.log.setLevel(logging.INFO)
    await tb.run_test(10)
    # try:
    #     tb = FPCPMultTB(dut)
    #     tb.log.setLevel(logging.DEBUG)
    #     await tb.run_test(10)
    # except Exception or AssertionError or AttributeError:
    #     set_excepthook()



@pytest.mark.dev
def test_simple_fp_hash_exp():
    # Run tests with different params
    in_exp_width = 6
    in_mant_width = 4
    out_exp_width = 6
    out_mant_width = 4
    gen_fp_lut = GenerateSVLutFP(
        function_name="exp",
        save=True,
        exp_width=in_exp_width,
        mant_width=in_mant_width,
        out_exp_width=out_exp_width,
        out_mant_width=out_mant_width,
    )
    gen_fp_lut.pipeline()
    veri_runner(
        group = "fp_operation",
        module = "fp_hash_exp",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/buffer"),
            str(SRC_PATH / "generated_lut"),
        ],
        module_param_list=[
            {"IN_EXP_WIDTH" : in_exp_width, "IN_MANT_WIDTH" : in_mant_width, "OUT_EXP_WIDTH" : out_exp_width, "OUT_MANT_WIDTH" : out_mant_width},
        ],
        trace = False,
    )

if __name__ == "__main__":
    test_simple_fp_hash_exp()