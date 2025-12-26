#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os
from pathlib import Path
# Add tools directory to path for cfl_cocotb import
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "tools"))

from cocotb.triggers import Timer, RisingEdge, FallingEdge
from cocotb.clock import Clock
from cfl_cocotb import veri_runner, FpGenerator
from math import ceil, log2
import math

exp_width = 4
mant_width = 3
layer_dim = 4  # Number of input elements (must be power of 2)
input_data_width = mant_width + exp_width + 1  # sign + exp + mant
overall_input_width = layer_dim * input_data_width

generator = FpGenerator(exp_width, mant_width)

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)

@cocotb.test()
async def test_fp_sum_reduction(dut):
    """Test SUM operation on fp_vector_reduce_layer"""
    # Start clock generation
    cocotb.start_soon(Clock(dut.clk, 2, units="ns").start())  # 2ns period (1GHz clock)
    
    await Timer(5, units="ns")
    cocotb.log.info("Starting fp SUM reduction test")
    
    # Apply Reset
    dut.rst.value = 0
    await Timer(5, units="ns")  # Hold reset for 5ns
    dut.rst.value = 1
    await Timer(5, units="ns")  # Allow some settling time
    
    # Generate test values
    test_values = [4.517, 1.18, 2.98, 10.00]
    fp_values, results = generator.generate_specified_value_fp_input(test_values)
    
    # Pack the input data
    input_data = 0
    for n in range(layer_dim):
        input_data |= (results[n] << (input_data_width * n))
    
    dut.data_in.value = input_data
    dut.operation.value = 0  # SUM_V_REDUCT
    dut.data_in_valid.value = 1
    dut.data_out_ready.value = 1
    
    # Wait for input to be accepted
    await RisingEdge(dut.clk)
    while not dut.data_in_ready.value:
        await RisingEdge(dut.clk)
    
    # Wait for valid output (pipeline delay through skid buffers)
    cycles_waited = 0
    max_cycles = 20
    while not dut.data_out_valid.value and cycles_waited < max_cycles:
        await RisingEdge(dut.clk)
        cycles_waited += 1
    
    if cycles_waited >= max_cycles:
        cocotb.log.error("Timeout waiting for data_out_valid")
        assert False, "Timeout waiting for output"
    
    # Calculate expected results
    # For SUM, each pair should be added
    # Pair 0: 4.517 + 1.18 = 5.697
    # Pair 1: 2.98 + 10.00 = 12.98
    expected_sum_0 = test_values[0] + test_values[1]
    expected_sum_1 = test_values[2] + test_values[3]
    
    # Extract output data
    output_data = dut.data_out.value.integer
    out_dim = (layer_dim + 1) // 2
    output_data_width = input_data_width  # No extension bits in this test
    
    # Extract each output element
    output_elements = []
    for i in range(out_dim):
        element = (output_data >> (output_data_width * i)) & ((1 << output_data_width) - 1)
        output_elements.append(element)
        float_val = generator.custom_fp_to_float(element)
        cocotb.log.info(f"Output element {i}: binary={bin(element)}, float={float_val}")
    
    # Check index output (for SUM, should be 0, which is the first index of the first pair)
    index_out = dut.index_out.value.integer
    cocotb.log.info(f"Index output: {index_out}")
    assert index_out == 0, f"Expected index 0 for SUM, got {index_out}"
    
    cocotb.log.info("<-------  SUM Reduction Result DATA  --------->")
    cocotb.log.info(f"Output Binary: {bin(output_data)}")
    cocotb.log.info(f"Expected sum pair 0: {expected_sum_0}")
    cocotb.log.info(f"Expected sum pair 1: {expected_sum_1}")


