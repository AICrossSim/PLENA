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

comp_dim = 2
block_dim = 2

fp_exp_width = 4
fp_mant_width = 3



generator = MXBlockFPConverter(mxfp_exp_width, mxfp_mant_width, mxfp_scale_width, block_dim)

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)

@cocotb.test()
async def random_mcu_test(dut):
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
        

        v_mx_fp_scales, v_mx_fp_elems = generator.generate_certain_values([1.24, 2.01, 1.0231, 0.9820])
        v_ele_data = 0
        v_scale_data = 0
        for i in range(comp_dim // block_dim):
            v_ele_data    += sum((v_mx_fp_elems[i][n] << (mxfp_exp_width + mxfp_mant_width + 1) * (n + i * block_dim) ) for n in range(block_dim))
            v_scale_data  += (v_mx_fp_scales[i] << (mxfp_scale_width) * i)

        dut.v1_element.value = v_ele_data
        dut.v1_scale.value = v_scale_data
        dut.v1_in_valid.value = 1
        dut.v_result_ready.value = 1

        dut.v2_element.value = v_ele_data
        dut.v2_scale.value = v_scale_data
        dut.v2_in_valid.value = 1
        dut.v_result_ready.value = 1



@pytest.mark.dev
def mcu_test():
    # Run tests with different params
    veri_runner(
        group = "systolic_gemm",
        module = "systolic_mcu",
        additional_include_paths = [
            "../../../../src/basic_components/mx_fp_operation",
            "../../../../src/basic_components/buffer",
            "../../../../src/basic_components/fp_operation",
            "../../../../src/basic_components/conversion",
            "../../../../src/basic_components/common"
        ],       
        module_param_list=[
            {"MXFP_MANT_WIDTH" : mxfp_mant_width, "MXFP_EXP_WIDTH" : mxfp_exp_width, "MXFP_SCALE_WIDTH" : mxfp_scale_width, 
             "BLOCK_DIM" : block_dim, "ACC_FP_MANT_WIDTH" : fp_mant_width, "ACC_FP_EXP_WIDTH" : fp_exp_width,
             "N" : comp_dim, "M" : comp_dim, "K" : comp_dim }
        ],
        trace = True,
    )

if __name__ == "__main__":
    mcu_test()
