#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os

from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock

from cfl_cocotb import veri_runner, MXBlockFPConverter

element_exp_width = 4
element_mant_width = 3
scale_width = 8

fp_exp_width = 4
fp_mant_width = 3

generator = MXBlockFPConverter(element_exp_width, element_mant_width, scale_width, block_size = 4)

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)

@cocotb.test()
async def simple_random_mxfp_test(dut):

    cocotb.start_soon(Clock(dut.clk, 2, units="ns").start()) 
    # Start clock generation
    TESTCASE_SIZE = 1
    await Timer(4, units="ns")
    cocotb.log.info("Starting fp addition test")
    await Timer(4, units="ns")
    dut.rst.value = 0
    await Timer(4, units="ns")  # Hold reset for 5ns
    dut.rst.value = 1
    await Timer(4, units="ns")  # Allow some settling time

    for i in range (TESTCASE_SIZE):
        # Generate random floating point values
        # fp_values, results = generator.generate_fp_input(2)
        test_data_1 = 2.023
        test_data_2 = 3.012
        mx_scale, mx_elems = generator.generate_certain_values([test_data_1, test_data_2, 1.0, 1.0])
        print(f"mx_scale: {mx_scale}, mx_elems: {mx_elems}")
        dut.in_top_element.value = mx_elems[0][0]
        dut.in_top_scale.value = mx_scale[0]
        dut.in_top_valid.value = 1
        dut.in_left.value = mx_elems[0][1]
        dut.in_left_scale.value = mx_scale[0]
        dut.in_left_valid.value = 1

        await Timer(200, units="ns")

        # await Timer(1, units="ns")
        # cocotb.log.info(f" Result a : {generator.convert_to_float([mx_elems[0]], mx_scale, element_exp_width, element_mant_width)} ELE Binary: {dut.element_data_a.value}, SCALE Binary: {dut.scale_data_a.value}")
        # cocotb.log.info(f" Result b : {generator.convert_to_float([mx_elems[1]], mx_scale, element_exp_width, element_mant_width)} ELE Binary: {dut.element_data_b.value}, SCALE Binary: {dut.scale_data_b.value}")
        # await Timer(1, units="ns")
        # cocotb.log.info(f"Internel Signal : shifted_element_data_a {dut.shifted_element_data_a.value}")
        # cocotb.log.info(f"Internel Signal : shifted_element_data_b {dut.shifted_element_data_b.value}")
        # cocotb.log.info(f"Expected result : {test_data_1 + test_data_2}, ELE Binary: {dut.element_data_out.value}, SCALE Binary: {dut.scale_data_out.value}, Converted Float : {generator.convert_to_float([dut.element_data_out.value], dut.scale_data_out.value, result_exp_width, result_mant_width)}")




@pytest.mark.dev
def test_simple_pe():
    # Run tests with different params
    veri_runner(
        group = "systolic_gemm",
        module = "default_pe",
        additional_include_paths = [
            "../../../../src/basic_components/fp_operation",    
            "../../../../src/basic_components/common",
            "../../../../src/basic_components/mx_fp_operation",
            "../../../../src/basic_components/conversion",
            "../../../../src/basic_components/buffer"                            
        ],
        module_param_list=[
            {"MXFP_EXP_WIDTH" : element_exp_width, "MXFP_MANT_WIDTH" : element_mant_width, "MXFP_SCALE_WIDTH" : scale_width, "ACC_FP_MANT_WIDTH" : fp_mant_width, "ACC_FP_EXP_WIDTH" : fp_exp_width},
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_simple_pe()
