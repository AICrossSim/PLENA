#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os
from pathlib import Path
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
from cfl_cocotb import veri_runner, FpGenerator
from math import ceil, log2

exp_width = 4
mant_width = 3
vect_dim = 4

output_man_width = mant_width + (1<<exp_width) * int(log2(vect_dim))
generator = FpGenerator(exp_width, mant_width)

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)

@cocotb.test()
async def random_fp_test(dut):
    # Start clock generation
    TESTCASE_SIZE = 10
    
    cocotb.start_soon(Clock(dut.clk, 2, units="ns").start())  # 2ns period (1GHz clock)
    
    await Timer(5, units="ns")
    cocotb.log.info("Starting fp addition test")
    # Apply Reset
    dut.rst.value = 0
    await Timer(5, units="ns")  # Hold reset for 5ns
    dut.rst.value = 1
    await Timer(5, units="ns")  # Allow some settling time

    for i in range (TESTCASE_SIZE):
        # Generate random floating point values
        fp_values, results = generator.generate_fp_input(vect_dim)
        input_data = sum((results[n] << int(log2(exp_width + mant_width + 1))) for n in range(vect_dim))
        dut.data_in.value = input_data
        # await RisingEdge(dut.clk)
        await Timer(2, units="ns")

        cocotb.log.info("<-------  INPUT DATA  --------->")
        cocotb.log.info(f"Input Binary {dut.data_in.value}")
        for m in range(vect_dim):
            cocotb.log.info(f"Value at index {m} : {fp_values[m]}, Result a : {generator.custom_fp_to_float(results[m])}")
        
        await Timer(8, units="ns")
        fp_results = sum(fp_values[g] for g in range(vect_dim))
        cocotb.log.info(f"Expected result : {fp_results}, DUT BIN_out: {dut.data_out.value}, Converted Float : {generator.full_precision_fp_float_convertion(exp_width, output_man_width, dut.data_out.value)}")


@pytest.mark.dev
def test_simple_fp_addition():
    # Run tests with different params
    veri_runner(
        group = "fp_operation",
        module = "fp_adder_tree",
        additional_include_paths = "/Users/georgewu/Documents/Cambridge/Coprocessor_for_Llama/src/basic_components/buffer",
        module_param_list=[
            {"VEC_DIM" : vect_dim, "IN_EXP_WIDTH" : exp_width, "IN_MAN_WIDTH" : mant_width},
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_simple_fp_addition()
