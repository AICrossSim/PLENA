#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os

from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock

from cfl_cocotb import veri_runner, FpGenerator

exp_width = 6
mant_width = 5

output_exp_width = 4
output_man_width = 3


generator = FpGenerator(exp_width, mant_width)

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)

@cocotb.test()
async def random_fp_test(dut):
    # Start clock generation
    TESTCASE_SIZE = 1
    # cocotb.start_soon(Clock(dut.clk, 2, units="ns").start())  # 2ns period (1GHz clock)
    await Timer(5, units="ns")
    cocotb.log.info("Starting fp addition test")

    for i in range (TESTCASE_SIZE):
        # Generate random floating point values
        # fp_values, results = generator.generate_fp_input(2)
        fp_values, results = generator.generate_specified_value_fp_input([221.310])
        dut.data_in.value = results[0]
        # await RisingEdge(dut.clk)
        await Timer(1, units="ns")
        cocotb.log.info(f"Value a : {fp_values[0]}, Result a : {generator.custom_fp_to_float(results[0])} Binary: {dut.data_in.value}")
        
        await Timer(2, units="ns")
        cocotb.log.info(f"Expected result : {fp_values[0]}, Binary: {dut.data_out.value}, Converted Float : {generator.full_precision_fp_float_convertion(output_exp_width, output_man_width, dut.data_out.value)}")

@pytest.mark.dev
def test_simple_fp_round():
    # Run tests with different params
    veri_runner(
        group = "fp_operation",
        module = "fp_round",
        module_param_list=[
            {"IN_EXP_WIDTH" : exp_width, "IN_MANT_WIDTH" : mant_width, "OUT_EXP_WIDTH" : output_exp_width, "OUT_MANT_WIDTH" : output_man_width},
        ],
        trace = False,
    )

if __name__ == "__main__":
    test_simple_fp_round()