@cocotb.test()
async def test_fp_max_reduction(dut):
    """Test MAX operation on fp_vector_reduce_layer"""
    # Start clock generation
    cocotb.start_soon(Clock(dut.clk, 2, units="ns").start())  # 2ns period (1GHz clock)
    
    await Timer(5, units="ns")
    cocotb.log.info("Starting fp MAX reduction test")
    
    # Apply Reset
    dut.rst.value = 0
    await Timer(5, units="ns")  # Hold reset for 5ns
    dut.rst.value = 1
    await Timer(5, units="ns")  # Allow some settling time
    
    # Generate test values where we know which is max
    # Pair 0: 1.18 < 4.517, so max is at index 1
    # Pair 1: 2.98 < 10.00, so max is at index 3
    test_values = [1.18, 4.517, 2.98, 10.00]
    fp_values, results = generator.generate_specified_value_fp_input(test_values)
    
    # Pack the input data
    input_data = 0
    for n in range(layer_dim):
        input_data |= (results[n] << (input_data_width * n))
    
    dut.data_in.value = input_data
    dut.operation.value = 1  # MAX_V_REDUCT
    dut.data_in_valid.value = 1
    dut.data_out_ready.value = 1
    
    # Wait for input to be accepted
    await RisingEdge(dut.clk)
    while not dut.data_in_ready.value:
        await RisingEdge(dut.clk)
    
    # Wait for valid output (pipeline delay through skid buffers)
    cycles_waited = 0
    max_cycles = 20
    while not dut.data_out_valid.value and cycles_waited < max_cycles:
        await RisingEdge(dut.clk)
        cycles_waited += 1
    
    if cycles_waited >= max_cycles:
        cocotb.log.error("Timeout waiting for data_out_valid")
        assert False, "Timeout waiting for output"
    
    # Calculate expected max values
    # Pair 0: max(1.18, 4.517) = 4.517 (index 1)
    # Pair 1: max(2.98, 10.00) = 10.00 (index 3)
    expected_max_0 = max(test_values[0], test_values[1])
    expected_max_1 = max(test_values[2], test_values[3])
    expected_max_index_0 = 1 if test_values[1] > test_values[0] else 0
    expected_max_index_1 = 3 if test_values[3] > test_values[2] else 2
    
    # Extract output data
    output_data = dut.data_out.value.integer
    out_dim = (layer_dim + 1) // 2
    output_data_width = input_data_width  # No extension bits in this test
    
    # Extract each output element
    output_elements = []
    for i in range(out_dim):
        element = (output_data >> (output_data_width * i)) & ((1 << output_data_width) - 1)
        output_elements.append(element)
        float_val = generator.custom_fp_to_float(element)
        cocotb.log.info(f"Output element {i}: binary={bin(element)}, float={float_val}")
    
    # Check index output (should be the index of the first pair's max, which is index 1)
    index_out = dut.index_out.value.integer
    cocotb.log.info(f"Index output: {index_out}")
    cocotb.log.info(f"Expected index for first pair: {expected_max_index_0}")
    assert index_out == expected_max_index_0, f"Expected index {expected_max_index_0} for MAX, got {index_out}"
    
    cocotb.log.info("<-------  MAX Reduction Result DATA  --------->")
    cocotb.log.info(f"Output Binary: {bin(output_data)}")
    cocotb.log.info(f"Expected max pair 0: {expected_max_0} (index {expected_max_index_0})")
    cocotb.log.info(f"Expected max pair 1: {expected_max_1} (index {expected_max_index_1})")


@cocotb.test()
async def test_fp_max_reduction_reverse(dut):
    """Test MAX operation with reversed order (first element is max)"""
    # Start clock generation
    cocotb.start_soon(Clock(dut.clk, 2, units="ns").start())  # 2ns period (1GHz clock)
    
    await Timer(5, units="ns")
    cocotb.log.info("Starting fp MAX reduction test (first element is max)")
    
    # Apply Reset
    dut.rst.value = 0
    await Timer(5, units="ns")  # Hold reset for 5ns
    dut.rst.value = 1
    await Timer(5, units="ns")  # Allow some settling time
    
    # Generate test values where first element in each pair is max
    # Pair 0: 4.517 > 1.18, so max is at index 0
    # Pair 1: 10.00 > 2.98, so max is at index 2
    test_values = [4.517, 1.18, 10.00, 2.98]
    fp_values, results = generator.generate_specified_value_fp_input(test_values)
    
    # Pack the input data
    input_data = 0
    for n in range(layer_dim):
        input_data |= (results[n] << (input_data_width * n))
    
    dut.data_in.value = input_data
    dut.operation.value = 1  # MAX_V_REDUCT
    dut.data_in_valid.value = 1
    dut.data_out_ready.value = 1
    
    # Wait for input to be accepted
    await RisingEdge(dut.clk)
    while not dut.data_in_ready.value:
        await RisingEdge(dut.clk)
    
    # Wait for valid output (pipeline delay through skid buffers)
    cycles_waited = 0
    max_cycles = 20
    while not dut.data_out_valid.value and cycles_waited < max_cycles:
        await RisingEdge(dut.clk)
        cycles_waited += 1
    
    if cycles_waited >= max_cycles:
        cocotb.log.error("Timeout waiting for data_out_valid")
        assert False, "Timeout waiting for output"
    
    # Calculate expected max values
    # Pair 0: max(4.517, 1.18) = 4.517 (index 0)
    # Pair 1: max(10.00, 2.98) = 10.00 (index 2)
    expected_max_index_0 = 0 if test_values[0] > test_values[1] else 1
    
    # Check index output (should be the index of the first pair's max, which is index 0)
    index_out = dut.index_out.value.integer
    cocotb.log.info(f"Index output: {index_out}")
    cocotb.log.info(f"Expected index for first pair: {expected_max_index_0}")
    assert index_out == expected_max_index_0, f"Expected index {expected_max_index_0} for MAX, got {index_out}"
    
    cocotb.log.info("<-------  MAX Reduction Result DATA (Reverse)  --------->")
    cocotb.log.info(f"Index output: {index_out}")


@pytest.mark.dev
def test_fp_vector_reduce_layer():
    """Run tests for fp_vector_reduce_layer"""
    veri_runner(
        group = "vector_machine",
        module = "fp_vector_reduce_layer",
        additional_include_paths = [
            "../../basic_components/buffer",
            "../../basic_components/common",
            "../../basic_components/fp_operation",
            "../../basic_components/int_operation"
        ],
        definitions_path = "../../definitions",
        module_param_list=[
            {
                "OVERALL_INPUT_WIDTH": overall_input_width,
                "LAYER_DIM": layer_dim,
                "IN_MAN_WIDTH": mant_width,
                "IN_EXP_WIDTH": exp_width,
                "EXT_MANT_WIDTH": 0,
                "EXT_EXP_WIDTH": 0
            },
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_fp_vector_reduce_layer()

