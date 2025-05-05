#!/usr/bin/env python3

# This script tests the fixed point linear
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

def hardware_sqrt(x, q_config):
    # Convert to binary and back to get exact hardware representation
    
    # Compute square root
    y = torch.sqrt(torch.abs(x))
    
    # Handle special cases
    y[torch.isnan(y)] = 0
    y[torch.isinf(y)] = 0
    
    return y

class FPSqrtTB(CombinationalTestbench):
    def generate_inputs(self, num):
        q_config = {
            "exp_width": self.dut.EXP_WIDTH.value,
            "man_width": self.dut.MANT_WIDTH.value,
        }
        
        # Generate random positive inputs
        x = torch.rand(num)  # Random numbers between 0 and 1
        
        # Convert inputs to binary format
        inputs = torch_fp2bin(x, q_config).tolist()
        
        # Compute expected outputs
        expected_output = hardware_sqrt(x, q_config)
        expected_outputs = torch_fp2bin(expected_output, q_config).tolist()
        
        self.inputs = {
            "data_in": inputs
        }
        self.outputs = {
            "data_out": expected_outputs
        }


@cocotb.test()
async def test(dut):
    tb = FPSqrtTB(dut)
    await tb.run_test(10)


if __name__ == "__main__":
    veri_runner(
        trace=True, 
        module="fp_cp_sqrt",
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