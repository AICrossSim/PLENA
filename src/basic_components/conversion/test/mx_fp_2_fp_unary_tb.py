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

        dut.element_data_in.value = mx_elems[0]
        dut.scale_data_in.value = mx_scale
        # await RisingEdge(dut.clk)

        await Timer(1, units="ns")
        cocotb.log.info(f" Data a : {generator.convert_to_float([mx_elems[0]], mx_scale, element_exp_width, element_mant_width)} ELE Binary: {dut.element_data_in.value}, SCALE Binary: {dut.scale_data_in.value}")
        await Timer(1, units="ns")
        cocotb.log.info(f"Expected result : {test_data_1}, FP Binary: {dut.fp_out.value} Converted Float : {generator.fp_gen.full_precision_fp_float_convertion(fp_exp_width, fp_mant_width, dut.fp_out.value)}")



@pytest.mark.dev
def test_simple_fp_addition():
    # Run tests with different params
    veri_runner(
        group = "conversion",
        module = "mx_fp_2_fp_unary",
        additional_include_paths = [
            "/Users/georgewu/Documents/Cambridge/Coprocessor_for_Llama/src/basic_components/fp_operation",                                      
        ],
        module_param_list=[
            {"MXFP_EXP_WIDTH" : element_exp_width, "MXFP_MANT_WIDTH" : element_mant_width, "MXFP_SCALE_WIDTH" : scale_width, "FP_MANT_WIDTH" : fp_mant_width, "FP_EXP_WIDTH" : fp_exp_width},
        ],
        trace = False,
    )

if __name__ == "__main__":
    test_simple_fp_addition()
