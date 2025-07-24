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
     
        await Timer(40, units="ns")
        for i in range(size):
            await RisingEdge(dut.clk)
            # Generate random floating point values
            # fp_values, results = generator.generate_fp_input(2)
            print(f"mx_scale: {mx_scale}, mx_elems: {mx_elems}")
            dut.data_in.value = mx_elems[0][i]
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)


        while True:
            await RisingEdge(dut.clk)
            cocotb.log.info(f"Result: {dut.data_out.value}")

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
        group = "common",
        module = "mult_reg",
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
                "DATA_WIDTH" : 8, 
                "REG_N" : 4},
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_simple_pe()
