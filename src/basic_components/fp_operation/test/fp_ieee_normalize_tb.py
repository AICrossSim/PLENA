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

logger = logging.getLogger("testbench")
logger.setLevel(logging.DEBUG)

src_path = Path(__file__).parent.parent.parent

torch.manual_seed(10)

def hardware_ieee_normalize(signed_mant, signed_exp, q_config):
    # Reconstruct the floating point number
    x = signed_mant * torch.pow(2, signed_exp)
    return x

class FPIEEENormalizeTB(CombinationalTestbench):
    def generate_inputs(self, num):
        q_config = {
            "exp_width": self.dut.EXP_WIDTH.value,
            "man_width": self.dut.MANT_WIDTH.value,
        }
        
        # Generate random inputs
        signed_mant = torch.rand(num) * 2 - 1  # Random mantissa between -1 and 1
        signed_exp = torch.randint(-2**(self.dut.EXP_WIDTH.value - 1), 2**(self.dut.EXP_WIDTH.value - 1) - 1, (num,))  # Random exponent between -10 and 10

        input_mant = (signed_mant * 2**int(self.dut.MANT_WIDTH.value)).round()

        expected_output = hardware_ieee_normalize(input_mant / 2**int(self.dut.MANT_WIDTH.value), signed_exp, q_config)
        expected_outputs = torch_fp2bin(expected_output, q_config).tolist()
        
        self.inputs = {
            "signed_mant": input_mant.int().tolist(),
            "signed_exp": signed_exp.tolist()
        }
        self.outputs = {
            "fp_out": expected_outputs
        }

@cocotb.test()
async def test(dut):
    tb = FPIEEENormalizeTB(dut)
    await tb.run_test(10)
    # try:
    #     tb = FPIEEENormalizeTB(dut)
    #     await tb.run_test(10)
    # except Exception as e:
    #     print("\nEntering debugger...")
    #     pdb.post_mortem(sys.exc_info()[2])

if __name__ == "__main__":
    veri_runner(
        trace=True, 
        module="fp_ieee_normalize",
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