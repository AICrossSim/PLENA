#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import sys
from pathlib import Path
# FIXED: Use 4 levels up, not 5
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "tools"))

import logging
import pytest
import cocotb
import os
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
from math import ceil, log2
import math
import torch
import numpy as np
from cfl_cocotb import veri_runner
from cfl_cocotb.runner import SRC_PATH
from cfl_cocotb.testbench import Testbench
from cfl_cocotb.fp_generation import FpGenerator

exp_width = 4
mant_width = 3
vect_dim = 4
print("hello this is the:", str(SRC_PATH))
level = math.ceil(math.log2(vect_dim))


generator = FpGenerator(exp_width, mant_width)

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)

#@cocotb.test()
async def random_fp_add_test(dut):
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
        fp_values, results = generator.generate_specified_value_fp_input([40.517, 218.18, 129.98, 210.00, 30.231, 41.77, 75.2, 19.29])
        # fp_values, results = generator.generate_specified_value_fp_input([40.517, 40.517, 40.517, 40.517, 30.231, 30.231, 30.231, 30.231])
        input_data_a = sum((results[n] << (exp_width + mant_width + 1) * n ) for n in range(vect_dim))
        input_data_b = sum((results[n + vect_dim] << (exp_width + mant_width + 1) * n ) for n in range(vect_dim))
        dut.v_in_a.value = input_data_a
        dut.v_in_b.value = input_data_b

        # await RisingEdge(dut.clk)
        await Timer(2, units="ns")
        # cocotb.log.info("<-------  INPUT DATA  --------->")
        # for m in range(2*vect_dim):
        #     cocotb.log.info(f"Value at index {m} : {fp_values[m]}, Result : {generator.custom_fp_to_float(results[m])}, Binary: {bin(results[m])}")
        
        # cocotb.log.info(f"Input Binary data_a {dut.v_in_a.value}")
        # cocotb.log.info(f"Input Binary data_b {dut.v_in_b.value}")
        # generator.translate_packed_array_fp(vect_dim, exp_width, mant_width, dut.data_a_in.value)

        dut.v_in_a_valid.value = 1
        dut.v_in_b_valid.value = 1
        dut.v_out_ready.value = 1
        dut.operation = 0

        await Timer(4, units="ns")
        addition_result = []
        for i in range(0, vect_dim):
            # Get the expected result
            addition_result.append(fp_values[i] + fp_values[i + vect_dim])
        cocotb.log.info("<-------  Addition Result DATA  --------->")
        cocotb.log.info(f"Internal Product Binary Results : {dut.v_out.value}")
        cocotb.log.info(f"Internal Converted Results : {generator.translate_packed_array_fp(vect_dim, exp_width, mant_width, dut.v_out.value)}")
        cocotb.log.info(f"Internal Product Ref : {addition_result}")


##+@cocotb.test()
async def random_fp_subtract_test(dut):
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
        fp_values, results = generator.generate_specified_value_fp_input([40.517, 218.18, 129.98, 210.00, 30.231, 41.77, 75.2, 19.29])
        input_data_a = sum((results[n] << (exp_width + mant_width + 1) * n ) for n in range(vect_dim))
        input_data_b = sum((results[n + vect_dim] << (exp_width + mant_width + 1) * n ) for n in range(vect_dim))
        dut.v_in_a.value = input_data_a
        dut.v_in_b.value = input_data_b

        # await RisingEdge(dut.clk)
        await Timer(2, units="ns")
        # cocotb.log.info("<-------  INPUT DATA  --------->")
        # for m in range(2*vect_dim):
        #     cocotb.log.info(f"Value at index {m} : {fp_values[m]}, Result : {generator.custom_fp_to_float(results[m])}, Binary: {bin(results[m])}")
        
        # cocotb.log.info(f"Input Binary data_a {dut.v_in_a.value}")
        # cocotb.log.info(f"Input Binary data_b {dut.v_in_b.value}")
        # generator.translate_packed_array_fp(vect_dim, exp_width, mant_width, dut.data_a_in.value)

        dut.v_in_a_valid.value = 1
        dut.v_in_b_valid.value = 1
        dut.v_out_ready.value = 1
        dut.operation = 1

        await Timer(4, units="ns")
        addition_result = []
        for i in range(0, vect_dim):
            # Get the expected result
            addition_result.append(fp_values[i] - fp_values[i + vect_dim])
        cocotb.log.info("<-------  Subtraction Vector DATA  --------->")
        cocotb.log.info(f"Internal Product Binary Results : {dut.v_out.value}")
        cocotb.log.info(f"Internal Converted Results : {generator.translate_packed_array_fp(vect_dim, exp_width, mant_width, dut.v_out.value)}")
        cocotb.log.info(f"Internal Product Ref : {addition_result}")

