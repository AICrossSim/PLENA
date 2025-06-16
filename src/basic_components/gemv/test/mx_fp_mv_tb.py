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

product_ext_exp_width = 0
product_ext_mant_width = 0

block_ext_mant_width = 0
block_ext_exp_width = 1

fp_ext_mant_width = 0
fp_ext_exp_width = 1


block_level = math.ceil(math.log2(block_dim))
fp_level = math.ceil(math.log2(comp_dim // block_dim))

inter_fp_exp_width = mxfp_exp_width + block_ext_exp_width * block_level + fp_ext_exp_width * fp_level + product_ext_exp_width
inter_fp_mant_width = mxfp_mant_width + block_ext_mant_width * block_level + fp_ext_mant_width * fp_level + product_ext_mant_width

print(f"inter_fp_exp_width: {inter_fp_exp_width}, inter_fp_mant_width: {inter_fp_mant_width}")

generator = MXBlockFPConverter(mxfp_exp_width, mxfp_mant_width, mxfp_scale_width, block_dim)

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)

@cocotb.test()
async def random_mxfp_mv_test(dut):
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
        
        m_mx_fp_scales, m_mx_fp_elems = generator.generate_certain_values([1.24, 2.01, 1.0231, 0.9820])
        m_ele_data = 0
        m_scale_data = 0
        for i in range(comp_dim * comp_dim // block_dim):
            m_ele_data    += sum((m_mx_fp_elems[i][n] << (mxfp_exp_width + mxfp_mant_width + 1) * (n + i * block_dim) ) for n in range(block_dim))
            m_scale_data  += (m_mx_fp_scales[i] << (mxfp_scale_width) * i)
        
        dut.element_m_data.value = m_ele_data
        dut.scale_m_data.value = m_scale_data
        dut.m_data_valid.value = 1

        v_mx_fp_scales, v_mx_fp_elems = generator.generate_certain_values([1.24, 2.01, 1.0231, 0.9820])
        v_ele_data = 0
        v_scale_data = 0
        for i in range(comp_dim // block_dim):
            v_ele_data    += sum((v_mx_fp_elems[i][n] << (mxfp_exp_width + mxfp_mant_width + 1) * (n + i * block_dim) ) for n in range(block_dim))
            v_scale_data  += (v_mx_fp_scales[i] << (mxfp_scale_width) * i)

        dut.element_v_data.value = v_ele_data
        dut.scale_v_data.value = v_scale_data
        dut.v_data_valid.value = 1
        dut.out_data_ready.value = 1
        
        await Timer(6, units="ns")
        cocotb.log.info("<-------  INPUT DATA  --------->")
        cocotb.log.info(f" Input Data : {generator.blockwise_convert_to_float(dut.element_m_data.value , dut.scale_m_data.value, (comp_dim * comp_dim) // block_dim, mxfp_exp_width, mxfp_mant_width)} ELE Binary: {dut.element_m_data.value}, SCALE Binary: {dut.scale_m_data.value}")
        cocotb.log.info(f" Input Data : {generator.blockwise_convert_to_float(dut.element_v_data.value , dut.scale_v_data.value, comp_dim // block_dim, mxfp_exp_width, mxfp_mant_width)} ELE Binary: {dut.element_v_data.value}, SCALE Binary: {dut.scale_v_data.value}")

        cocotb.log.info("<-------  INTERNAL DATA --------->")
        cocotb.log.info(f"dot product port A: {dut.row_matrix_by_vec[0].dot_product_inst.element_a_in.value} ")
        cocotb.log.info(f"dot product port A scale {dut.row_matrix_by_vec[0].dot_product_inst.scale_a_in.value} ")
        cocotb.log.info(f"dot product port B: {dut.row_matrix_by_vec[0].dot_product_inst.element_b_in.value} ")
        cocotb.log.info(f"dot product port B scale {dut.row_matrix_by_vec[0].dot_product_inst.scale_b_in.value} ")
        cocotb.log.info(f"SCALE_BIAS : {bin(dut.row_matrix_by_vec[0].dot_product_inst.SCALE_BIAS.value)} ")
        
        cocotb.log.info("<-------  INTERNAL Within Dot Prod Layer --------->")
        cocotb.log.info(f"element_product_vec       {dut.row_matrix_by_vec[0].dot_product_inst.element_product_vec.value}" )
        cocotb.log.info(f"scale_product_vec         {dut.row_matrix_by_vec[0].dot_product_inst.scale_product_vec.value}" )
        cocotb.log.info(f"dot product result in fp  {dut.row_matrix_by_vec[0].dot_product_inst.data_out.value}" )

        cocotb.log.info("<-------  INTERNAL Within Dot Prod Adder Tree --------->")    
        cocotb.log.info(f"block_element_data_in     {dut.row_matrix_by_vec[0].dot_product_inst.adder_tree.element_data_in.value}" )   
        cocotb.log.info(f"block_scale_data_in       {dut.row_matrix_by_vec[0].dot_product_inst.adder_tree.scale_data_in.value}" )
        cocotb.log.info(f"block_element_data_out    {dut.row_matrix_by_vec[0].dot_product_inst.adder_tree.block_element_data_out.value}" )    

        cocotb.log.info(f"converted_fp_out {dut.row_matrix_by_vec[0].dot_product_inst.adder_tree.converted_fp_out.value}" )          


        cocotb.log.info("<-------  INTERNAL Dot Product Layer DATA --------->")
        cocotb.log.info(f"fp_dot_out : Binary: {dut.fp_dot_out.value} ")
        cocotb.log.info(f"Converted FP : {generator.fp_gen.multi_fp_conversion(inter_fp_exp_width, inter_fp_mant_width, dut.fp_dot_out.value)} ")

        await Timer(8, units="ns")
        cocotb.log.info("<-------  OUTPUT DATA  --------->")
        cocotb.log.info(f"Output Element Data : Binary: {dut.element_out_data.value} ")
        cocotb.log.info(f"Output Scale Data : Binary: {dut.scale_out_data.value} ")
        cocotb.log.info(f" Result : {generator.blockwise_convert_to_float(dut.element_out_data.value , dut.scale_out_data.value, comp_dim // block_dim, mxfp_exp_width, mxfp_mant_width)}")
        




@pytest.mark.dev
def mxfp_mv_test():
    # Run tests with different params
    veri_runner(
        group = "mv_unit",
        module = "mx_fp_mv",
        additional_include_paths = [
            "../../../../src/basic_components/mx_fp_operation",
            "../../../../src/basic_components/buffer",
            "../../../../src/basic_components/fp_operation",
            "../../../../src/basic_components/conversion",
            "../../../../src/basic_components/common"
        ],       
        module_param_list=[
            {"MXFP_MANT_WIDTH" : mxfp_mant_width, "MXFP_EXP_WIDTH" : mxfp_exp_width, "MXFP_SCALE_WIDTH" : mxfp_scale_width, "COMPUTE_DIM" : comp_dim, "BLOCK_DIM" : block_dim, 
             "PRODUCT_EXT_MANT_WIDTH" : product_ext_mant_width, "PRODUCT_EXT_EXP_WIDTH" : product_ext_exp_width,
             "FP_ADD_EXT_MANT_WIDTH" : fp_ext_mant_width, "FP_ADD_EXT_EXP_WIDTH" : fp_ext_exp_width, 
             "BLOCK_ADD_EXT_MANT_WIDTH" : block_ext_mant_width, "BLOCK_ADD_EXT_EXP_WIDTH" : block_ext_exp_width,
             "OUTPUT_FP_ROUND_EN" : 0},
        ],
        trace = True,
    )

if __name__ == "__main__":
    mxfp_mv_test()
