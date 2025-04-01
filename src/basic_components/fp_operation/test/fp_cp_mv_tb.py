#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os
from pathlib import Path
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
from cfl_cocotb import veri_runner, FpGenerator
from math import ceil, log2
import math

exp_width = 4
mant_width = 3
tile_size = 2

level = math.ceil(math.log2(tile_size))

product_ext_exp_width = 1
product_ext_mant_width = 0

product_exp_width = exp_width + product_ext_exp_width
product_mant_width = mant_width + product_ext_mant_width

print(f"Product exp width: {product_exp_width}, mant width: {product_mant_width}")

add_ext_exp_width = 1
add_ext_mant_width = 0

add_exp_width = product_exp_width + add_ext_exp_width * level
add_mant_width = product_mant_width + add_ext_mant_width * level

print(f"Addition exp width: {add_exp_width}, mant width: {add_mant_width}")

output_exp_width = 4
output_mant_width = 3

print(f"Output exp width: {output_exp_width}, mant width: {output_mant_width}")


generator = FpGenerator(exp_width, mant_width)

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

        # m_fp_values, m_results = generator.generate_fp_input(tile_size)
        m_fp_values, m_results = generator.generate_specified_value_fp_input([4.517, 2.18, 1.98, 1.30])
        m_data = sum((m_results[n] << (exp_width + mant_width + 1) * n ) for n in range(tile_size * tile_size))
        dut.m_data.value = m_data

        v_fp_values, v_results = generator.generate_specified_value_fp_input([2.4, 1.4])
        v_data = sum((v_results[n] << (exp_width + mant_width + 1) * n ) for n in range(tile_size))
        dut.v_data.value = v_data

        # await RisingEdge(dut.clk)
        await Timer(2, units="ns")
        cocotb.log.info("<-------  Matrix INPUT DATA  --------->")
        for m in range(tile_size * tile_size):
            cocotb.log.info(f"Matrix Value at index {m} : {m_fp_values[m]}, Result : {generator.custom_fp_to_float(m_results[m])}, Binary: {bin(dut.m_data.value)}")
        
        cocotb.log.info("<-------  Vector INPUT DATA  --------->")
        for v in range(tile_size):
            cocotb.log.info(f"Vector Value at index {v} : {v_fp_values[v]}, Result : {generator.custom_fp_to_float(v_results[v])}, Binary: {bin(dut.v_data.value)}")

        dut.m_data_valid.value = 1
        dut.v_data_valid.value = 1
        dut.out_data_ready.value = 1

        await Timer(4, units="ns")
        product_results = []
        for i in range(0, tile_size):
            # Get the expected result
            product_results.append(sum(m_fp_values[i * tile_size + j] * v_fp_values[j] for j in range(tile_size)))
        cocotb.log.info("<-------  Product Vector DATA  --------->")
        # cocotb.log.info(f"Internal fp_vector_mult_inst Binary Results : {dut.fp_vector_mult_inst.data_out.value}")
        cocotb.log.info(f"Internal RAW Results : {dut.dot_product_data_out.value}")
        cocotb.log.info(f"Internal Converted Results : {generator.translate_packed_array_fp(tile_size, add_exp_width, add_mant_width, dut.dot_product_data_out.value)}")
        cocotb.log.info(f"Internal Product Ref : {product_results}")

        await Timer(4, units="ns")
        cocotb.log.info("<-------  Rounded DATA  --------->")
        cocotb.log.info(f"Internal Converted Results : {generator.translate_packed_array_fp(tile_size, output_exp_width, output_mant_width, dut.out_data.value)}")




@pytest.mark.dev
def simple_test_mv_unit():
    # Run tests with different params
    veri_runner(
        group = "fp_operation",
        module = "fp_cp_mv",
        additional_include_paths = [
            "/Users/georgewu/Documents/Cambridge/Coprocessor_for_Llama/src/basic_components/buffer",
            "/Users/georgewu/Documents/Cambridge/Coprocessor_for_Llama/src/basic_components/common"                                        
        ],
        module_param_list=[
            {"COMPUTE_DIM" : tile_size, "IN_EXP_WIDTH" : exp_width, "IN_MAN_WIDTH" : mant_width, "PRODUCT_EXT_EXP_WIDTH" : product_ext_exp_width, "PRODUCT_EXT_MANT_WIDTH" : product_ext_mant_width, "ADD_EXT_EXP_WIDTH" : add_ext_exp_width, "ADD_EXT_MANT_WIDTH" : add_ext_mant_width, "OUT_EXP_WIDTH" : output_exp_width, "OUT_MAN_WIDTH" : output_mant_width},
        ],
        trace = True,
    )

if __name__ == "__main__":
    simple_test_mv_unit()
