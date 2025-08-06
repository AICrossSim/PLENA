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

from assembler.instruction_mapping_pipeline import instruction_mapping_pipeline, parse_args
from cfl_tools import PROJECT_PATH
from pathlib import Path
from assembler.memory_mapping.rand_gen import RandomTensorGenerator
from utils.load_config import load_svh_settings
from quant.quantizer.hardware_quantizer.mxfp import _mx_fp_quantize_hardware
from quant.quantizer.hardware_quantizer.minifloat import _minifloat_ieee_quantize_hardware
from cfl_cocotb.torch_fp_conversion import bin_2_fp

import torch
from cfl_tools.logger import get_logger
from cfl_tools.debugger import set_excepthook
logger = get_logger("testbench")
logger.setLevel(logging.DEBUG)
current_path = Path(__file__).resolve().parent

testcase_name = "matrix"
INSTRUCTION_LENGTH = 16
set_excepthook()

from cfl_cocotb.torch_fp_conversion import pack_fp_to_bin, fp_2_bin

def generate_golden_result(data, precision_settings, data_config):
    qdata, pbexp, pbmant, pbbias = _mx_fp_quantize_hardware(
        data, 
        width=precision_settings["ACT_MXFP_EXP_WIDTH"] + precision_settings["ACT_MXFP_MANT_WIDTH"] + 1, 
        exponent_width=precision_settings["ACT_MXFP_EXP_WIDTH"], 
        exponent_bias_width=precision_settings["MXFP_SCALE_WIDTH"],
        block_size=data_config["block_size"])
    qele = pbmant * 2**pbexp
    logger.debug("---- mxfp_input ----")
    logger.debug(f"data: {data}")
    logger.debug(f"pbexp: {pbexp}")
    logger.debug(f"pbmant: {pbmant}")
    logger.debug(f"qele: {qele}")
    bin_ele = pack_fp_to_bin(pbexp, pbmant, precision_settings["ACT_MXFP_EXP_WIDTH"], precision_settings["ACT_MXFP_MANT_WIDTH"])
    bin_bias = pbbias
    logger.debug(f"-- hardware bin --")
    logger.debug(f"bin_ele: {bin_ele}")
    logger.debug(f"bin_bias: {bin_bias}")


    logger.debug("---- fp_input ----")
    qdata_fp, bin_fp = fp_2_bin(qdata, precision_settings["V_FP_EXP_WIDTH"], precision_settings["V_FP_MANT_WIDTH"])
    logger.debug(f"qdata_fp: {qdata_fp}")
    logger.debug(f"--hardware bin--")
    logger.debug(f"bin_fp: {bin_fp}")

    logger.debug("---- exp_out ----")
    exp_fp = torch.exp(qdata_fp)
    qexp_fp, bin_exp_fp = fp_2_bin(exp_fp, precision_settings["V_FP_EXP_WIDTH"], precision_settings["V_FP_MANT_WIDTH"])
    logger.debug(f"exp_fp: {qexp_fp}")
    logger.debug(f"--hardware bin--")
    logger.debug(f"bin_exp_fp: {bin_exp_fp}")

    logger.debug("---- 1 + exp(x) ----")
    q1_exp_fp, bin_1_exp_fp = fp_2_bin(1 + qexp_fp, precision_settings["V_FP_EXP_WIDTH"], precision_settings["V_FP_MANT_WIDTH"])
    logger.debug(f"1_exp_fp: {q1_exp_fp}")
    logger.debug(f"--hardware bin--")
    logger.debug(f"bin_1_exp_fp: {bin_1_exp_fp}")
    

    return qdata

    


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
        torch.manual_seed(52)
        precision_settings = load_svh_settings(str(SRC_PATH / "definitions" / "precision.svh"))
        asm_file_name = os.environ["ASM_FILE"]
        asm_file = Path(PROJECT_PATH / "test" / "Instr_Level_Benchmark" / f"{asm_file_name}.asm")
        data_config = {
            "tensor_size": [1, 8],
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
            directory=PROJECT_PATH / "test" / Path(asm_file).parent.stem / "build",
            filename="test_projection_data.pt",
            quant_config=quant_config
        )
        
        # Expect shape, blocks.shape = (32, 4), bias.shape = (32, 1)
        rand_gen_high.tensor_gen()
        data = rand_gen_high.tensor_load()
        qdata, pbexp, pbmant, _ = _mx_fp_quantize_hardware(
            data, 
            width=precision_settings["ACT_MXFP_EXP_WIDTH"] + precision_settings["ACT_MXFP_MANT_WIDTH"] + 1, 
            exponent_width=precision_settings["ACT_MXFP_EXP_WIDTH"], 
            exponent_bias_width=precision_settings["MXFP_SCALE_WIDTH"],
            block_size=data_config["block_size"])
        qele = pbmant * 2**pbexp

        self.qdata, _, _ = _minifloat_ieee_quantize_hardware(
            qdata, 
            width=precision_settings["V_FP_EXP_WIDTH"] + precision_settings["V_FP_MANT_WIDTH"] + 1, 
            exponent_width=precision_settings["V_FP_EXP_WIDTH"])
        print(f"input ref data: {data}")
        blocks, bias = rand_gen_high.quantize_tensor(data)

        generate_golden_result(data, precision_settings, data_config)

        instruction_mapping_pipeline(
            blocks, bias, asm_file, data_config, quant_config)
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
        def log_fp_data_with_handshake(data, exp_width, mant_width):
            _list = []
            # Convert string of 128 values into 8 16-bit elements
            for i in range(0, len(data), exp_width + mant_width+1):
                chunk = data[i:i+exp_width + mant_width]
                _list.append(chunk.integer)
            torch_list = []
            for item in _list:
                torch_fp = bin_2_fp(item, exp_width, mant_width)
                torch_list.append(torch_fp)
            return torch_list
        
        while True:
            await RisingEdge(self.dut.clk)
            if self.dut.dut.vector_machine_init.element_v_out_valid.value == 1 and self.dut.dut.vector_machine_init.element_v_out_ready.value == 1:
                data = self.dut.dut.vector_machine_init.element_v_out.value
                list_ = []
                for i in range(0, len(data), 16):
                    list_.append(data[i:i+15].integer)
                self.log.debug(f"Vector Core fp_out: {list_}")


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
            str(SRC_PATH / "basic_components/systolic_gemm_mx"),
            str(SRC_PATH / "basic_components/gemv"),
            str(SRC_PATH / "basic_components/synopsis"),
            str(SRC_PATH / "basic_components/synopsis_ip_inst"),
            str(SRC_PATH / "basic_components/hadamard_transform"),
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
            {
                "INSTRUCTION_LENGTH": INSTRUCTION_LENGTH,
                "FAKE_HBM_ELEMENT_INIT_FILE": f"\"{os.environ['HBM_ELEMENT_FILE']}\"",
                "FAKE_HBM_SCALE_INIT_FILE": f"\"{os.environ['HBM_SCALE_FILE']}\"",
                "FP_MEM_INIT_FILE": f"\"{os.environ['FP_MEM_INIT_FILE']}\"",
                "INT_MEM_INIT_FILE": f"\"{os.environ['INT_MEM_INIT_FILE']}\"",
                "VECTOR_MEM_RESULT_FILE": f"\"{os.environ['VECTOR_MEM_RESULT_FILE']}\"",
                "HBM_ADDR_MAPPER_FILE": f"\"{os.environ['HBM_ADDR_MAPPER_FILE']}\"",
                "FAKE_HBM_ELEMENT_WRITE_M_FILE": f"\"{os.environ['FAKE_HBM_ELEMENT_WRITE_M_FILE']}\"",
                "FAKE_HBM_ELEMENT_WRITE_V_FILE": f"\"{os.environ['FAKE_HBM_ELEMENT_WRITE_V_FILE']}\"",
                "FAKE_HBM_SCALE_WRITE_M_FILE": f"\"{os.environ['FAKE_HBM_SCALE_WRITE_M_FILE']}\"",
                "FAKE_HBM_SCALE_WRITE_V_FILE": f"\"{os.environ['FAKE_HBM_SCALE_WRITE_V_FILE']}\""
            }
        ],
        trace = True,
        skip_build = False
    )

