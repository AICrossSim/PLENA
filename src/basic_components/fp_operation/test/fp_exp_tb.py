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
    MultiSignalStreamDriver,
    MultiSignalStreamMonitor,
)
from cfl_cocotb.runner import veri_runner, SRC_PATH
from cfl_cocotb.torch_fp_conversion import fp_2_bin, bin_2_fp
from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware
from quant.quant_operations.exp import fp_exp_hardware

logger = logging.getLogger("testbench")
logger_level = logging.DEBUG
logger.setLevel(logger_level)

src_path = Path(__file__).parent.parent.parent

torch.manual_seed(10)


class FPExpTB(Testbench):
    def __init__(self, dut) -> None:
        super().__init__(dut, dut.clk, dut.rst)

        if not hasattr(self, "log"):
            self.log = SimLog("%s" % (type(self).__qualname__))
            self.log.setLevel(logging.DEBUG)

        # * QKV drivers
        self.in_driver = MultiSignalStreamDriver(
            dut.clk, (dut.signed_exp_in, dut.signed_mant_in), dut.data_in_valid, dut.data_in_ready
        )

        self.out_monitor = MultiSignalStreamMonitor(
            dut.clk,
            (dut.signed_exp_out, dut.signed_mant_out),
            dut.data_out_valid,
            dut.data_out_ready,
            check=True,
        )
        self.out_monitor.log.setLevel(logging.DEBUG)

    def generate_inputs(self, num):
        torch.manual_seed(0)
        q_config = {
            "in_exp_width": self.dut.IN_EXP_WIDTH.value,
            "in_fix_width": self.dut.IN_FIX_WIDTH.value,
            "in_fix_frac_width": self.dut.IN_FIX_FRAC_WIDTH.value,
            "extend_width": self.dut.EXTEND_WIDTH.value,
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

        self.inputs = [(int(a_exp[i]), int(a_mant[i]*2**(q_config["in_fix_frac_width"]))) for i in range(num)]
        self.outputs = [(int(expected_exp[i]), int(expected_mant[i]*2**(q_config["out_fix_frac_width"]))) for i in range(num)]

    async def run_test(self, us, num):
        await self.reset()
        self.log.info(f"Reset finished")
        self.out_monitor.ready.value = 1

        self.generate_inputs(num)   

        self.in_driver.load_driver(self.inputs)

        self.out_monitor.load_monitor(self.outputs)

        await Timer(us, units="us")
        assert self.out_monitor.exp_queue.empty()


@cocotb.test()
async def test(dut):
    tb = FPExpTB(dut)
    tb.log.setLevel(logger_level)
    await tb.run_test(20, 10)


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