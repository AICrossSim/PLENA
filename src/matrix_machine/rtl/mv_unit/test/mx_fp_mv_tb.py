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

comp_dim = 4
block_dim = 2


product_ext_exp_width = 0
product_ext_mant_width = 0

block_ext_mant_width = 0
block_ext_exp_width = 1

fp_ext_mant_width = 0
fp_ext_exp_width = 1



block_level = math.ceil(math.log2(block_dim))
fp_level = math.ceil(math.log2(comp_dim // block_dim))


output_fp_exp_width = mxfp_exp_width + block_ext_exp_width * block_level + fp_ext_exp_width * fp_level
output_fp_mant_width = mxfp_mant_width + block_ext_mant_width * block_level + fp_ext_mant_width * fp_level

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
        
        mx_fp_scales, mx_fp_elems = generator.generate_certain_values([1.24, 2.01, 1.0231, 0.9820])
        print(f"mx_fp_scales: {mx_fp_scales}, mx_fp_elems: {mx_fp_elems}")

        ele_data = 0
        scale_data = 0
        for i in range(comp_dim // block_dim):
            ele_data    += sum((mx_fp_elems[i][n] << (mxfp_exp_width + mxfp_mant_width + 1) * (n + i * block_dim) ) for n in range(block_dim))
            scale_data  += (mx_fp_scales[i] << (mxfp_scale_width) * i)
        dut.element_data_in.value = ele_data
        dut.scale_data_in.value = scale_data
        dut.data_in_valid.value = 1
        dut.data_out_ready.value = 1
        await Timer(2, units="ns")

        cocotb.log.info("<-------  INPUT DATA  --------->")
        cocotb.log.info(f" Input Data : {generator.blockwise_convert_to_float(dut.element_data_in.value , dut.scale_data_in.value, comp_dim // block_dim, mxfp_exp_width, mxfp_mant_width)} ELE Binary: {dut.element_data_in.value}, SCALE Binary: {dut.scale_data_in.value}")
        
        await Timer(12, units="ns")
        cocotb.log.info("<-------  Intermediate DATA  --------->")
        # cocotb.log.info(f"Internal Signal : block_a {dut.block_adder_tree[1].fp_full_precision_add_tree.data_in.value}")
        # cocotb.log.info(f"Internal Signal : block_a {dut.block_adder_tree[1].fp_full_precision_add_tree.data_out.value}")
        # cocotb.log.info(f"Internal Signal : block_b {generator.fp_gen.full_precision_fp_float_convertion(mxfp_exp_width + 1, mxfp_mant_width, dut.block_adder_tree[1].fp_full_precision_add_tree.data_out.value)}")
        cocotb.log.info(f"Internel Signal : block_element_data_out {dut.block_element_data_out.value}, Converted Float : {generator.blockwise_convert_to_float(dut.block_element_data_out.value , dut.stored_block_scale_data.value, 1, mxfp_exp_width + 1, mxfp_mant_width)}")
        cocotb.log.info(f"Internel Signal : stored_block_scale_data {dut.stored_block_scale_data.value}")
        cocotb.log.info(f"Internel Signal : converted_fp_out {dut.converted_fp_out.value}")
        cocotb.log.info(f"Internal Signal : unary_element_in {dut.mxfp_2_fp[1].mxfp_2_fp.element_data_in.value}, {dut.mxfp_2_fp[1].mxfp_2_fp.scale_data_in.value}")
        cocotb.log.info(f"Internal Signal : unary_element_out {dut.mxfp_2_fp[1].mxfp_2_fp.fp_out.value}, {generator.fp_gen.full_precision_fp_float_convertion(mxfp_exp_width + 1, mxfp_mant_width, dut.mxfp_2_fp[1].mxfp_2_fp.fp_out.value)}")

        cocotb.log.info(f"Internal Signal : fp_inter_block_adder_tree {dut.fp_inter_block_adder_tree.data_in.value}")
        cocotb.log.info(f"Internal Signal : block_data_out_valid {dut.block_data_out_valid.value}")
        cocotb.log.info(f"Internal Signal : block_data_out_ready {dut.block_data_out_ready.value}")
        cocotb.log.info(f"Internal Signal : scale_storage_valid {dut.scale_storage_out_valid.value}")

        cocotb.log.info(f"Internal Signal : fp_inter_block_adder_tree {dut.blockwise_addition_valid.value}")
        cocotb.log.info(f"Internal Signal : fp_inter_block_adder_tree {dut.fp_inter_block_adder_tree.data_in_valid.value}")

        cocotb.log.info("<-------  OUTPUT DATA --------->")
        cocotb.log.info(f"Output Binary: {dut.fp_out.value}, Converted Float : {generator.fp_gen.full_precision_fp_float_convertion(output_fp_exp_width, output_fp_mant_width, dut.fp_out.value)}")

@pytest.mark.dev
def test_simple_fp_addition():
    # Run tests with different params
    veri_runner(
        group = "mx_fp_operation",
        module = "mx_fp_mv",
        additional_include_paths = [
            "/Users/georgewu/Documents/Cambridge/Coprocessor_for_Llama/src/basic_components/buffer",
            "/Users/georgewu/Documents/Cambridge/Coprocessor_for_Llama/src/basic_components/fp_operation",
            "/Users/georgewu/Documents/Cambridge/Coprocessor_for_Llama/src/basic_components/conversion",
            "/Users/georgewu/Documents/Cambridge/Coprocessor_for_Llama/src/basic_components/common"
        ],       
        module_param_list=[
            {"MXFP_EXP_WIDTH" : mxfp_exp_width, "MXFP_MANT_WIDTH" : mxfp_mant_width, "MXFP_SCALE_WIDTH" : mxfp_scale_width, "BLOCK_EXT_MANT_WIDTH_PER_LAYER" : block_ext_mant_width, "BLOCK_EXT_EXP_WIDTH_PER_LAYER" : block_ext_exp_width, "FP_EXT_MANT_WIDTH_PER_LAYER" : fp_ext_mant_width, "FP_EXT_EXP_WIDTH_PER_LAYER" : fp_ext_exp_width, "COMP_DIM" : comp_dim, "BLOCK_DIM" : block_dim},
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_simple_fp_addition()
