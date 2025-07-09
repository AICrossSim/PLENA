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
from cfl_tools.logger import get_logger

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)
class FPCPExpTB(CombinationalTestbench):
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
        torch_x = torch.randn(num) * 2.5
        # Replace values too close to zero with reasonable values
        torch_x[torch.abs(torch_x) < 0.1] = torch.sign(torch_x[torch.abs(torch_x) < 0.1]) * 0.5

        in_width = q_config["in_mant_width"] + q_config["in_exp_width"]
        in_exponent_width = q_config["in_exp_width"]

        # Quantize input
        qx, x_exp, x_mant = _minifloat_ieee_quantize_hardware(torch_x, in_width, in_exponent_width)

        from quant.quant_operations.exp import fp_exp_hardware
        # Calculate reciprocal: 1/x
        exp_harware_config = {
            "in_fix_width": self.dut.EXP_IN_FIXED_WIDTH.value,    
            "in_fix_frac_width": self.dut.EXP_IN_FIXED_FRAC_WIDTH.value,
            "in_exp_width": self.dut.EXP_IN_EXP_WIDTH.value,
            "extend_width": self.dut.EXTEND_WIDTH.value,
            "out_fix_width": self.dut.EXP_OUT_FIXED_WIDTH.value,
            "out_fix_frac_width": self.dut.EXP_OUT_FIXED_FRAC_WIDTH.value,
            "out_exp_width": self.dut.EXP_OUT_EXP_WIDTH.value,
        }
        exp_out_exp, exp_out_mant = fp_exp_hardware(x_exp, x_mant, exp_harware_config)
        hardware_result = exp_out_mant * 2**(exp_out_exp)
        logger.debug(f"exp_out_mant: {exp_out_mant}")
        logger.debug(f"exp_out_exp: {exp_out_exp}")
        logger.debug(f"hardware_result: {hardware_result}")


        
        # Quantize output
        out_width = q_config["out_mant_width"] + q_config["out_exp_width"] + 1
        out_exponent_width = q_config["out_exp_width"]

        # Pack inputs and outputs to binary format
        inputs_x = pack_fp_to_bin(x_exp, x_mant, q_config["in_exp_width"], q_config["in_mant_width"])
        from quant.quant_operations.cast import fp_cast_hardware
        q_out = fp_cast_hardware(hardware_result, q_config)
        q_out, q_out_exp, q_out_mant = _minifloat_ieee_quantize_hardware(q_out, out_width, out_exponent_width)
        outputs_out = pack_fp_to_bin(q_out_exp, q_out_mant, q_config["out_exp_width"], q_config["out_mant_width"])

        self.inputs = {
            "data_in": inputs_x.int().tolist(),
        }

        self.log.debug("input : {}, {}, {}".format(qx, x_exp, x_mant))
        self.log.debug("output : {}, {}, {}".format(q_out, q_out_exp, q_out_mant))
        self.outputs = {
            "data_out": outputs_out.int().tolist(),
        }
    def check_output(self, expected_output, hardware_output):
        self.log.debug(f"----------------{self.dut}---------")
        from cfl_tools.debugger import get_dut_attributes
        # get_dut_attributes(self.dut, self.log, 'signed_integer')
        get_dut_attributes(self.dut, self.log)
        self.log.debug(f"expected_output: {expected_output}, hardware_output: {int(hardware_output.signed_integer)}")

        self.log.debug(f"exp_out_mant: {self.dut.exp_out_mant.value.signed_integer}")
        self.log.debug(f"exp_out_exp: {self.dut.exp_out_exp.value.signed_integer}")
        result = self.dut.exp_out_mant.value.signed_integer * 2**(self.dut.exp_out_exp.value.signed_integer)
        self.log.debug(f"result: {result}")
        # get_dut_attributes(self.dut.fp_exp_inst.taylor_series_expansion_inst, self.log, "integer")
        get_dut_attributes(self.dut.fp_normalize, self.log, "signed_integer")
        get_dut_attributes(self.dut.fp_normalize, self.log)
        # get_dut_attributes(self.dut.taylor_series_expansion_inst, self.log, 'integer')
        
        assert expected_output == hardware_output.signed_integer, f"Expected {expected_output}, but got {int(hardware_output.signed_integer)}"

@cocotb.test()
async def test_fp_cp_exp(dut):
    tb = FPCPExpTB(dut)
    tb.log.setLevel(logging.DEBUG)
    await tb.run_test(10)

@pytest.mark.dev
def test_simple_fp_exp():
    # Run tests with different params
    veri_runner(
        group = "fp_operation",
        module = "fp_cp_exp",
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
            # {"IN_EXP_WIDTH" : 5, "IN_MANT_WIDTH" : 10, "OUT_EXP_WIDTH" : 5, "OUT_MANT_WIDTH" : 10},
        ],
        trace = False,
    )

if __name__ == "__main__":
    test_simple_fp_exp()