def init_mem():
    args = parse_args()
    asm_file = Path(args.path).stem

    build_path = PROJECT_PATH / "test" / Path(args.path).parent.stem / "build" / Path(args.path).stem
    build_path.mkdir(parents=True, exist_ok=True)
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
    with open(fp_mem_file, "w") as f:
        f.write("3F00\n")
    fixed_mem_file.touch()
    addr_mapper_file.touch()

    os.environ["FP_MEM_INIT_FILE"] = str(fp_mem_file)
    os.environ["INT_MEM_INIT_FILE"] = str(fixed_mem_file)
    os.environ["VECTOR_MEM_RESULT_FILE"] = str(vector_mem_result_file)
    os.environ["HBM_ADDR_MAPPER_FILE"] = str(addr_mapper_file)
    os.environ["FAKE_HBM_ELEMENT_WRITE_M_FILE"] = str(hbm_write_element_m_file)
    os.environ["FAKE_HBM_ELEMENT_WRITE_V_FILE"] = str(hbm_write_element_v_file)
    os.environ["FAKE_HBM_SCALE_WRITE_M_FILE"] = str(hbm_write_scale_m_file)
    os.environ["FAKE_HBM_SCALE_WRITE_V_FILE"] = str(hbm_write_scale_v_file)
    os.environ["ASM_FILE"] = str(asm_file)

if __name__ == "__main__":
    init_mem()
    
    SimToP_test()