#@cocotb.test()
async def random_fp_multiply_test(dut):
    # Start clock generation
    TESTCASE_SIZE = 1
    
    cocotb.start_soon(Clock(dut.clk, 2, units="ns").start())  # 2ns period (1GHz clock)
    
    await Timer(5, units="ns")
    cocotb.log.info("Starting fp multiply test")
    # Apply Reset
    dut.rst.value = 0
    await Timer(5, units="ns")  # Hold reset for 5ns
    dut.rst.value = 1
    await Timer(5, units="ns")  # Allow some settling time

    for i in range (TESTCASE_SIZE):
        # Generate random floating point values

        # fp_values, results = generator.generate_fp_input(vect_dim)
        fp_values, results = generator.generate_specified_value_fp_input([4.517, 2.18, 9.98, 2.00, 3.231, 4.77, 7.2, 19.29])
        input_data_a = sum((results[n] << (exp_width + mant_width + 1) * n ) for n in range(vect_dim))
        input_data_b = sum((results[n + vect_dim] << (exp_width + mant_width + 1) * n ) for n in range(vect_dim))
        dut.v_in_a.value = input_data_a
        dut.v_in_b.value = input_data_b

        # await RisingEdge(dut.clk)
        await Timer(2, units="ns")
        dut.v_in_a_valid.value = 1
        dut.v_in_b_valid.value = 1
        dut.v_out_ready.value = 1
        dut.operation = 2

        await Timer(4, units="ns")
        addition_result = []
        for i in range(0, vect_dim):
            # Get the expected result
            addition_result.append(fp_values[i] * fp_values[i + vect_dim])
        cocotb.log.info("<-------  Subtraction Vector DATA  --------->")
        cocotb.log.info(f"Internal Product Binary Results : {dut.v_out.value}")
        cocotb.log.info(f"Internal Converted Results : {generator.translate_packed_array_fp(vect_dim, exp_width, mant_width, dut.v_out.value)}")
        cocotb.log.info(f"Internal Product Ref : {addition_result}")


