#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os
from cfl_cocotb.runner import SRC_PATH
from pathlib import Path
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
from cfl_cocotb import veri_runner, MXBlockFPConverter
from math import ceil, log2
import math
import torch
from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware
from cfl_cocotb.torch_fp_conversion import pack_fp_to_bin

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)
EXP_WIDTH = 5
MANT_WIDTH = 10
@cocotb.test()
async def simple_shift_test(dut):
    VLEN = int(dut.VLEN.value)
    VDEPTH = int(dut.VDEPTH.value)
    global EXP_WIDTH, MANT_WIDTH
    width = EXP_WIDTH + MANT_WIDTH + 1
    # Start clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Generate random input
    torch.manual_seed(0)
    max_val = 2**(VLEN - 1) // VDEPTH  # Fixed: use VLEN for bit width
    shift_amount = 2
    v_in = torch.randn(VDEPTH)
    qa, a_exp, a_mant = _minifloat_ieee_quantize_hardware(v_in, VLEN, EXP_WIDTH)
    inputs_a = pack_fp_to_bin(
        a_exp, a_mant, EXP_WIDTH, MANT_WIDTH)
    # Calculate expected output: shift down by shift_amount, fill with zeros
    out = [0] * shift_amount + v_in[:-shift_amount].tolist()
    out_tensor = torch.tensor(out)
    # Drive shift signal
    dut.shift.value = shift_amount
    v_packed = 0
    # Drive input array
    for i, value in enumerate(inputs_a):
        v_packed |= (value << (i * width))
    dut.v_in_ready.value = 1
    dut.V_in.value = int(v_packed)
    await RisingEdge(dut.clk)
    dut.v_in_ready.value = 0
    qout, out_exp, out_mant = _minifloat_ieee_quantize_hardware(out_tensor, width, EXP_WIDTH)
    outputs_out = pack_fp_to_bin(
        out_exp, out_mant,
        EXP_WIDTH, MANT_WIDTH)
    # Wait for output ready
    while not dut.v_out_ready.value:
        await RisingEdge(dut.clk)
    vout_packed = dut.V_out.value
    # Read output array
    actual=[]
    for i in range(VDEPTH):
        value = int(vout_packed >> (i * width)) & ((1 << width) - 1)
        actual.append(value)
    actual = torch.tensor(actual)
    print(f"Unpacked output values: {actual}")
    print(f"Expected output values: {outputs_out}")
    assert torch.all(actual == outputs_out).item(), f"Expected {outputs_out}, got {actual}"
    cocotb.log.info(f"[PASS] Input: {inputs_a}, Shift: {shift_amount}, Output: {actual}")

@pytest.mark.dev
def test_simple_fp_addition():
    global EXP_WIDTH, MANT_WIDTH
    # Run tests with different params
    veri_runner(
        module = "fp_vec_shift",  
        additional_include_paths=[
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/buffer"),
            str(SRC_PATH / "basic_components/fp_operation"),
            str(SRC_PATH / "basic_components/int_operation")
        ],      
        module_param_list=[
            {"VLEN": EXP_WIDTH + MANT_WIDTH + 1, "VDEPTH": 4},
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_simple_fp_addition()

