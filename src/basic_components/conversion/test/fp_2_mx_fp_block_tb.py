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
    
    await Timer(4, units="ns")
    cocotb.log.info("Starting fp addition test")
    # Apply Reset
    dut.rst.value = 0
    await Timer(2, units="ns")  # Hold reset for 5ns
    dut.rst.value = 1
    await Timer(4, units="ns")  # Allow some settling time
    dut.rst.value = 0
    await Timer(2, units="ns")  # Hold reset for 5ns

    for i in range (TESTCASE_SIZE):
        # Generate random floating point values
        
        # mx_fp_scales, mx_fp_elems = generator.generate_certain_values([1.24, 2.01, 1.0231, 0.9820])
        fp_values, results = generator.fp_gen.generate_specified_value_fp_input([1.24, 2.01, 1.0231, 0.9820])
        input_data = sum((results[n] << (fp_exp_width + fp_mant_width + 1) * n ) for n in range(block_dim))
        dut.data_in.value = input_data
        dut.data_in_valid.value = 1
        dut.mx_fp_data_out_ready.value = 1
        await Timer(2, units="ns")

        cocotb.log.info("<-------  INPUT DATA  --------->")
        cocotb.log.info(f" Testing Data : Values: {fp_values}, ")
        cocotb.log.info(f" Input Data : Binary: {dut.data_in.value}, ")
        
        await Timer(8, units="ns")

        cocotb.log.info("<-------  INTERNAL DATA --------->")
        cocotb.log.info(f"exp_max Data : Binary: {dut.exp_max.value} FP_OFFSET {bin(dut.FP_OFFSET.value)} ")
        cocotb.log.info(f"p2_sh_exp Data : Binary: {dut.p2_sh_exp.value} ")
        cocotb.log.info(f"p2_m_shifts Data : Binary: {dut.p2_m_shifts.value} ")

        cocotb.log.info("<-------  OUTPUT DATA --------->")
        cocotb.log.info(f"Output Scale {dut.scale_data_out.value}, Element Data {dut.element_data_out.value}")
        cocotb.log.info(f"Converted Result {generator.convert_block_to_fp(dut.element_data_out.value, dut.scale_data_out.value, mxfp_exp_width, mxfp_mant_width)}")

@pytest.mark.dev
def test_simple_fp_2_mxfp_conversion():
    # Run tests with different params
    veri_runner(
        group = "conversion",
        module = "fp_2_mx_fp_block",
        additional_include_paths = [
            "../../../../src/basic_components/buffer",
            "../../../../src/basic_components/fp_operation",
            "../../../../src/basic_components/common"
        ],       
        module_param_list=[
            {"BLOCK_DIM" : block_dim, "FP_MANT_WIDTH" : fp_mant_width, "FP_EXP_WIDTH" : fp_exp_width, "MXFP_EXP_WIDTH" : mxfp_exp_width, "MXFP_MANT_WIDTH" : mxfp_mant_width, "MXFP_SCALE_WIDTH" : mxfp_scale_width},
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_simple_fp_2_mxfp_conversion()
