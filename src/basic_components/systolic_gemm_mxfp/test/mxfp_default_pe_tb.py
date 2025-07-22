#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os

from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock

from cfl_cocotb import veri_runner, MXBlockFPConverter, SRC_PATH
from quant.quantizer import minifloat_ieee_quantizer
from cfl_cocotb.torch_fp_conversion import bin_2_fp
import torch

element_exp_width = 4
element_mant_width = 3
scale_width = 8

fp_exp_width = 7
fp_mant_width = 8

generator = MXBlockFPConverter(element_exp_width, element_mant_width, scale_width, block_size = 4)

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)
from cfl_cocotb.torch_fp_conversion import fp_2_bin

@cocotb.test()
async def simple_random_mxfp_test(dut):
    async def send_data(dut):
        test_data_1 = 2.023
        test_data_2 = 3.012
        size = 4
        mx_scale, mx_elems = generator.generate_certain_values([test_data_1, test_data_2, 1.0, 1.0])
        tensor_ = torch.tensor([test_data_1, test_data_2, 1.0, 1.0])
        from quant.quantizer.hardware_quantizer.mxfp import _mx_fp_quantize_hardware
        from cfl_cocotb.torch_fp_conversion import pack_fp_to_bin
        mx_int_, exp, mant, bias = _mx_fp_quantize_hardware(tensor_.unsqueeze(0), 8, 3,8, [1,4])
        result = pack_fp_to_bin(exp, mant, 4, 3)

        mult_result = mant * mant * 2**(exp + exp)

        mx_int_mult, mult_exp, mult_mant, mult_bias = _mx_fp_quantize_hardware(mult_result, 8, 3,8, [1,4])
        qmult_result = pack_fp_to_bin(mult_exp, mult_mant, 4, 3)

        result = test_data_1 * test_data_1 + test_data_2 * test_data_2 + 2
        result = [test_data_1 * test_data_1, test_data_2 * test_data_2, 1, 1]
        qresult = minifloat_ieee_quantizer(torch.tensor(result), 16, 7)
        breakpoint()
        await Timer(40, units="ns")
        for i in range(size):
            await RisingEdge(dut.clk)
            # Generate random floating point values
            # fp_values, results = generator.generate_fp_input(2)
            print(f"mx_scale: {mx_scale}, mx_elems: {mx_elems}")
            dut.in_top_element.value = mx_elems[0][i]
            dut.in_top_scale.value = mx_scale[0]
            dut.system_top_valid.value = 1
            dut.in_left_element.value = mx_elems[0][i]
            dut.in_left_scale.value = mx_scale[0]
            dut.system_left_valid.value = 1
            dut.out_result_ready.value = 1
        await RisingEdge(dut.clk)
        dut.in_left_element.value = 0
        dut.in_left_scale.value = 0
        dut.system_left_valid.value = 0
        dut.in_top_element.value = 0
        dut.in_top_scale.value = 0
        dut.system_top_valid.value = 0
        dut.out_result_ready.value = 0


        while True:
            await RisingEdge(dut.clk)
            # cocotb.log.info(f"Result: {qresult}")
            cocotb.log.info(f"Result: {fp_2_bin(qresult, 7, 8)}")
            print("fp_out", bin_2_fp(int(dut.out_fp.value.integer), 7, 8))
            breakpoint()
            if dut.out_fp.value.integer != 0:
                cocotb.log.info(f"Result: {dut.out_fp.value}")
                cocotb.log.info(f"Result: {bin_2_fp(int(dut.out_fp.value.integer), 7, 8)}")

    # Start clock generation
    cocotb.start_soon(Clock(dut.clk, 5, units="ns").start()) 
    cocotb.start_soon(send_data(dut)) 

    await Timer(10, units="ns")
    cocotb.log.info("Starting fp addition test")
    await Timer(10, units="ns")
    dut.rst.value = 1
    await Timer(10, units="ns")
    dut.rst.value = 0   
    await Timer(10, units="ns")

    while True:
        await RisingEdge(dut.clk)
        if dut.system_top_valid.value == 1 and dut.system_left_valid.value == 1 and dut.mult_ready.value == 1:
            dut.mult_valid.value = 1
            break
        else:
            dut.mult_valid.value = 0

    await Timer(1, units="us")

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
        group = "systolic_gemm_mxfp",
        module = "mxfp_default_pe",
        additional_include_paths = [
            str(SRC_PATH / "basic_components/mx_fp_operation"),
            str(SRC_PATH / "basic_components/buffer"),
            str(SRC_PATH / "basic_components/fp_operation"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/int_operation")
        ],
        definitions_path = [],
        module_param_list=[
            {
                "MXFP_T_EXP_WIDTH" : element_exp_width, 
                "MXFP_T_MANT_WIDTH" : element_mant_width, 
                "MXFP_L_EXP_WIDTH" : element_exp_width, 
                "MXFP_L_MANT_WIDTH" : element_mant_width, 
                "MXFP_SCALE_WIDTH" : scale_width, 
                "ACC_FP_EXP_WIDTH" : fp_exp_width, 
                "ACC_FP_MANT_WIDTH" : fp_mant_width, 
                "PROD_EXT_EXP_WIDTH" : 0, 
                "PROD_EXT_MANT_WIDTH" : 0},
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_simple_pe()
