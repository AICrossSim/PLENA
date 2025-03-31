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

exp_width = 5
mant_width = 3
ext_mant_width = 0
ext_exp_width = 1
vect_dim = 3
level = math.ceil(math.log2(vect_dim))

output_man_width = mant_width + ext_mant_width * level

output_exp_width = exp_width + ext_exp_width * level



# TEMP
intermediate_man_width = mant_width + ext_mant_width 
intermediate_exp_width = exp_width + ext_exp_width
# print("intermediate_man_width ", intermediate_man_width)


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
        
        fp_values, results = generator.generate_specified_value_fp_input([1152.0, 8192.0, 9216.0, 3584.0])
        
        input_data = sum((results[n] << (exp_width + mant_width + 1) * n ) for n in range(vect_dim))
        dut.data_in.value = input_data
        # await RisingEdge(dut.clk)
        await Timer(2, units="ns")
        cocotb.log.info("<-------  INPUT DATA  --------->")
        cocotb.log.info(f"Input Binary {dut.data_in.value}")
        for m in range(vect_dim):
            cocotb.log.info(f"Value at index {m} : {fp_values[m]}, Result : {generator.custom_fp_to_float(results[m])}, Binary: {bin(results[m])}")
        
        cocotb.log.info(f"Input Binary {dut.data_in.value}")
        dut.data_in_valid.value = 1
        dut.data_out_ready.value = 1

        await Timer(2, units="ns")
        # cocotb.log.info(f"Internal data_storage: {dut.gen_adder_tree.data_storage.value}")
        # cocotb.log.info(f"Internal valid: {dut.gen_adder_tree.valid.value}")
        # cocotb.log.info(f"Internal ready: {dut.gen_adder_tree.ready.value}")
        # cocotb.log.info(f"Internal sum: {dut.gen_adder_tree.sum.value}")
        # cocotb.log.info(f"Internal Level 1 data_in: {dut.gen_adder_tree.level[1].full_precision_add_layer.data_in.value}")
        # cocotb.log.info(f"Internal Level 1 data_ou: {dut.gen_adder_tree.level[1].full_precision_add_layer.data_out.value}")
        
        await Timer(2, units="ns")
        cocotb.log.info(f"Internal data_storage: {dut.gen_adder_tree.data_storage.value}")
        cocotb.log.info(f"Internal sum: {dut.gen_adder_tree.sum.value}")
        
        cocotb.log.info(f"Internal Level 0 updated exp: {dut.gen_adder_tree.level[0].full_precision_add_layer.updated_exp.value}")
        cocotb.log.info(f"Internal Level 0  UPDATED_BIAS: {dut.gen_adder_tree.level[0].full_precision_add_layer.UPDATED_BIAS.value}")
        cocotb.log.info(f"Internal Level 1 data_a: {dut.gen_adder_tree.level[1].full_precision_add_layer.pair[0].fp_add.data_a.value}")
        cocotb.log.info(f"converted: {generator.full_precision_fp_float_convertion(intermediate_exp_width, intermediate_man_width, dut.gen_adder_tree.level[1].full_precision_add_layer.pair[0].fp_add.data_a.value)}")        
        cocotb.log.info(f"Internal Level 1 data_b: {dut.gen_adder_tree.level[1].full_precision_add_layer.pair[0].fp_add.data_b.value}")
        cocotb.log.info(f"converted: {generator.full_precision_fp_float_convertion(intermediate_exp_width, intermediate_man_width, dut.gen_adder_tree.level[1].full_precision_add_layer.pair[0].fp_add.data_b.value)}")   
        cocotb.log.info(f"Internal Level 1 data_out: {dut.gen_adder_tree.level[1].full_precision_add_layer.pair[0].fp_add.data_out.value}")

        
        # await Timer(2, units="ns")
        # cocotb.log.info(f"Internal data_storage: {dut.gen_adder_tree.data_storage.value}")
        # cocotb.log.info(f"Internal sum: {dut.gen_adder_tree.sum.value}")
        # cocotb.log.info(f"Internal Level 1 data_in: {dut.gen_adder_tree.level[1].full_precision_add_layer.data_in.value}")
        # cocotb.log.info(f"Internal Level 1 data_ou: {dut.gen_adder_tree.level[1].full_precision_add_layer.data_out.value}")

        # await Timer(2, units="ns")
        # cocotb.log.info(f"Internal data_storage: {dut.gen_adder_tree.data_storage.value}")
        # cocotb.log.info(f"Internal sum: {dut.gen_adder_tree.sum.value}")
        # cocotb.log.info(f"Internal valid: {dut.gen_adder_tree.valid.value}")
        # cocotb.log.info(f"Internal ready: {dut.gen_adder_tree.ready.value}")


        await Timer(4, units="ns")
        fp_results = sum(fp_values[g] for g in range(vect_dim))
        cocotb.log.info(f"Expected result : {fp_results}, DUT BIN_out: {dut.data_out.value}, Converted Float : {generator.full_precision_fp_float_convertion(output_exp_width, output_man_width, dut.data_out.value)}")


@pytest.mark.dev
def test_simple_fp_addition():
    # Run tests with different params
    veri_runner(
        group = "fp_operation",
        module = "fp_adder_tree",
        additional_include_paths = [
            "/Users/georgewu/Documents/Cambridge/Coprocessor_for_Llama/src/basic_components/buffer"
        ],       
        module_param_list=[
            {"VEC_DIM" : vect_dim, "IN_EXP_WIDTH" : exp_width, "IN_MAN_WIDTH" : mant_width, "EXT_MANT_WIDTH_PER_LAYER" : ext_mant_width, "EXT_EXP_BITS_PER_LAYER" : ext_exp_width},
        ],
        trace = True,
    )

if __name__ == "__main__":
    test_simple_fp_addition()
