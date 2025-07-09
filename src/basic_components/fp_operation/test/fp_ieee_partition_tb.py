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

logger = logging.getLogger("testbench")
logger.setLevel(logging.DEBUG)

src_path = Path(__file__).parent.parent.parent

torch.manual_seed(10)

class FPIEEEPartitionTB(CombinationalTestbench):
    def generate_inputs(self, num):

        self.q_config = {
            "exp_width": self.dut.EXP_WIDTH.value,
            "man_width": self.dut.MANT_WIDTH.value,
        }
        
        # Generate random inputs between -1 and 1
        x = torch.rand(num) * self.range - self.range / 2

        from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware
        x, exponent, mantissa = _minifloat_ieee_quantize_hardware(
            x, 
            self.q_config["man_width"] + self.q_config["exp_width"] + 1, 
            self.q_config["exp_width"],
        )
        
        fp_bits = pack_fp_to_bin(exponent, mantissa, self.q_config["exp_width"], self.q_config["man_width"])

        self.log.debug(f"Exponent: {exponent}")
        self.log.debug(f"Mantissa: {mantissa}")
        self.log.debug(f"Packed FP: {fp_bits}")

        # Convert inputs to binary format
        inputs = fp_bits.int().tolist()
        
        signed_mant = mantissa * 2**(self.q_config["man_width"])

        # Convert outputs to binary format
        self.inputs = {
            "data_in": fp_bits.int().tolist(),
        }
        self.outputs = {
            "signed_exp": exponent.int().tolist(),
            "signed_mant": signed_mant.int().tolist(),
        }
        
    def check_output(self, input, output):
        self.log.debug(f"Expected result : {input}, got: {int(output.signed_integer)}")
        assert input == output.signed_integer, f"Expected {input}, but got {int(output.signed_integer)}"

import math
# def convert_to_twos_complement(x):
#     width = math.ceil(math.log2(abs(x)))
#     if x % 2**width == 0:
#         width += 1
#     if x < 0:
#         return x + (1 << (width+1))
#     return x

@cocotb.test()
async def test(dut):
    tb = FPIEEEPartitionTB(dut)
    tb.log.setLevel(logging.DEBUG)
    tb.range = 100
    await tb.run_test(num=100)
    # try:
    #     tb = FPIEEEOperationsTB(dut)
    #     await tb.run_test(10)
    # except Exception as e:
    #     print("\nEntering debugger...")
    #     pdb.post_mortem(sys.exc_info()[2])

if __name__ == "__main__":
    veri_runner(
        trace=True, 
        module="fp_ieee_partition",
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
