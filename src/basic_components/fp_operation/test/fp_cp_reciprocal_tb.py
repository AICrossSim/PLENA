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
from cfl_cocotb.fp_generation import TorchFpGenerator

from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware
from cfl_cocotb.torch_fp_conversion import pack_fp_to_bin
from cfl_tools.debugger import set_excepthook, get_dut_attributes


class FPCPReciprocalTB(CombinationalTestbench):
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

        self.inputs = {
            "data_in": inputs_x.int().tolist(),
        }

        self.log.debug("input : {}, {}, {}".format(qx, x_exp, x_mant))
        self.log.debug("output : {}, {}, {}".format(qout, out_exp, out_mant))
        self.outputs = {
            "data_out": outputs_out.int().tolist(),
        }

    def check_output(self, input, output):
        self.log.debug("Expected result : {}, got: {}".format(input, int(output)))
        self.log.debug("----------------{}---------".format(self.dut))
        # get_dut_attributes(self.dut, self.log, None)

        assert input == output, "Expected {}, but got {}".format(input, int(output))

@cocotb.test()
async def test_fp_cp_reciprocal(dut):
    set_excepthook()
    tb = FPCPReciprocalTB(dut)
    tb.log.setLevel(logging.DEBUG)
    await tb.run_test(10)

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
            {"IN_EXP_WIDTH" : 4, "IN_MANT_WIDTH" : 3, "OUT_EXP_WIDTH" : 4, "OUT_MANT_WIDTH" : 3},
            {"IN_EXP_WIDTH" : 5, "IN_MANT_WIDTH" : 10, "OUT_EXP_WIDTH" : 5, "OUT_MANT_WIDTH" : 10},
        ],
        trace = False,
    )

if __name__ == "__main__":
    test_simple_fp_reciprocal()
