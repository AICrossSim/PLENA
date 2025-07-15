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
from cfl_cocotb.torch_fp_conversion import fp_2_bin, bin_2_fp
from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware
from cfl_tools.debugger import set_excepthook, get_dut_attributes

logger = logging.getLogger("testbench")
logger.setLevel(logging.DEBUG)

src_path = Path(__file__).parent.parent.parent

torch.manual_seed(10)


class FPIEEECasting(CombinationalTestbench):
    def generate_inputs(self, num):
        self.q_config = {
            "in_exp_width": self.dut.IN_EXP_WIDTH.value,
            "in_man_width": self.dut.IN_MANT_WIDTH.value,
            "out_exp_width": self.dut.OUT_EXP_WIDTH.value,
            "out_man_width": self.dut.OUT_MANT_WIDTH.value,
        }
        
        # Generate random inputs between -1 and 1
        x = torch.rand(num) * 10 - 5

        q_x, fp_inputs = fp_2_bin(
            x, 
            self.q_config["in_exp_width"], 
            self.q_config["in_man_width"]
        )

        self.log.debug(f"Input Packed FP: {fp_inputs}")

        q_x, fp_outputs = fp_2_bin(
            q_x, 
            self.q_config["out_exp_width"], 
            self.q_config["out_man_width"]
        )

        self.log.debug(f"Output Packed FP: {fp_outputs}")

        self.inputs = {
            "data_in": fp_inputs.int().tolist(),
        }

        self.outputs = {
            "data_out": fp_outputs.int().tolist(),
        }
        
    def check_output(self, input, output):
        self.log.debug(f"Expected result : {input}, got: {int(output.integer)}")
        self.log.debug(f"----------------{self.dut}---------")
        get_dut_attributes(self.dut, self.log, None)

        assert input == int(output.integer), f"Expected {input}, but got {int(output.integer)}"

@cocotb.test()
async def test(dut):
    try:
        tb = FPIEEECasting(dut)
        tb.log.setLevel(logging.INFO)
        await tb.run_test(10)
    except Exception as e:
        set_excepthook()

if __name__ == "__main__":
    veri_runner(
        trace=True, 
        module="fp_ieee_upcasting",
        group="vector_machine",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/buffer"),
            str(SRC_PATH / "basic_components/fp_operation"),
            str(SRC_PATH / "basic_components/int_operation")
        ],
        module_param_list=[
            {
                "IN_EXP_WIDTH": 3,
                "IN_MANT_WIDTH": 5,
                "OUT_EXP_WIDTH": 5,
                "OUT_MANT_WIDTH": 8
            }
        ]
    )
