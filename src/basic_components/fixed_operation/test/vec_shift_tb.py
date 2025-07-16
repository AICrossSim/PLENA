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
async def simple_shift_test(dut):
    VLEN = int(dut.VLEN)
    VDEPTH = int(dut.VDEPTH)

    # Start clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Generate random input
    torch.manual_seed(0)
    max_val = 2**(VLEN - 1) // VDEPTH  # Fixed: use VLEN for bit width
    shift_amount = 3
    v_in = torch.randint(1, max_val, (VDEPTH,), dtype=torch.int32)  # Fixed: VDEPTH elements
    
    # Calculate expected output: shift down by shift_amount, fill with zeros
    expected = [0] * shift_amount + v_in[:-shift_amount].tolist()

    # Drive shift signal
    dut.shift.value = shift_amount
    
    # Drive input array
    for i in range(VDEPTH):  # Fixed: iterate over VDEPTH
        dut.V_in[i].value = int(v_in[i])
    dut.v_in_ready.value = 1

    await RisingEdge(dut.clk)
    dut.v_in_ready.value = 0

    # Wait for output ready
    while not dut.v_out_ready.value:
        await RisingEdge(dut.clk)

    # Read output array
    actual = [int(dut.V_out[i].value) for i in range(VDEPTH)]  # Fixed: VDEPTH elements
    assert actual == expected, f"Expected {expected}, got {actual}"
    cocotb.log.info(f"[PASS] Input: {v_in.tolist()}, Shift: {shift_amount}, Output: {actual}")

@pytest.mark.dev
def test_simple_fp_addition():
    # Run tests with different params
    veri_runner(
        module = "vec_shift",     
        module_param_list=[
            {"VLEN": 32, "VDEPTH": 8},
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_simple_fp_addition()

