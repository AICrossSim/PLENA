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
vect_dim = 4

level = math.ceil(math.log2(vect_dim))

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

        # fp_values, results = generator.generate_fp_input(vect_dim)
        fp_values, results = generator.generate_specified_value_fp_input([40.517, 218.18, 129.98, 210.00, 30.231, 41.77, 75.2, 19.29])
        input_data_a = sum((results[n] << (exp_width + mant_width + 1) * n ) for n in range(vect_dim))
        input_data_b = sum((results[n + vect_dim] << (exp_width + mant_width + 1) * n ) for n in range(vect_dim))
        dut.data_a_in.value = input_data_a
        dut.data_b_in.value = input_data_b

        # await RisingEdge(dut.clk)
        await Timer(2, units="ns")
        cocotb.log.info("<-------  INPUT DATA  --------->")
        for m in range(vect_dim):
            cocotb.log.info(f"Value at index {m} : {fp_values[m]}, Result : {generator.custom_fp_to_float(results[m])}, Binary: {bin(results[m])}")
        
        cocotb.log.info(f"Input Binary data_a {dut.data_a_in.value}")
        cocotb.log.info(f"Input Binary data_b {dut.data_b_in.value}")
        # generator.translate_packed_array_fp(vect_dim, exp_width, mant_width, dut.data_a_in.value)

        dut.data_a_in_valid.value = 1
        dut.data_b_in_valid.value = 1
        dut.data_out_ready.value = 1

        await Timer(4, units="ns")
        product_results = []
        for i in range(0, vect_dim):
            # Get the expected result
            product_results.append(fp_values[i] * fp_values[i + vect_dim])
        cocotb.log.info("<-------  Product Vector DATA  --------->")
        cocotb.log.info(f"Internal fp_vector_mult_inst Binary Results : {dut.fp_vector_mult_inst.data_out.value}")
        cocotb.log.info(f"Internal Product Binary Results : {dut.product_vec.value}")
        cocotb.log.info(f"Internal Converted Results : {generator.translate_packed_array_fp(vect_dim, product_exp_width, product_mant_width, dut.product_vec.value)}")
        cocotb.log.info(f"Internal Product Ref : {product_results}")

        await Timer(2, units="ns")
        fp_results = sum(product_results)
        cocotb.log.info("<-------  ADDITION DATA  --------->")
        cocotb.log.info(f"Expected result : {fp_results}, DUT BIN_out: {dut.data_out.value}, Converted Float : {generator.full_precision_fp_float_convertion(add_exp_width, add_mant_width, dut.data_out.value)}")


@pytest.mark.dev
def test_simple_fp_addition():
    # Run tests with different params
    veri_runner(
        group = "fp_operation",
        module = "fp_dot_product",
        additional_include_paths = [
            "/Users/georgewu/Documents/Cambridge/Coprocessor_for_Llama/src/basic_components/buffer",
            "/Users/georgewu/Documents/Cambridge/Coprocessor_for_Llama/src/basic_components/common"                                        
        ],
        module_param_list=[
            {"VEC_DIM" : vect_dim, "EXP_WIDTH" : exp_width, "MANT_WIDTH" : mant_width, "PRODUCT_EXT_EXP_WIDTH" : product_ext_exp_width, "PRODUCT_EXT_MANT_WIDTH" : product_ext_mant_width, "ADD_EXT_EXP_WIDTH" : add_ext_exp_width, "ADD_EXT_MANT_WIDTH" : add_ext_mant_width},
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_simple_fp_addition()
