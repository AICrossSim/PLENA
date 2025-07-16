#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os
from pathlib import Path
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
from cfl_cocotb import veri_runner, MXBlockFPConverter
from math import ceil, log2
import math
import torch


logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)

@cocotb.test()
async def simple_prefix_scan_test(dut):
    N = int(dut.N)
    WIDTH = int(dut.WIDTH)

    # Start clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Optionally reset (if you add a reset to your SV)
    # dut.rst.value = 0
    # await Timer(5, units="ns")
    # dut.rst.value = 1
    # await Timer(5, units="ns")

    # Generate random input
    torch.manual_seed(0)
    max_val = 2**(WIDTH - 1) // N
    v_in = torch.randint(1, max_val, (N,), dtype=torch.int32)
    expected = torch.cumsum(v_in, dim=0)

    # Drive input array
    for i in range(N):
        dut.vin[i].value = int(v_in[i])
    dut.in_ready.value = 1

    await RisingEdge(dut.clk)
    dut.in_ready.value = 0

    # Wait for output ready
    while not dut.out_ready.value:
        await RisingEdge(dut.clk)

    # Read output array
    actual = [int(dut.vout[i].value) for i in range(N)]
    assert actual == expected.tolist(), f"Expected {expected.tolist()}, got {actual}"
    cocotb.log.info(f"[PASS] Input: {v_in.tolist()}, Output: {actual}")
@pytest.mark.dev
def test_simple_fp_addition():
    # Run tests with different params
    veri_runner(
        module = "prefix_scan",     
        module_param_list=[
            {"N": 4, "WIDTH": 16},  # <-- Set these to match your test or DUT
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_simple_fp_addition()

