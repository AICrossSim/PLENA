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
        from quant.quantizer import fixed_point_quantizer
        torch.random.manual_seed(10)
        q_config = {
            "in_fixed_width": self.dut.IN_FIXED_WIDTH.value,
            "in_fixed_frac_width": self.dut.IN_FIXED_FRAC_WIDTH.value,
            "in_exp_width": self.dut.IN_EXP_WIDTH.value,
            "out_mant_width": self.dut.OUT_MANT_WIDTH.value,
            "out_exp_width": self.dut.OUT_EXP_WIDTH.value,
        }

        signed_mant = torch.rand(num) * 3 - 1.5  # Random mantissa between -1 and 1
        signed_mant = fixed_point_quantizer(
            signed_mant, 
            q_config["in_fixed_width"], 
            q_config["in_fixed_frac_width"], 
            is_signed=True
        )
        signed_exp = torch.randint(-10, 10, num)  
        signed_exp = signed_exp.clamp(
            min=-2**(q_config["in_exp_width"] - 1), 
            max=2**(q_config["in_exp_width"] - 1) - 1)

        q_fp = signed_mant * 2**(signed_exp)

        from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware
        x, exponent, mantissa = _minifloat_ieee_quantize_hardware(
            q_fp, 
            q_config["out_mant_width"] + q_config["out_exp_width"] + 1, 
            q_config["out_exp_width"],
        )
        fp_bits = self.pack_fp_to_bin(exponent, mantissa)
        expected_output = hardware_ieee_normalize(signed_mant, signed_exp, q_config)
        expected_outputs = torch_fp2bin(expected_output, q_config).tolist()
        
        self.inputs = {
            "signed_mant": signed_mant.int().tolist(),
            "signed_exp": signed_exp.int().tolist()
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