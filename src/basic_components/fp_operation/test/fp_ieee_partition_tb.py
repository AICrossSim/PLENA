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

def fp_quantize(x, q_config):
    man_width = q_config["man_width"]
    exp_width = q_config["exp_width"]
    return x

def hardware_ieee_partition(x, q_config):
    sign = torch.sign(x)

    exp_width = q_config["exp_width"]
    man_width = q_config["man_width"]
    # Get raw exponent and mantissa
    exponent = torch.zeros_like(x)
    # Handle non-zero values: calculate log2 and floor it to get exponent
    non_zero_mask = x != 0
    if non_zero_mask.any():
        exponent[non_zero_mask] = torch.floor(torch.log2(torch.abs(x[non_zero_mask])))
    
    # Handle zero values: set exponent to 0
    exponent[~non_zero_mask] = 0
    mantissa_val = x / (2 ** exponent) - 1.0  # remove leading 1
    # Bias the exponent
    bias = (2**(exp_width - 1)) - 1

    # Mantissa
    mantissa_bits = (mantissa_val * 2**man_width).floor()
    return sign*mantissa_bits, exponent



class FPIEEEPartitionTB(CombinationalTestbench):
    def generate_inputs(self, num):
        q_config = {
            "exp_width": self.dut.EXP_WIDTH.value,
            "man_width": self.dut.MANT_WIDTH.value,
        }
        
        # Generate random inputs between -1 and 1
        x = torch.rand(num) * 2 - 1
        
        # For sqrt, ensure inputs are positive
        x_sqrt = torch.abs(x)
        
        # Convert inputs to binary format
        inputs = torch_fp2bin(x, q_config).tolist()
        
        # Compute expected outputs
        signed_mant, signed_exp = hardware_ieee_partition(x, q_config)
        
        # Convert outputs to binary format
        self.inputs = {
            "data_in": inputs,
        }
        self.outputs = {
            "signed_mant": signed_mant.int().tolist(),
            "signed_exp": signed_exp.int().tolist(),
        }

@cocotb.test()
async def test(dut):
    tb = FPIEEEPartitionTB(dut)
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
