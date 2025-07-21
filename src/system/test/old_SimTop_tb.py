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
from cfl_cocotb.fp_generation import FpGenerator

# parser = argparse.ArgumentParser(description="Greet someone.")
# parser.add_argument("--benchmark", type=str, default="general")
# args = parser.parse_args()

logger = logging.getLogger("testbench")
logger.setLevel(logging.DEBUG)
current_path = Path(__file__).resolve().parent

testcase_name       = "vect_fp"
# instr_file          = f"{current_path.parent.parent.parent}/test/Layerwise_Benchmark/{testcase_name}.mem"
instr_file                  = f"{current_path.parent.parent.parent}/test/Instr_Level_Benchmark/{testcase_name}.mem"
hbm_element_file            = f"{current_path.parent.parent.parent}/test/load_mem/hbm_ele.mem"
hbm_scale_file              = f"{current_path.parent.parent.parent}/test/load_mem/hbm_scale.mem"
hbm_write_element_m_file    = f"{current_path.parent.parent.parent}/test/result_mem/hbm_write_m_ele.mem"
hbm_write_element_v_file    = f"{current_path.parent.parent.parent}/test/result_mem/hbm_write_v_ele.mem"
hbm_write_scale_m_file      = f"{current_path.parent.parent.parent}/test/result_mem/hbm_write_m_scale.mem"
hbm_write_scale_v_file      = f"{current_path.parent.parent.parent}/test/result_mem/hbm_write_v_scale.mem"
vector_mem_result_file      = f"{current_path.parent.parent.parent}/test/result_mem/vector_result.mem"
fp_mem_file                 = f"{current_path.parent.parent.parent}/test/load_mem/fp.mem"
fixed_mem_file              = f"{current_path.parent.parent.parent}/test/load_mem/fixed.mem"
addr_mapper_file            = f"{current_path.parent.parent.parent}/test/load_mem/hbm_addr_mapper.mem"

INSTRUCTION_LENGTH = 16
fp_exp = 7
fp_mant = 8
mlen = 8
fp_gen = FpGenerator(fp_exp, fp_mant)

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
        breakpoint()
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
    # cocotb.start_soon(record_data_on_trigger(dut=dut.dut.matrix_machine_init.matrix_compute_unit, clk=dut.clk, trigger_signal=dut.dut.matrix_machine_init.matrix_compute_unit.v1_in_valid, output_file=f"{current_path}/log/recorded_data.txt"))
    # cocotb.start_soon()
    tb = SimTOP(dut, hbm_element_file, hbm_scale_file, instr_file)
    await tb.run_test()


@cocotb.coroutine
async def record_data_on_trigger(dut, clk, trigger_signal, num_cycles=10, output_file="recorded_data.txt"):
    await RisingEdge(trigger_signal)
    dut._log.info("Trigger detected. Recording begins.")

    with open(output_file, "w") as f:
        for cycle in range(num_cycles):
            await RisingEdge(clk)

            if dut.v1_in_valid.value:
                # for i, v in enumerate(dut.v1_data.value):
                f.write(f"V1:  {hex(dut.v1_data.value)}\n")
                converted_v1_data = fp_gen.translate_packed_array_fp(mlen, fp_exp, fp_mant, dut.v1_data.value)
                f.write(f"V1 Cycle {cycle} - \n")
                f.write(f"[")
                for i, v in enumerate(reversed(converted_v1_data)):
                    f.write(f"{v}, ")
                f.write(f"]\n")

            if dut.v2_in_valid.value:
                # for i, v in enumerate(dut.v2_data.value):
                f.write(f"V2:  {hex(dut.v2_data.value)}\n")
                converted_v2_data = fp_gen.translate_packed_array_fp(mlen, fp_exp, fp_mant, dut.v2_data.value)
                f.write(f"V2 Cycle {cycle} - \n")
                f.write(f"[")
                for i, v in enumerate(reversed(converted_v2_data)):
                    f.write(f"{v}, ")
                f.write(f"]\n")

    dut._log.info(f"Recording complete. Data saved to {output_file}")

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
            "../../../src/basic_components/gemv",
            "../../../src/basic_components/fixed_operation",
            "../../../src/basic_components/systolic_gemm_mxfp",
            "../../../src/basic_components/systolic_gemm_fp",
            "../../../src/basic_components/int_operation",
            "../../../src/basic_components/cast",
            "../../../src/frontend",
            "../../../src/control",
            "../../../src/matrix_machine",
            "../../../src/vector_machine",
            "../../../src/scalar_machine",
            "../../../src/memory/matrix_sram",
            "../../../src/memory/vector_sram",
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
                "FIXED_MEM_INIT_FILE": f"\"{fixed_mem_file}\"",
                "VECTOR_MEM_RESULT_FILE": f"\"{vector_mem_result_file}\"",
                "HBM_ADDR_MAPPER_FILE": f"\"{addr_mapper_file}\"",
                "FAKE_HBM_ELEMENT_WRITE_M_FILE": f"\"{hbm_write_element_m_file}\"",
                "FAKE_HBM_ELEMENT_WRITE_V_FILE": f"\"{hbm_write_element_v_file}\"",
                "FAKE_HBM_SCALE_WRITE_M_FILE": f"\"{hbm_write_scale_m_file}\"",
                "FAKE_HBM_SCALE_WRITE_V_FILE": f"\"{hbm_write_scale_v_file}\""
            }
        ],
        trace = True,
    )


if __name__ == "__main__":
    SimToP_test()


