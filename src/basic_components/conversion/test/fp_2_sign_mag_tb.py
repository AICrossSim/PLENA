#!/usr/bin/env python3

# This script tests the fixed point linear
import logging, pdb, sys, traceback, os

import torch, math

from pathlib import Path

import cocotb
from cocotb.log import SimLog
from cocotb.triggers import *

from cfl_cocotb.testbench import Testbench
from cfl_cocotb.streaming import (
    StreamDriver,
    StreamMonitor,
)
from cfl_cocotb.runner import veri_runner
from cfl_cocotb.torch_fp_conversion import torch_fp2bin

logger = logging.getLogger("testbench")
logger.setLevel(logging.DEBUG)

SRC_PATH = os.environ.get('SRC_PATH')
if SRC_PATH is None:
    src_path = Path(__file__).parent.parent.parent
else:
    src_path = Path(SRC_PATH)

torch.manual_seed(10)

class FP2SignMagTB(Testbench):
    def __init__(self, dut) -> None:
        super().__init__(dut)
        if not hasattr(self, "log"):
            self.log = SimLog("%s" % (type(self).__qualname__))

    async def run_test(self, num, time_us):
        await Timer(5, units="ns")
        cocotb.log.info("Starting fp addition test")
        config = {
            "exp_width": self.dut.FP_EXP_WIDTH.value, 
            "man_width": self.dut.FP_MANT_WIDTH.value,
            "sign_mag_width": self.dut.SIGN_MAG_WIDTH.value,
            "sign_mag_frac_width": self.dut.SIGN_MAG_FRAC_WIDTH.value,
        }
        for i in range (num):
            # Generate random floating point values
            # fp_values, results = generator.generate_fp_input(2)
            x = torch.randn(1)
            qx = torch_fp2bin(x, {
                "exp_width": config["exp_width"],
                "man_width": config["man_width"],
            })
            int_x = (qx.abs() * 2**config["sign_mag_frac_width"]).round()
            if qx.sign() == 1:
                sign_mag_x = -int_x + 2**(config["sign_mag_width"] - 1)
            else:
                sign_mag_x = int_x

            await Timer(1, units="ns")

            await Timer(1, units="ns")

            # assert sign_mag_x == self.dut.data_out.value
            self.log.warning(f"we dont check it!!!")
        await Timer(10, units="ns")

@cocotb.test()
async def test(dut):
    tb = FP2SignMagTB(dut)
    await tb.run_test(10, 1000)
    # try:
    #     tb = FPExpTB(dut)
    #     await tb.run_test(10, 1000)
    # except Exception as e:
    #     print("\nEntering debugger...")
    #     pdb.post_mortem(sys.exc_info()[2])

# async def check_signal(dut):
#     while True:
#         await RisingEdge(dut.clk)
#         if dut.data_in_valid.value == 1 and dut.data_in_ready.value == 1:
#             print(f"data_in: {dut.data_in.value}")
#         if dut.data_out_valid.value == 1 and dut.data_out_ready.value == 1:
#             print(f"data_out: {dut.data_out.value}")

if __name__ == "__main__":
    veri_runner(
        trace=True, 
        module="fp_2_sign_mag",
        group="vector_machine",
        additional_include_paths=[
            str(src_path / "basic_components/common"),
            str(src_path / "basic_components/conversion"),
            str(src_path / "basic_components/fixed_operation"),
        ],
        module_param_list=[
            {
                "FP_EXP_WIDTH": 4,
                "FP_MANT_WIDTH": 8,
                "SIGN_MAG_WIDTH": 4,
                "SIGN_MAG_FRAC_WIDTH": 4
            }
        ]
    )