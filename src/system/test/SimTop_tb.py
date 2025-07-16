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
from cfl_cocotb.fp_generation import FpGenerator
from cfl_cocotb import SRC_PATH

# parser = argparse.ArgumentParser(description="Greet someone.")
# parser.add_argument("--benchmark", type=str, default="general")
# args = parser.parse_args()

import torch
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
        # cocotb.start_soon(self.check_signal())
        cocotb.start_soon(self.check_vector_sram())
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
        await Timer(5, units="us")

    async def check_signal(self):
        await Timer(40, units="ns")
        while True:
            await RisingEdge(self.dut.clk)
            if self.dut.instruction_ready.value:
                logger.info(f"Instruction ready: {self.dut.instruction.value}")


    async def check_vector_sram(self):
        def log_fp_data_with_handshake(valid, ready, data, exp_width, mant_width, log, name):
            if valid == 1 and ready == 1:
                _list = []
                self.log.debug(f"{name}: {data}")
                # Convert string of 128 values into 8 16-bit elements
                if (len(data) == 128):
                    for i in range(0, 128, 16):
                        chunk = data[i:i+15]
                        _list.append(chunk.integer)
                else:
                    raise ValueError(f"Data length is not 128 bits: {len(data)}")
                from cfl_cocotb.torch_fp_conversion import bin_2_fp
                torch_list = []
                for item in _list:
                    torch_fp = bin_2_fp(item, exp_width, mant_width)
                    torch_list.append(torch_fp)
                log.debug(f"Vector SRAM fp_out: {torch_list}")
                return torch_list
            else:
                return torch.tensor([])

        while True:
            await RisingEdge(self.dut.clk)
            vector_out_valid = self.dut.dut.vector_machine_init.v_out_valid.value
            vector_out_ready = self.dut.dut.vector_machine_init.v_out_ready.value
            vector_out_data = self.dut.dut.vector_machine_init.v_out.value

            vector_a_valid = self.dut.dut.vector_machine_init.v_a_valid.value
            vector_a_ready = self.dut.dut.vector_machine_init.v_a_ready.value
            vector_a_data = self.dut.dut.vector_machine_init.v_a_in.value

            vector_b_valid = self.dut.dut.vector_machine_init.v_b_valid.value
            vector_b_ready = self.dut.dut.vector_machine_init.v_b_ready.value
            vector_b_data = self.dut.dut.vector_machine_init.v_b_in.value

            from assembler.parser import load_isa_definitions
            isa_definitions = load_isa_definitions(str(SRC_PATH / "definitions" / "operation.svh"))
            # Create a reverse mapping of ISA definitions
            isa_definitions_reverse = {v: k for k, v in isa_definitions.items()}
            if self.dut.dut.instruction_valid.value == 1 and self.dut.dut.instruction_ready.value == 1:
                instruction = self.dut.dut.instruction.value[15-5:15]
                isa = isa_definitions_reverse[int(instruction)]
                self.log.debug(f"Instruction: {instruction} {isa}")
                

            element_v_control = self.dut.dut.vector_machine_init.element_v_control.value
            self.log.debug(f"element_v_control: {element_v_control}")
            
            # if self.dut.dut.v_sram_req_b.value == 1 and self.dut.dut.v_sram_wen_b.value == 1:
            #     self.log.debug(f"Vector SRAM write: {vector_out_data}")

            lut_list = log_fp_data_with_handshake(
                vector_out_valid, vector_out_ready, vector_out_data, 7, 8, self.log, "Vector Out")

            a_list = log_fp_data_with_handshake(
                vector_a_valid, vector_a_ready, vector_a_data, 7, 8, self.log, "Vector A")

            b_list = log_fp_data_with_handshake(
                vector_b_valid, vector_b_ready, vector_b_data, 7, 8, self.log, "Vector B")

@cocotb.test()
async def test(dut):
    tb = SimTOP(dut, os.environ["HBM_ELEMENT_FILE"], os.environ["HBM_SCALE_FILE"], os.environ["INSTR_FILE"])
    tb.log.setLevel(logging.DEBUG)
    await tb.run_test()


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
                "FAKE_HBM_SCALE_INIT_FILE": f"\"{os.environ['HBM_SCALE_FILE']}\"",
                "FP_MEM_INIT_FILE": f"\"{os.environ['FP_MEM_INIT_FILE']}\"",
                "FIXED_MEM_INIT_FILE": f"\"{os.environ['FIXED_MEM_INIT_FILE']}\"",
                "VECTOR_MEM_RESULT_FILE": f"\"{os.environ['VECTOR_MEM_RESULT_FILE']}\"",
                "HBM_ADDR_MAPPER_FILE": f"\"{os.environ['HBM_ADDR_MAPPER_FILE']}\"",
                "FAKE_HBM_ELEMENT_WRITE_M_FILE": f"\"{os.environ['FAKE_HBM_ELEMENT_WRITE_M_FILE']}\"",
                "FAKE_HBM_ELEMENT_WRITE_V_FILE": f"\"{os.environ['FAKE_HBM_ELEMENT_WRITE_V_FILE']}\"",
                "FAKE_HBM_SCALE_WRITE_M_FILE": f"\"{os.environ['FAKE_HBM_SCALE_WRITE_M_FILE']}\"",
                "FAKE_HBM_SCALE_WRITE_V_FILE": f"\"{os.environ['FAKE_HBM_SCALE_WRITE_V_FILE']}\""
            }
        ],
        trace = True,
        skip_build = False,
    )

