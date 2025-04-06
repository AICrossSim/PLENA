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
block_size = 4
ext_mant_width = 0
ext_exp_width = 1

result_exp_width = element_exp_width + ext_exp_width
result_mant_width = element_mant_width + ext_mant_width

generator = MXBlockFPConverter(element_exp_width, element_mant_width, scale_width, block_size)

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)

@cocotb.test()
async def simple_random_mxfp_test(dut):
    # Start clock generation
    TESTCASE_SIZE = 1
    await Timer(5, units="ns")
    cocotb.log.info("Starting fp addition test")

    for i in range (TESTCASE_SIZE):
        # Generate random floating point values
        # fp_values, results = generator.generate_fp_input(2)
        test_data_1 = 2.023
        test_data_2 = 3.012
        mx_scale, mx_elems = generator.generate_certain_values([test_data_1, test_data_2])

        dut.element_data_a.value = mx_elems[0]
        dut.scale_data_a.value = mx_scale
        dut.element_data_b.value = mx_elems[1]
        dut.scale_data_b.value = mx_scale
        # await RisingEdge(dut.clk)

        await Timer(1, units="ns")
        cocotb.log.info(f" Result a : {generator.convert_to_float([mx_elems[0]], mx_scale, element_exp_width, element_mant_width)} ELE Binary: {dut.element_data_a.value}, SCALE Binary: {dut.scale_data_a.value}")
        cocotb.log.info(f" Result b : {generator.convert_to_float([mx_elems[1]], mx_scale, element_exp_width, element_mant_width)} ELE Binary: {dut.element_data_b.value}, SCALE Binary: {dut.scale_data_b.value}")
        await Timer(1, units="ns")
        cocotb.log.info(f"Internel Signal : shifted_element_data_a {dut.shifted_element_data_a.value}")
        cocotb.log.info(f"Internel Signal : shifted_element_data_b {dut.shifted_element_data_b.value}")
        cocotb.log.info(f"Expected result : {test_data_1 + test_data_2}, ELE Binary: {dut.element_data_out.value}, SCALE Binary: {dut.scale_data_out.value}, Converted Float : {generator.convert_to_float([dut.element_data_out.value], dut.scale_data_out.value, result_exp_width, result_mant_width)}")



@pytest.mark.dev
def test_simple_fp_addition():
    # Run tests with different params
    veri_runner(
        group = "mx_fp_operation",
        module = "mx_fp_unit_adder",
        additional_include_paths = [
            "/Users/georgewu/Documents/Cambridge/Coprocessor_for_Llama/src/basic_components/fp_operation",                                      
        ],
        module_param_list=[
            {"MXFP_EXP_WIDTH" : element_exp_width, "MXFP_MANT_WIDTH" : element_mant_width, "MXFP_SCALE_WIDTH" : scale_width, "EXT_MANT_WIDTH" : ext_mant_width, "EXT_EXP_WIDTH" : ext_exp_width},
        ],
        trace = False,
    )

if __name__ == "__main__":
    test_simple_fp_addition()
