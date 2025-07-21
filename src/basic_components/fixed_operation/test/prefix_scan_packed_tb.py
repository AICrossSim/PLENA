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

    # Generate random input
    torch.manual_seed(0)
    max_val = 2**(WIDTH - 1) // N
    v_in = torch.randint(1, max_val, (N,), dtype=torch.int32)
    expected = torch.cumsum(v_in, dim=0)
    
    
    #breakpoint()
      # Assign each element to the packed input
    # Drive input array - assign each element individually
    # dut.in_ready.value = 1
    # for i in range(1,N):
    #     val = int(v_in[i]) & ((1 << WIDTH) - 1)  # Mask to WIDTH bits
    #     dut.vin.value.set_value[WIDTH* (i-1):WIDTH*(i)] = val
    dut.in_ready.value = 1
    packed = 0
    for i in range(N):
        elem = int(v_in[i]) & ((1<<WIDTH)-1)
        packed |= elem << (i*WIDTH)
    # assign the full N*WIDTH‑bit vector in one go
    dut.vin.value = packed
    await RisingEdge(dut.clk)
    dut.in_ready.value = 0
    #breakpoint()
    # Wait for output ready
    while not dut.out_ready.value:
        await RisingEdge(dut.clk)
    temp = dut.vout.value
    # Unpack output values from packed array
    # vout is [WIDTH-1:0][N-1:0] - WIDTH separate N-bit values
    actual = []
    for i in range(N):
        actual.append(temp >> (i * WIDTH) & ((1 << WIDTH) - 1))
    
    assert actual == expected.tolist(), f"Expected {expected.tolist()}, got {actual}"
    cocotb.log.info(f"[PASS] Input: {v_in.tolist()}, Output: {actual}")
    cocotb.log.info(f"DUT attributes: {dir(dut)}")


@pytest.mark.dev
def test_simple_fp_addition():
    # Run tests with different params
    veri_runner(
        module = "prefix_scan_packed",     
        module_param_list=[
            {"N": 4, "WIDTH": 16},  # <-- Set these to match your test or DUT
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_simple_fp_addition()