def init_mem():
    global hbm_element_file, hbm_scale_file, instr_file
    
    from assembler.instruction_mapping_pipeline import instruction_mapping_pipeline, parse_args
    from cfl_tools import PROJECT_PATH
    from pathlib import Path
    from assembler.memory_mapping.rand_gen import RandomTensorGenerator
    from utils.load_config import load_svh_settings
    precision_settings = load_svh_settings(str(SRC_PATH / "definitions" / "precision.svh"))
    
    args = parse_args()
    data_config = {
        "tensor_size": [8, 8],
        "block_size": [1, 4],
    }

    quant_config = {
            "exp_width": precision_settings["ACT_MXFP_EXP_WIDTH"],
            "man_width": precision_settings["ACT_MXFP_MANT_WIDTH"],
            "exp_bias_width": precision_settings["MXFP_SCALE_WIDTH"],
            "block_size": data_config["block_size"],
            "skip_first_dim": False,
        }

    rand_gen_high = RandomTensorGenerator(
        shape=tuple(data_config["tensor_size"]),
        directory=PROJECT_PATH / "test" / Path(args.path).parent.stem / "build",
        filename="test_projection_data.pt",
        quant_config=quant_config
    )
    
    # Expect shape, blocks.shape = (32, 4), bias.shape = (32, 1)
    rand_gen_high.tensor_gen()
    data = rand_gen_high.tensor_load()
    blocks, bias = rand_gen_high.quantize_tensor(data)
    
    instruction_mapping_pipeline(blocks, bias, args.path, data_config, quant_config)
    build_path = PROJECT_PATH / "test" / Path(args.path).parent.stem / "build" / Path(args.path).stem
    hbm_element_file = build_path / "hbm_ele.mem"
    hbm_scale_file = build_path / "hbm_scale.mem"
    instr_file = build_path / f"{Path(args.path).stem}.mem"

    os.environ["HBM_ELEMENT_FILE"] = str(hbm_element_file)
    os.environ["HBM_SCALE_FILE"] = str(hbm_scale_file)
    os.environ["INSTR_FILE"] = str(instr_file) 

    hbm_write_element_m_file    = build_path / "hbm_write_m_ele.mem"
    hbm_write_element_v_file    = build_path / "hbm_write_v_ele.mem"
    hbm_write_scale_m_file      = build_path / "hbm_write_m_scale.mem"
    hbm_write_scale_v_file      = build_path / "hbm_write_v_scale.mem"
    vector_mem_result_file      = build_path / "vector_result.mem"
    # same 
    hbm_write_element_m_file.touch()
    hbm_write_element_v_file.touch()
    hbm_write_scale_m_file.touch()
    hbm_write_scale_v_file.touch()
    vector_mem_result_file.touch()

    fp_mem_file                 = build_path / "fp.mem"
    fixed_mem_file              = build_path / "fixed.mem"
    addr_mapper_file            = build_path / "hbm_addr_mapper.mem"

    fp_mem_file.touch()
    fixed_mem_file.touch()
    addr_mapper_file.touch()

    os.environ["FP_MEM_INIT_FILE"] = str(fp_mem_file)
    os.environ["FIXED_MEM_INIT_FILE"] = str(fixed_mem_file)
    os.environ["VECTOR_MEM_RESULT_FILE"] = str(vector_mem_result_file)
    os.environ["HBM_ADDR_MAPPER_FILE"] = str(addr_mapper_file)
    os.environ["FAKE_HBM_ELEMENT_WRITE_M_FILE"] = str(hbm_write_element_m_file)
    os.environ["FAKE_HBM_ELEMENT_WRITE_V_FILE"] = str(hbm_write_element_v_file)
    os.environ["FAKE_HBM_SCALE_WRITE_M_FILE"] = str(hbm_write_scale_m_file)
    os.environ["FAKE_HBM_SCALE_WRITE_V_FILE"] = str(hbm_write_scale_v_file)

if __name__ == "__main__":
    init_mem()
    SimToP_test()


