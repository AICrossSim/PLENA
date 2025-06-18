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
from cfl_cocotb.torch_fp_conversion import torch_fp2bin
from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware, pack_fp_to_bin

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

        q_x, in_exponent, in_mantissa = _minifloat_ieee_quantize_hardware(
            x, 
            self.q_config["in_man_width"] + self.q_config["in_exp_width"] + 1, 
            self.q_config["in_exp_width"],
        )

        fp_inputs = pack_fp_to_bin(
            in_exponent, 
            in_mantissa, 
            self.q_config["in_exp_width"], 
            self.q_config["in_man_width"]
        )

        self.log.debug(f"Input Exponent: {in_exponent}")
        self.log.debug(f"Input Mantissa: {in_mantissa}")
        self.log.debug(f"Input Packed FP: {fp_inputs}")

        q_out, out_exponent, out_mantissa = _minifloat_ieee_quantize_hardware(
            q_x, 
            self.q_config["out_exp_width"],
        )

        fp_outputs = pack_fp_to_bin(
            out_exponent, 
            out_mantissa, 
            self.q_config["out_exp_width"], 
            self.q_config["out_man_width"]
        )

        self.log.debug(f"Output Exponent: {out_exponent}")
        self.log.debug(f"Output Mantissa: {out_mantissa}")
        self.log.debug(f"Output Packed FP: {fp_outputs}")

        self.inputs = {
            "data_in": fp_inputs.int().tolist(),
        }

        self.outputs = {
            "data_out": fp_outputs.int().tolist(),
        }
        
    def check_output(self, input, output):
        self.log.debug(f"Expected result : {input}, got: {int(output.signed_integer)}")
        assert input == int(output.signed_integer), f"Expected {input}, but got {int(output.signed_integer)}"

@cocotb.test()
async def test(dut):
    tb = FPIEEECasting(dut)
    tb.log.setLevel(logging.INFO)
    await tb.run_test(10)
    # try:
    #     tb = FPIEEEOperationsTB(dut)
    #     await tb.run_test(10)
    # except Exception as e:
    #     print("\nEntering debugger...")
    #     pdb.post_mortem(sys.exc_info()[2])

if __name__ == "__main__":
    veri_runner(
        trace=True, 
        module="fp_ieee_casting",
        group="vector_machine",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/buffer")
        ],
        module_param_list=[
            {
                "EXP_WIDTH": 4,
                "MANT_WIDTH": 8
            }
        ]
    )
