#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os

from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock

from cfl_cocotb import veri_runner, MXBlockFPConverter, FpGenerator

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
async def simple_mxfp_2_fp_conversion(dut):
    # Start clock generation
    TESTCASE_SIZE = 1
    await Timer(5, units="ns")
    cocotb.log.info("Starting fp addition test")

    for i in range (TESTCASE_SIZE):
        # Generate random floating point values
        # fp_values, results = generator.generate_fp_input(2)
        mx_fp_scales, mx_fp_elems = generator.generate_certain_values([1.24, 2.01, 1.0231, 0.9820])
        print(f"mx_fp_scales: {mx_fp_scales}, mx_fp_elems: {mx_fp_elems}")

        ele_data = 0
        scale_data = 0
        ele_data    += sum((mx_fp_elems[0][n] << (mxfp_exp_width + mxfp_mant_width + 1) * (n + i * block_dim) ) for n in range(block_dim))
        scale_data  += (mx_fp_scales[0] << (mxfp_scale_width) * i)

        dut.element_in.value = ele_data
        dut.scale_in.value = scale_data

        await Timer(2, units="ns")
        cocotb.log.info(f"Input Data {generator.convert_block_to_fp(dut.element_in.value, dut.scale_in.value, mxfp_exp_width, mxfp_mant_width)}")
        cocotb.log.info(f"element_in {dut.element_in.value}")
        cocotb.log.info(f"scale_in {dut.scale_in.value}")
        
        cocotb.log.info(f"mxfp_exp {dut.mxfp_exp.value}")
        cocotb.log.info(f"temp_exp {dut.temp_exp.value}")
        cocotb.log.info(f"exp_overflow {dut.exp_overflow.value}")
        
        cocotb.log.info(f"mxfp_mant {dut.mxfp_mant.value}")
        cocotb.log.info(f"mant_out{dut.mant_out.value}")
      
        cocotb.log.info(f"FP_OUT Result{dut.fp_out.value}")
        cocotb.log.info(f"Converted Result {generator.fp_gen.multi_fp_conversion(  fp_exp_width, fp_mant_width, dut.fp_out.value)}")



@pytest.mark.dev
def test_simple_fp_addition():
    # Run tests with different params
    veri_runner(
        group = "conversion",
        module = "mx_fp_blockwise_adder",
        additional_include_paths = [
            "../../../../src/basic_components/fp_operation",                                      
        ],
        module_param_list=[
            {"BLOCK_DIM" : block_dim, "MXFP_EXP_WIDTH" : mxfp_exp_width, "MXFP_MANT_WIDTH" : mxfp_mant_width, "MXFP_SCALE_WIDTH" : mxfp_scale_width, "FP_MANT_WIDTH" : fp_mant_width, "FP_EXP_WIDTH" : fp_exp_width},
        ],
        trace = False,
    )

if __name__ == "__main__":
    test_simple_fp_addition()
