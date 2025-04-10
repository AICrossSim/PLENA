#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os
from pathlib import Path
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
from cfl_cocotb import veri_runner, MXBlockFPConverter
from math import ceil, log2
import math


mxfp_exp_width = 4
mxfp_mant_width = 3
mxfp_scale_width = 8

block_dim = 4

fp_exp_width = 4
fp_mant_width = 3

generator = MXBlockFPConverter(mxfp_exp_width, mxfp_mant_width, mxfp_scale_width, block_dim)

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)

@cocotb.test()
async def random_fp_test(dut):
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
        
        # mx_fp_scales, mx_fp_elems = generator.generate_certain_values([1.24, 2.01, 1.0231, 0.9820])
        fp_values, results = generator.generate_specified_value_fp_input([1.24, 2.01, 1.0231, 0.9820])
        input_data = sum((results[n] << (fp_exp_width + fp_mant_width + 1) * n ) for n in range(block_dim))
        dut.data_in.value = input_data
        dut.data_in_valid.value = 1
        dut.data_out_ready.value = 1
        await Timer(2, units="ns")

        cocotb.log.info("<-------  INPUT DATA  --------->")
        cocotb.log.info(f" Input Data : Binary: {bin(dut.data_in.value)}, ")
        

        cocotb.log.info("<-------  OUTPUT DATA --------->")
        # cocotb.log.info(f"Output Binary {dut.data_out.value}")
        cocotb.log.info(f"Converted Result {generator.blockwise_convert_to_float(dut.element_data_out.value, dut.scale_data_out.value, block_dim, mxfp_exp_width, mxfp_mant_width)}")

@pytest.mark.dev
def test_simple_fp_2_mxfp_conversion():
    # Run tests with different params
    veri_runner(
        group = "conversion",
        module = "fp_2_mx_fp_vector",
        additional_include_paths = [
            "/Users/georgewu/Documents/Cambridge/Coprocessor_for_Llama/src/basic_components/buffer",
            "/Users/georgewu/Documents/Cambridge/Coprocessor_for_Llama/src/basic_components/fp_operation",
            "/Users/georgewu/Documents/Cambridge/Coprocessor_for_Llama/src/basic_components/common"
        ],       
        module_param_list=[
            {"CONVERT_DIM" : block_dim, "IN_MAN_WIDTH" : fp_mant_width, "IN_EXP_WIDTH" : fp_exp_width, "MX_FP_EXP_WIDTH" : mxfp_exp_width, "MX_FP_MANT_WIDTH" : mxfp_mant_width, "MX_FP_SCALE_WIDTH" : mxfp_scale_width},
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_simple_fp_2_mxfp_conversion()
