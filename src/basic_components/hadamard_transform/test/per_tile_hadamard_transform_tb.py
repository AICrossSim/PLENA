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
from cfl_cocotb import SRC_PATH
from math import ceil, log2
import math

exp_width = 4
mant_width = 3
vect_dim = 4

level = math.ceil(math.log2(vect_dim))


generator = FpGenerator(exp_width, mant_width)

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)


@cocotb.test()
async def random_hadamard_transform_test(dut):
    
    cocotb.start_soon(Clock(dut.clk, 2, units="ns").start())  # 2ns period (1GHz clock)
    
    await Timer(5, units="ns")
    cocotb.log.info("Starting fp multiply test")
    # Apply Reset
    dut.rst.value = 0
    await Timer(5, units="ns")  # Hold reset for 5ns
    dut.rst.value = 1
    await Timer(5, units="ns")  # Allow some settling time

@pytest.mark.dev
def simple_test():
    # Run tests with different params
    veri_runner(
        group = "basic_components",
        module = "per_tile_hadamard_transform",
        additional_include_paths = [
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/mx_fp_operation"),
            str(SRC_PATH / "basic_components/fp_operation"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/buffer"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/int_operation"),
            str(SRC_PATH / "basic_components/cast"),
            str(SRC_PATH / "basic_components/systolic_gemm_mx"),
            str(SRC_PATH / "basic_components/gemv"),
            str(SRC_PATH / "basic_components/synopsis"),
            str(SRC_PATH / "basic_components/synopsis_ip_inst"),
            str(SRC_PATH / "frontend"),
            str(SRC_PATH / "control"),
            str(SRC_PATH / "matrix_machine"),
            str(SRC_PATH / "vector_machine"),
            str(SRC_PATH / "scalar_machine"),
            str(SRC_PATH / "memory/matrix_sram"),
            str(SRC_PATH / "memory/vector_sram"),
            str(SRC_PATH / "memory/scratch_sram"),
            str(SRC_PATH / "memory/scalar_sram"),
            str(SRC_PATH / "memory/HBM"),
            str(SRC_PATH / "core")
        ],       
        definitions_path = [
            str(SRC_PATH / "definitions"), 
            str(SRC_PATH / "memory/HBM/TileLink_Lib"),
        ],
        module_param_list=[
            {"TILESIZE" : vect_dim, "EXP_WIDTH" : exp_width, "MANT_WIDTH" : mant_width},
        ],
        trace = True,
    )

if __name__ == "__main__":
    simple_test()
