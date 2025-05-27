#!/usr/bin/env python3

# This script tests the fixed point linear
import os, logging

import cocotb
from cocotb.log import SimLog
from cocotb.triggers import *

from cfl_cocotb.testbench import Testbench
from cfl_cocotb.streaming import (
    StreamDriver,
    StreamMonitor,
)

import pytest
from cfl_cocotb.runner import veri_runner
from cocotb.triggers import Timer, RisingEdge

from typing import Literal, Optional, Tuple, Union, Dict, List
import math
from functools import partial
import random
import argparse
from pathlib import Path


# parser = argparse.ArgumentParser(description="Greet someone.")
# parser.add_argument("--benchmark", type=str, default="general")
# args = parser.parse_args()

logger = logging.getLogger("testbench")
logger.setLevel(logging.DEBUG)
current_path = Path(__file__).resolve().parent

testcase_name       = "attention"
instr_file          = f"{current_path.parent.parent.parent}/test/Layerwise_Benchmark/{testcase_name}.mem"
hbm_element_file    = f"{current_path}/workload/hbm_ele.mem"
hbm_scale_file      = f"{current_path}/workload/hbm_scale.mem"
fp_mem_file         = f"{current_path}/workload/fp.mem"
fixed_mem_file      = f"{current_path}/workload/fixed.mem"
INSTRUCTION_LENGTH = 16


class SimTOP(Testbench):
    def __init__(self, dut, element_file, scale_file, instr_file) -> None:
        super().__init__(dut, dut.clk, dut.rst)
        self.element_file = element_file
        self.scale_file = scale_file
        self.instr_file = instr_file

        if not hasattr(self, "log"):
            self.log = SimLog("%s" % (type(self).__qualname__))

        self.data_in_0_driver = StreamDriver(
            dut.clk,
            dut.instruction,
            dut.instruction_valid,
            dut.instruction_ready,
        )

    def generate_inputs(self):
        inputs = []
        with open(self.instr_file, 'r') as file:
            for line in file:
                stripped_line = line.strip()
                if stripped_line:  # skip empty lines
                    inputs.append(int(stripped_line, base=16))
        return inputs

    def assign_workload(self):
        pass
    
    async def run_test(self):
        self.assign_workload()
        await self.reset()
        logger.info(f"Reset finished")
        inputs = self.generate_inputs()
        self.data_in_0_driver.load_driver(inputs)
        await Timer(500, units="us")

@cocotb.test()
async def test(dut):
    # cocotb.start_soon(check_signal(dut))
    tb = SimTOP(dut, hbm_element_file, hbm_scale_file, instr_file)
    await tb.run_test()

async def check_signal(dut):
    await Timer(40, units="ns")


@pytest.mark.dev
def SimToP_test():
    # Run tests with different params
    veri_runner(
        group = "system",
        module = "SimTop",
        additional_include_paths = [
            "../../../src/basic_components/common",
            "../../../src/basic_components/mx_fp_operation",
            "../../../src/basic_components/fp_operation",
            "../../../src/basic_components/conversion",
            "../../../src/basic_components/buffer",
            "../../../src/basic_components/fixed_operation",
            "../../../src/frontend",
            "../../../src/control",
            "../../../src/matrix_machine",
            "../../../src/vector_machine",
            "../../../src/scalar_machine",
            "../../../src/memory/matrix_sram",
            "../../../src/memory/scratch_sram",
            "../../../src/memory/scalar_sram",
            "../../../src/memory/HBM",
            "../../../src/core"
        ],       
        definitions_path = ["../../../src/definitions", 
                            "../../../src/memory/HBM/TileLink_Lib" ],
        module_param_list=[
            {
                "INSTRUCTION_LENGTH": INSTRUCTION_LENGTH,
                "FAKE_HBM_ELEMENT_INIT_FILE": f"\"{hbm_element_file}\"",
                "FAKE_HBM_SCALE_INIT_FILE": f"\"{hbm_scale_file}\"",
                "FP_MEM_INIT_FILE": f"\"{fp_mem_file}\"",
                "FIXED_MEM_INIT_FILE": f"\"{fixed_mem_file}\""
            }
        ],
        trace = True,
    )


if __name__ == "__main__":
    SimToP_test()


