#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os
import torch

from cocotb.triggers import Timer
from cfl_cocotb import veri_runner
from cfl_cocotb.runner import SRC_PATH
from cfl_cocotb.testbench import CombinationalTestbench
from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware
from cfl_cocotb.torch_fp_conversion import pack_fp_to_bin

class FPCompareTB(CombinationalTestbench):
    def generate_inputs(self, num):
        exp_width = self.dut.EXP_WIDTH.value
        mant_width = self.dut.MANT_WIDTH.value
        total_width = exp_width + mant_width + 1

        torch.manual_seed(0)
        # Generate random floats
        torch_a = torch.randn(num) * 10
        torch_b = torch.randn(num) * 10
        
        # Add some edge cases: identical values, opposite signs of same magnitude, zeros
        torch_a = torch.cat([torch_a, torch.tensor([0.0, 1.0, -1.0, 2.5, 2.5, 0.0])])
        torch_b = torch.cat([torch_b, torch.tensor([0.0, 1.0, 1.0, 2.5, -2.5, -0.0])])
        num += 6

        # Quantize to the hardware format
        qa, a_exp, a_mant = _minifloat_ieee_quantize_hardware(torch_a, total_width - 1, exp_width)
        qb, b_exp, b_mant = _minifloat_ieee_quantize_hardware(torch_b, total_width - 1, exp_width)


        packed_a = pack_fp_to_bin(a_exp, a_mant, exp_width, mant_width).tolist()
        packed_b = pack_fp_to_bin(b_exp, b_mant, exp_width, mant_width).tolist()

        self.inputs = {
            "data_a": packed_a,
            "data_b": packed_b,
        }

        # Expected results using torch's comparison on quantized values
        self.outputs = {
            "a_gt_b": (qa > qb).int().tolist(),
            "a_lt_b": (qa < qb).int().tolist(),
            "a_eq_b": (qa == qb).int().tolist(),
        }

    def check_output(self, expected, output):
        # CombinationalTestbench calls this per-port if self.outputs is a dict.
        # 'expected' is the scalar value from the list in self.outputs[port_name]
        # 'output' is the value of the port from the DUT.
        assert int(output) == int(expected), f"Mismatch! Expected {expected}, got {output}"

@cocotb.test()
async def test(dut):
    tb = FPCompareTB(dut)
    tb.log.setLevel(logging.DEBUG)
    await tb.run_test(50)

@pytest.mark.dev
def test_fp_compare():
    veri_runner(
        group = "fp_operation",
        module = "fp_compare",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
        ],
        module_param_list=[
            {"EXP_WIDTH": 5, "MANT_WIDTH": 10},
            {"EXP_WIDTH": 4, "MANT_WIDTH": 3},
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_fp_compare()