@cocotb.test()
async def prefix_scan_test(dut):
    """Test prefix scan operation with proper timing"""
    
    # Start clock first
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())  # Slower clock
    
    await Timer(5, units="ns")
    cocotb.log.info("Starting prefix scan test")
    
    # Proper reset sequence
    dut.rst.value = 0
    dut.v_in_a_valid.value = 0
    dut.v_in_b_valid.value = 0
    dut.v_out_ready.value = 0
    dut.operation.value = 0
    
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    # Test data: [1.0, 2.0, 3.0, 4.0]
    # Expected prefix scan: [1.0, 3.0, 6.0, 10.0]
    test_values = [1.0, 2.0, 3.0, 4.0]
    fp_values, results = generator.generate_specified_value_fp_input(test_values)
    input_data_a = sum((results[n] << (exp_width + mant_width + 1) * n) for n in range(vect_dim))
    
    cocotb.log.info(f"Input values: {test_values}")
    cocotb.log.info(f"Input data packed: {hex(input_data_a)}")
    
    # Set inputs
    dut.v_in_a.value = input_data_a
    dut.v_in_b.value = 0  # Not used for prefix scan
    dut.operation.value = 8  # PREFIX_SCAN_V_ELEMENT
    dut.v_out_ready.value = 1
    dut.v_in_a_valid.value = 1
    await RisingEdge(dut.clk)
    
    # Assert valid
    dut.v_in_a_valid.value = 0
    dut.v_in_b_valid.value = 0
    
    cocotb.log.info("Inputs set, waiting for computation...")
    
    # Wait for prefix scan to complete - check for valid output
    timeout = 0
    max_timeout = 50
    
    while timeout < max_timeout:
        await RisingEdge(dut.clk)
        timeout += 1
        
        # Log intermediate signals for debugging
        if timeout % 10 == 0:
            cocotb.log.info(f"Cycle {timeout}: v_out={hex(dut.v_out.value)}, v_out_valid={dut.v_out_valid.value}")
        
        # Check if we have valid output
        if dut.v_out_valid.value == 1:
            cocotb.log.info(f"Valid output detected at cycle {timeout}")
            break
            
        # Also check if output is non-zero (for combinational logic)
        if dut.v_out.value != 0:
            cocotb.log.info(f"Non-zero output detected at cycle {timeout}")
            # Wait a few more cycles to be sure
            for _ in range(5):
                await RisingEdge(dut.clk)
            break
   # breakpoint()
    if timeout >= max_timeout:
        cocotb.log.error("Timeout waiting for prefix scan result")
    
    # Deassert valid
    
    
    # Get and verify results
    actual_result = generator.translate_packed_array_fp(vect_dim, exp_width, mant_width, dut.v_out.value)
    
    # Calculate expected prefix scan
    expected_result = []
    cumsum = 0.0
    for val in test_values:
        cumsum += val
        expected_result.append(cumsum)
    
    cocotb.log.info("<-------  Prefix Scan Results  --------->")
    cocotb.log.info(f"Input: {test_values}")
    cocotb.log.info(f"Expected: {expected_result}")
    cocotb.log.info(f"Hardware Binary: {hex(dut.v_out.value)}")
    cocotb.log.info(f"Hardware Result: {actual_result}")
    #breakpoint()
    # Debug internal signals
    try:
        cocotb.log.info(f"use_prefix_scan: {dut.use_prefix_scan.value}")
        cocotb.log.info(f"prefix_scan_valid: {dut.prefix_scan_valid.value}")
        cocotb.log.info(f"prefix_scan_ready: {dut.prefix_scan_ready.value}")
    except AttributeError:
        cocotb.log.warning("Some internal signals not accessible")
    
    # Verify results with reasonable tolerance
    tolerance = 0.5  # Adjust based on your FP precision
    all_passed = True
    
    for j in range(vect_dim):
        error = abs(actual_result[j] - expected_result[j]) if expected_result[j] != 0 else abs(actual_result[j])
        if error > tolerance:
            cocotb.log.error(f"✗ Mismatch at index {j}: expected {expected_result[j]}, got {actual_result[j]}, error {error}")
            all_passed = False
        else:
            cocotb.log.info(f"✓ Index {j}: {actual_result[j]} ≈ {expected_result[j]}")
    
    # Add assertion to actually fail the test if results are wrong
    assert all_passed, f"Prefix scan test failed - see errors above"
    
    cocotb.log.info("✓ Prefix scan test PASSED!")

@pytest.mark.dev
def simple_test():
    # Run tests with different params
    veri_runner(
        group = "vector_machine",
        module = "fp_elementwise_compute_unit",
        additional_include_paths=[
            str(SRC_PATH / "basic_components/buffer"),
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/fp_operation"),
            str(SRC_PATH / "basic_components/hadamard_transform"),
            str(SRC_PATH / "basic_components/synopsis_ip_inst"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/int_operation"),
            str(SRC_PATH / "basic_components/synopsis")
        ],
        definitions_path=[str(SRC_PATH / "definitions")],
        module_param_list=[
            {"EXP_WIDTH" : exp_width, "MANT_WIDTH" : mant_width, "VLEN" : vect_dim  },
        ],
        trace = True,
    )

if __name__ == "__main__":
    simple_test()
