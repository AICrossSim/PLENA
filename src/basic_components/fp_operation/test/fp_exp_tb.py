#!/usr/bin/env python3

# This script tests the fixed point exponential function
import logging, pdb, sys, traceback

from mpmath import ln2, taylor
import torch, math
import numpy as np

from pathlib import Path

import cocotb
from cocotb.log import SimLog
from cocotb.triggers import *

from cfl_cocotb.testbench import Testbench, CombinationalTestbench
from cfl_cocotb.streaming import (
    StreamDriver,
    StreamMonitor,
)
from cfl_cocotb.runner import veri_runner, SRC_PATH
from cfl_cocotb.torch_fp_conversion import fp_2_bin, bin_2_fp
from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware
from quant.quant_operations.exp import fp_exp_hardware

logger = logging.getLogger("testbench")
logger_level = logging.INFO
logger.setLevel(logger_level)

src_path = Path(__file__).parent.parent.parent

torch.manual_seed(10)



class FPExpTB(CombinationalTestbench):
    def generate_inputs(self, num):
        torch.manual_seed(0)
        q_config = {
            "in_exp_width": self.dut.IN_EXP_WIDTH.value,
            "in_fix_width": self.dut.IN_FIX_WIDTH.value,
            "in_fix_frac_width": self.dut.IN_FIX_FRAC_WIDTH.value,
            "extend_exp_width": self.dut.EXTEND_WIDTH.value,
            "out_exp_width": self.dut.OUT_EXP_WIDTH.value,
            "out_fix_width": self.dut.OUT_FIX_WIDTH.value,
            "out_fix_frac_width": self.dut.OUT_FIX_FRAC_WIDTH.value,
        }
        
        # Generate test inputs
        a = torch.randn(num) * 3
        qa, a_exp, a_mant = _minifloat_ieee_quantize_hardware(a, q_config["in_fix_frac_width"] + q_config["in_exp_width"] + 1, q_config["in_exp_width"])
        
        # Generate mantissa values
        mant = torch.rand(num) * 2 - 1  # Range [-1, 1]
        int_mant = (mant * 2**(q_config["in_fix_frac_width"])).round().long()
        
        # Calculate expected outputs using hardware model
        expected_exp, expected_mant = fp_exp_hardware(a_exp, a_mant, q_config)

        self.inputs = {
            "signed_exp_in": a_exp.int().tolist(),
            "signed_mant_in": (a_mant*2**(q_config["in_fix_frac_width"])).int().tolist(),
        }
        self.outputs = {
            "signed_exp_out": expected_exp.int().tolist(),
            "signed_mant_out": (expected_mant * 2**(q_config["out_fix_frac_width"])).int().tolist(),
        }
    
    def check_output(self, expected_output, hardware_output):
        self.log.debug(f"----------------{self.dut}---------")
        from cfl_tools.debugger import get_dut_attributes
        # get_dut_attributes(self.dut, self.log, 'signed_integer')
        get_dut_attributes(self.dut, self.log)
        self.log.debug(f"expected_output: {expected_output}, hardware_output: {int(hardware_output.signed_integer)}")
        get_dut_attributes(self.dut.taylor_series_expansion_inst, self.log, 'integer')
        
        assert expected_output == hardware_output.signed_integer, f"Expected {expected_output}, but got {int(hardware_output.signed_integer)}"


@cocotb.test()
async def test(dut):
    tb = FPExpTB(dut)
    tb.log.setLevel(logger_level)
    await tb.run_test(20)


if __name__ == "__main__":
    veri_runner(
        trace=True, 
        module="fp_exp",
        group="fp_operation",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/int_operation"),
            str(SRC_PATH / "basic_components/buffer"),
        ],
        module_param_list=[
            {
                "IN_EXP_WIDTH": 8,
                "IN_FIX_WIDTH": 7,
                "IN_FIX_FRAC_WIDTH": 5,
                "EXTEND_WIDTH": 5,
                "OUT_EXP_WIDTH": 8,
                "OUT_FIX_WIDTH": 8,
                "OUT_FIX_FRAC_WIDTH": 5
            }
        ]
    )