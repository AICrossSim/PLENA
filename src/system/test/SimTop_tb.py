#!/usr/bin/env python3

# This script tests the fixed point linear
import os, logging

import cocotb
from cocotb.log import SimLog
from cocotb.triggers import *
from cfl_cocotb.runner import veri_runner, SRC_PATH
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

logger = logging.getLogger("testbench")
logger.setLevel(logging.DEBUG)
current_path = Path(__file__).resolve().parent

testcase_name = "matrix"


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
    tb = SimTOP(dut, os.environ["HBM_ELEMENT_FILE"], os.environ["HBM_SCALE_FILE"], os.environ["INSTR_FILE"])
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
            str(SRC_PATH / "basic_components/common"),
            str(SRC_PATH / "basic_components/mx_fp_operation"),
            str(SRC_PATH / "basic_components/fp_operation"),
            str(SRC_PATH / "basic_components/conversion"),
            str(SRC_PATH / "basic_components/buffer"),
            str(SRC_PATH / "basic_components/fixed_operation"),
            str(SRC_PATH / "basic_components/int_operation"),
            str(SRC_PATH / "basic_components/cast"),
            str(SRC_PATH / "basic_components/systolic_gemm_mxfp"),
            str(SRC_PATH / "basic_components/gemv"),
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
            str(SRC_PATH / "memory/HBM/TileLink_Lib")
        ],
        module_param_list=[
            {
                "INSTRUCTION_LENGTH": INSTRUCTION_LENGTH,
                "FAKE_HBM_ELEMENT_INIT_FILE": f"\"{os.environ['HBM_ELEMENT_FILE']}\"",
                "FAKE_HBM_SCALE_INIT_FILE": f"\"{os.environ['HBM_SCALE_FILE']}\""
            }
        ],
        trace = True,
    )

def init_mem():
    global hbm_element_file, hbm_scale_file, instr_file
    
    from assembler.instruction_mapping_pipeline import instruction_mapping_pipeline, parse_args
    from cfl_tools import PROJECT_PATH
    from pathlib import Path
    from assembler.memory_mapping.rand_gen import RandomTensorGenerator
    
    args = parse_args()
    quant_config = {
            "exp_width": 4,
            "man_width": 3,
            "exp_bias_width": 8,
            "block_size": [1, 4],
            "skip_first_dim": False,
        }
    rand_gen_high = RandomTensorGenerator(
        shape=(1, 8),
        directory=PROJECT_PATH / "test" / Path(args.path).parent.stem / "build",
        filename="test_projection_data.pt",
        quant_config=quant_config
    )
    
    # Expect shape, blocks.shape = (32, 4), bias.shape = (32, 1)
    rand_gen_high.tensor_gen()
    data = rand_gen_high.tensor_load()
    blocks, bias = rand_gen_high.quantize_tensor(data)
    
    hbm_element_file = PROJECT_PATH / "test" / Path(args.path).parent.stem / "build" / Path(args.path).stem / "hbm_ele.mem"
    hbm_scale_file = PROJECT_PATH / "test" / Path(args.path).parent.stem / "build" / Path(args.path).stem / "hbm_scale.mem"
    instr_file = PROJECT_PATH / "test" / Path(args.path).parent.stem / "build" / Path(args.path).stem / f"{Path(args.path).stem}.mem"

    os.environ["HBM_ELEMENT_FILE"] = str(hbm_element_file)
    os.environ["HBM_SCALE_FILE"] = str(hbm_scale_file)
    os.environ["INSTR_FILE"] = str(instr_file) 
    instruction_mapping_pipeline(blocks, bias, args.path, quant_config)

if __name__ == "__main__":
    init_mem()
    SimToP_test()


