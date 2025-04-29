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
import math

exp_width = 4
mant_width = 3
vect_dim = 4

level = math.ceil(math.log2(vect_dim))


generator = FpGenerator(exp_width, mant_width)

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)

@cocotb.test()
async def random_fp_sum_test(dut):
    # Start clock generation
    TESTCASE_SIZE = 1
    
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

        # fp_values, results = generator.generate_fp_input(vect_dim)
        fp_values, results = generator.generate_specified_value_fp_input([4.517, 1.18, 2.98, 10.00])
        # fp_values, results = generator.generate_specified_value_fp_input([40.517, 40.517, 40.517, 40.517, 30.231, 30.231, 30.231, 30.231])
        input_data_a = sum((results[n] << (exp_width + mant_width + 1) * n ) for n in range(vect_dim))
        dut.v_in.value = input_data_a

        # await RisingEdge(dut.clk)
        await Timer(2, units="ns")
        # cocotb.log.info("<-------  INPUT DATA  --------->")
        # for m in range(2*vect_dim):
        #     cocotb.log.info(f"Value at index {m} : {fp_values[m]}, Result : {generator.custom_fp_to_float(results[m])}, Binary: {bin(results[m])}")
        
        # cocotb.log.info(f"Input Binary data_a {dut.v_in_a.value}")
        # cocotb.log.info(f"Input Binary data_b {dut.v_in_b.value}")
        # generator.translate_packed_array_fp(vect_dim, exp_width, mant_width, dut.data_a_in.value)

        dut.v_in_valid.value = 1
        dut.v_out_ready.value = 1
        dut.operation = 0

        await Timer(4, units="ns")
        addition_result = 0
        for i in range(0, vect_dim):
            # Get the expected result
            addition_result += fp_values[i]
        cocotb.log.info("<-------  Addition Result DATA  --------->")
        cocotb.log.info(f"Internal Product Binary Results : {dut.v_out.value}")
        cocotb.log.info(f"Internal Converted Results : {generator.translate_packed_array_fp(vect_dim, exp_width, mant_width, dut.v_out.value)}")
        cocotb.log.info(f"Internal Product Ref : {addition_result}")


@cocotb.test()
async def random_fp_sum_test(dut):
    # Start clock generation
    TESTCASE_SIZE = 1
    
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

        # fp_values, results = generator.generate_fp_input(vect_dim)
        fp_values, results = generator.generate_specified_value_fp_input([4.517, 1.18, 2.98, 10.00])
        # fp_values, results = generator.generate_specified_value_fp_input([40.517, 40.517, 40.517, 40.517, 30.231, 30.231, 30.231, 30.231])
        input_data_a = sum((results[n] << (exp_width + mant_width + 1) * n ) for n in range(vect_dim))
        dut.v_in.value = input_data_a

        # await RisingEdge(dut.clk)
        await Timer(2, units="ns")
        # cocotb.log.info("<-------  INPUT DATA  --------->")
        # for m in range(2*vect_dim):
        #     cocotb.log.info(f"Value at index {m} : {fp_values[m]}, Result : {generator.custom_fp_to_float(results[m])}, Binary: {bin(results[m])}")
        
        # cocotb.log.info(f"Input Binary data_a {dut.v_in_a.value}")
        # cocotb.log.info(f"Input Binary data_b {dut.v_in_b.value}")
        # generator.translate_packed_array_fp(vect_dim, exp_width, mant_width, dut.data_a_in.value)

        dut.v_in_valid.value = 1
        dut.v_out_ready.value = 1
        dut.operation = 1

        await Timer(4, units="ns")
        addition_result = 0
        for i in range(0, vect_dim):
            # Get the expected result
            addition_result = max(addition_result, fp_values[i])
        cocotb.log.info("<-------  Addition Result DATA  --------->")
        cocotb.log.info(f"Internal Product Binary Results : {dut.v_out.value}")
        cocotb.log.info(f"Internal Converted Results : {generator.translate_packed_array_fp(vect_dim, exp_width, mant_width, dut.v_out.value)}")
        cocotb.log.info(f"Internal Product Ref : {addition_result}")


@pytest.mark.dev
def test_simple_fp_addition():
    # Run tests with different params
    veri_runner(
        group = "vector_machine",
        module = "fp_reduction_compute_unit",
        additional_include_paths = [
            "../../../../src/basic_components/buffer",
            "../../../../src/basic_components/common",
            "../../../../src/basic_components/fp_operation"                                    
        ],
        definitions_path = "../../../../src/definitions",
        module_param_list=[
            {"EXP_WIDTH" : exp_width, "MANT_WIDTH" : mant_width, "VLEN" : vect_dim // 2  },
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_simple_fp_addition()
