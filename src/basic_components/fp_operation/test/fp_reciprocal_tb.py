#!/usr/bin/env python3

import logging, pdb, sys, traceback
import torch, math
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
from cfl_cocotb.torch_fp_conversion import fp_2_bin, bin_2_fp, pack_fp_to_bin
from quant.quant_operations.reciprocal import fp_reciprocal
from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware

logger = logging.getLogger("testbench")
logger.setLevel(logging.DEBUG)

src_path = Path(__file__).parent.parent.parent

torch.manual_seed(10)

class FPReciprocalTB(CombinationalTestbench):
    def generate_inputs(self, num):
        q_config = {
            "in_exp_width": self.dut.IN_EXP_WIDTH.value,
            "in_fix_width": self.dut.IN_FIX_WIDTH.value,
            "in_fix_frac_width": self.dut.IN_FIX_FRAC_WIDTH.value,
            "out_exp_width": self.dut.OUT_EXP_WIDTH.value,
            "out_fix_width": self.dut.OUT_FIX_WIDTH.value,
            "out_fix_frac_width": self.dut.OUT_FIX_FRAC_WIDTH.value,
        }
        
        # Generate random inputs between -1 and 1, avoiding very small numbers
        x = torch.rand(num) * 2 - 1
        x[torch.abs(x) < 0.1] = 0.1  # Avoid division by very small numbers
        
        qx, exp_x, mant_x = _minifloat_ieee_quantize_hardware(
            x, q_config["in_fix_frac_width"] + q_config["in_exp_width"] + 1, q_config["in_exp_width"])
        # Convert inputs to binary format
        inputs = pack_fp_to_bin(exp_x, mant_x, q_config["in_exp_width"], q_config["in_fix_width"]).tolist()
        
        # Compute expected outputs
        expected_exp, expected_mant = fp_reciprocal(exp_x, mant_x, q_config)
        expected_outputs = pack_fp_to_bin(expected_exp, expected_mant, q_config["out_exp_width"], q_config["out_fix_width"]).tolist()
        
        self.inputs = {
            "signed_mant_in": mant_x.int().tolist(),
            "signed_exp_in": exp_x.int().tolist(),
        }
        self.outputs = {
            "signed_exp_out": expected_exp.int().tolist(),
            "signed_mant_out": expected_mant.int().tolist(),
        }

@cocotb.test()
async def test(dut):
    tb = FPReciprocalTB(dut)
    await tb.run_test(10)

if __name__ == "__main__":
    veri_runner(
        trace=True, 
        module="fp_reciprocal",
        group="fp_operation",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/buffer")
        ],
        module_param_list=[
            {
                "IN_EXP_WIDTH": 4,
                "IN_FIX_WIDTH": 8,
                "IN_FIX_FRAC_WIDTH": 5,
                "OUT_EXP_WIDTH": 4,
                "OUT_FIX_WIDTH": 8,
                "OUT_FIX_FRAC_WIDTH": 5
            }
        ]
    )
