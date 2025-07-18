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

    # Drive input array - with packed arrays, construct the full bit vector
    vin_value = 0
    for i in range(N):
        val = int(v_in[i])
        # Place this WIDTH-bit value at the correct position in the packed array
        vin_value |= (val << (i * WIDTH))
    
    # INCORRECT - This treats vin as a packed array
    # dut.vin.value = vin_value  # Don't do this
    breakpoint()
    # CORRECT - Drive each element of the unpacked array individually
    for i in range(N):
        val = int(v_in[i])
        # In SystemVerilog: input logic vin [WIDTH-1:0] [N-1:0]
        # Access as dut.vin[i] for the i-th array element
        dut.vin[i].value = val

    dut.in_ready.value = 1

    await RisingEdge(dut.clk)
    dut.in_ready.value = 0

    # Wait for output ready
    while not dut.out_ready.value:
        await RisingEdge(dut.clk)

    # Read output array - extract values from the packed array
    # INCORRECT - This treats vout as a packed array
    # vout_value = int(dut.vout.value)  # Don't do this

    # CORRECT - Read each element individually
    actual = []
    for i in range(N):
        # Read the i-th element of the unpacked array
        val = int(dut.vout[i].value)
        actual.append(val)
    #
    breakpoint()
    assert actual == expected.tolist(), f"Expected {expected.tolist()}, got {actual}"
    cocotb.log.info(f"[PASS] Input: {v_in.tolist()}, Output: {actual}")
    # Add after connecting inputs but before starting the test
    cocotb.log.info(f"DUT attributes: {dir(dut)}")

    # For more specific inspection, also examine the exp_out and mant_out arrays
    if hasattr(dut, 'exp_out') and hasattr(dut, 'mant_out'):
        cocotb.log.info(f"exp_out type: {type(dut.exp_out)}")
        cocotb.log.info(f"exp_out attributes: {dir(dut.exp_out)}")
        
        # Check the first element's actual value and properties
        if len(dut.exp_out) > 0:
            cocotb.log.info(f"exp_out[0] type: {type(dut.exp_out[0])}")
            cocotb.log.info(f"exp_out[0] attributes: {dir(dut.exp_out[0])}")
            cocotb.log.info(f"exp_out[0] value: {dut.exp_out[0].value}")
@pytest.mark.dev
def test_simple_fp_addition():
    # Run tests with different params
    veri_runner(
        module = "prefix_scan_unpacked",     
        module_param_list=[
            {"N": 4, "WIDTH": 16},  # <-- Set these to match your test or DUT
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_simple_fp_addition()

