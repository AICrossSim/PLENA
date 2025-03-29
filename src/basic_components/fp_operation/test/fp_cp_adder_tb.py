#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os

from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock

from cfl_cocotb import veri_runner, FpGenerator

exp_width = 4
mant_width = 3
ext_mant_width = 0
ext_exp_width = 1

output_man_width = mant_width + ext_mant_width
output_exp_width = exp_width + ext_exp_width

generator = FpGenerator(exp_width, mant_width)

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)

@cocotb.test()
async def random_fp_test(dut):
    # Start clock generation
    TESTCASE_SIZE = 10
    # cocotb.start_soon(Clock(dut.clk, 2, units="ns").start())  # 2ns period (1GHz clock)
    await Timer(5, units="ns")
    cocotb.log.info("Starting fp addition test")

    for i in range (TESTCASE_SIZE):
        # Generate random floating point values
        fp_values, results = generator.generate_fp_input(2)
        dut.data_a.value = results[0]
        dut.data_b.value = results[1]
        # await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        cocotb.log.info(f"Value a : {fp_values[0]}, Result a : {generator.custom_fp_to_float(results[0])} Binary: {dut.data_a.value}")
        cocotb.log.info(f"Value b : {fp_values[1]}, Result b : {generator.custom_fp_to_float(results[1])} Binary: {dut.data_b.value}")
        await Timer(1, units="ns")
        cocotb.log.info(f"Expected result : {fp_values[0] + fp_values[1]}, Binary: {dut.data_out.value}, Converted Float : {generator.full_precision_fp_float_convertion(output_exp_width, output_man_width, dut.data_out.value)}")




@pytest.mark.dev
def test_simple_fp_addition():
    # Run tests with different params
    veri_runner(
        group = "fp_operation",
        module = "fp_cp_adder",
        module_param_list=[
            {"EXP_WIDTH" : exp_width, "MANT_WIDTH" : mant_width, "EXT_MANT_WIDTH" : ext_mant_width, "EXT_EXP_WIDTH" : ext_exp_width},
        ],
        trace = False,
    )

if __name__ == "__main__":
    test_simple_fp_addition()
