#!/usr/bin/env python3

# This script tests the fixed point linear
import os, logging
import sys
import torch
import pytest
import cocotb
from pathlib import Path
from functools import partial
from cocotb.log import SimLog
from cocotb.triggers import *
from cocotb.triggers import Timer, RisingEdge
from cfl_cocotb.runner import veri_runner, SRC_PATH
from cfl_cocotb.testbench import Testbench
from cfl_cocotb.streaming import (
    StreamDriver,
    StreamMonitor,
)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cfl_cocotb.runner import veri_runner
from cfl_cocotb import SRC_PATH
from cfl_cocotb.torch_fp_conversion import bin_2_fp

from memory_mapping.rand_gen import RandomTensorGenerator
from utils.load_config import load_svh_settings
from quant.quantizer.hardware_quantizer.mxfp import _mx_fp_quantize_hardware
from quant.quantizer.hardware_quantizer import _minifloat_ieee_quantize_hardware

from cfl_tools.logger import get_logger
from cfl_tools.debugger import set_excepthook
from cfl_tools import PROJECT_PATH

from sys_utils.build_sys_tools import (
    generate_golden_result,
    env_setup,
    init_mem
)

logger = get_logger("testbench")
logger.setLevel(logging.DEBUG)
current_path = Path(__file__).resolve().parent

testcase_name = "matrix"
INSTRUCTION_LENGTH = 32
set_excepthook()

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
                "exp_bias_width": precision_settings["MX_SCALE_WIDTH"],
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
            exponent_bias_width=precision_settings["MX_SCALE_WIDTH"],
            block_size=data_config["block_size"])
        qele = pbmant * 2**pbexp

        self.qdata, _, _ = _minifloat_ieee_quantize_hardware(
            qdata, 
            width=precision_settings["V_FP_EXP_WIDTH"] + precision_settings["V_FP_MANT_WIDTH"] + 1, 
            exponent_width=precision_settings["V_FP_EXP_WIDTH"])

        blocks, bias = rand_gen_high.quantize_tensor(data)
        generate_golden_result(data, logger, precision_settings, data_config)
        env_setup(blocks, bias, asm_file, data_config, quant_config)
        
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
            str(SRC_PATH / "basic_components/synopsis/rtl"),
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
            str(SRC_PATH / "core"),
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



if __name__ == "__main__":
    init_mem()
    #init_vector_sram()
    #init_vector_hbm_for_test()
    
    SimToP_test()


