#!/usr/bin/env python3

import logging
import pytest
import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
from cfl_cocotb import veri_runner
from cfl_cocotb.runner import SRC_PATH
from random import randint

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)

# Element bit-width (sign + exp + mant)
EXP_WIDTH = 5
MANT_WIDTH = 10
ELEM_WIDTH = EXP_WIDTH + MANT_WIDTH + 1

@cocotb.test()
async def simple_shift_test(dut):
    # Try reading params; fallback to runner defaults
    try:
        lanes = int(dut.VLEN.value)
    except Exception:
        lanes = 8
    try:
        width = int(dut.VDEPTH.value)
    except Exception:
        width = ELEM_WIDTH

    # Clock (module has clk)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    mask = (1 << width) - 1
    inputs_a = [randint(0, mask) for _ in range(lanes)]
    shift_amount = min(2, lanes - 1)
    dut.shift.value = shift_amount

    # Pack lanes into a single bus
    v_packed = 0
    for i, value in enumerate(inputs_a):
        v_packed |= ((value & mask) << (i * width))

    # Drive input, wait a cycle, sample output
    dut.v_in.value = int(v_packed)
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")

    vout_packed = int(dut.v_out.value)

    # Unpack output
    actual = []
    for i in range(lanes):
        actual.append((vout_packed >> (i * width)) & mask)

    expected = ([0] * shift_amount) + inputs_a[:lanes - shift_amount]

    logger.info(f"VLEN={lanes}, WIDTH={width}, shift={shift_amount}")
    logger.info(f"in:  {inputs_a}")
    logger.info(f"out: {actual}")
    logger.info(f"exp: {expected}")

    assert actual == expected, f"Expected {expected}, got {actual}"

@pytest.mark.dev
def test_simple_fp_vec_shift():
    # Build and run the wrapper (packed buses)
    veri_runner(
        module="fp_vec_shift_wrap",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/fp_operation"),
        ],
        module_param_list=[
            {"VLEN": 8, "VDEPTH": ELEM_WIDTH},
        ],
        trace=True,
    )

if __name__ == "__main__":
    test_simple_fp_vec_shift()

