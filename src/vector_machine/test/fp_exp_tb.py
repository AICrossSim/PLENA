#!/usr/bin/env python3

# This script tests the fixed point linear
import logging, pdb, sys, traceback

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

src_path = Path(__file__).parent.parent.parent

torch.manual_seed(10)

def fp_quantize(x, q_config):
    # TODO: 
    man_width = q_config["man_width"]
    exp_width = q_config["exp_width"]
    return x

def hardware_exp(x, q_config):
    # TODO: currently, this software model cannot exactly match the hardware due to.
    # 1. Hardware FP is not confirmed
    # The constant e in torch can be accessed using torch.exp(torch.tensor(1.0))
    # or using math.e and converting to tensor if needed
    log2_e = torch.log2(torch.tensor(math.e))  # log base 2 of e
    log2_e_x = x * log2_e
    q_x = fp_quantize(x, q_config)
    _int = q_x.floor()
    _frac = q_x - _int
    # Calculate 2^_frac using Taylor series expansion
    # 2^x = 1 + x*ln(2) + (x*ln(2))^2/2! + (x*ln(2))^3/3! + ...
    # For _frac (the fractional part), we can use this expansion
    # First term: 1
    result = torch.ones_like(_frac)
    
    # Second term: _frac * ln(2)
    ln2 = torch.tensor(math.log(2))
    term = _frac * ln2
    result += term
    
    # Third term: (_frac * ln(2))^2 / 2!
    term = term * _frac * ln2 / 2
    result += term
    
    # Fourth term: (_frac * ln(2))^3 / 3!
    term = term * _frac * ln2 / 3
    result += term
    
    # Fifth term: (_frac * ln(2))^4 / 4!
    term = term * _frac * ln2 / 4
    result += term
    
    # Combine integer and fractional parts: 2^_int * 2^_frac
    final_result = torch.pow(2, _int) * result
    return fp_quantize(final_result, q_config)

    
class FPExpTB(Testbench):
    def __init__(self, dut) -> None:
        super().__init__(dut, dut.clk, dut.rst)
        if not hasattr(self, "log"):
            self.log = SimLog("%s" % (type(self).__qualname__))

        self.data_in_0_driver = StreamDriver(
            dut.clk,
            dut.data_in,
            dut.data_in_valid,
            dut.data_in_ready,
        )

        self.data_out_0_monitor = StreamMonitor(
            dut.clk,
            dut.data_out,
            dut.data_out_valid,
            dut.data_out_ready,
            check=False,
        )
        self.data_in_0_driver.log.setLevel(logging.DEBUG)
        self.data_out_0_monitor.log.setLevel(logging.DEBUG)

    def generate_inputs(self, num=10):
        q_config = {
                "man_width": self.get_parameter("MANT_WIDTH"),
                "exp_width": self.get_parameter("EXP_WIDTH"),
        }
        # Generate random input
        x = torch.rand(num) * 2 - 1  # Random number between -1 and 1
        inputs = torch_fp2bin(x, q_config).tolist()
        # Calculate expected output
        y = hardware_exp(x, q_config)
        expected_outputs = torch_fp2bin(y, q_config).tolist()
        return inputs, expected_outputs

    async def run_test(self, num, time_us):
        await self.reset()
        self.log.info("Reset finished")
        self.data_out_0_monitor.ready.value = 1

        inputs, expected_outputs = self.generate_inputs(num)
        self.data_in_0_driver.load_driver(inputs)
        self.data_out_0_monitor.load_monitor(expected_outputs)
        await Timer(time_us, units="us")
        assert self.data_out_0_monitor.exp_queue.empty()


@cocotb.test()
async def test(dut):
    tb = FPExpTB(dut)
    await tb.run_test(10, 1000)
    # try:
    #     tb = FPExpTB(dut)
    #     await tb.run_test(10, 1000)
    # except Exception as e:
    #     print("\nEntering debugger...")
    #     pdb.post_mortem(sys.exc_info()[2])

async def check_signal(dut):
    while True:
        await RisingEdge(dut.clk)
        if dut.data_in_valid.value == 1 and dut.data_in_ready.value == 1:
            print(f"data_in: {dut.data_in.value}")
        if dut.data_out_valid.value == 1 and dut.data_out_ready.value == 1:
            print(f"data_out: {dut.data_out.value}")

if __name__ == "__main__":
    veri_runner(
        trace=True, 
        module="fp_exp",
        group="vector_machine",
        additional_include_paths=[
            str(src_path / "basic_components/common"),
            str(src_path / "basic_components/conversion"),
            str(src_path / "basic_components/fixed_operation"),
            str(src_path / "basic_components/buffer")
        ],
        module_param_list=[
            {
                "EXP_WIDTH": 4,
                "MANT_WIDTH": 8
            }
        ]
    )