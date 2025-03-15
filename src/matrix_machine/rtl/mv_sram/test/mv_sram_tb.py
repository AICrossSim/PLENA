#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os

from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock

# # Absolute path to your package directory
# cocotb_tool_path = "/home/george/Documents/Cambridge/Coprocessor_for_Llama/tools/cfl_cocotb"

# # Ensure the path exists and is not already in sys.path
# if os.path.exists(cocotb_tool_path) and cocotb_tool_path not in sys.path:
#     sys.path.append(cocotb_tool_path)

# print("Updated sys.path:", sys.path)

from cfl_cocotb import veri_runner

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)

# Parameters Definition
# ---------------------
DataWidth = 8
SRAM_Depth = 128
MLEN = 8
Parallel_Wr_Dim = 4
Parallel_Rd_Dim = 2

def print_verilog_output(out_data):
    for i, data in enumerate(out_data):
        print(f"out_data[{i}] = {data}")  # Pri


@cocotb.test()
async def mv_sram_functional_test(dut):
    """Basic Cocotb test for my design."""
    
    # Start clock generation
    cocotb.start_soon(Clock(dut.clk, 2, units="ns").start())  # 2ns period (1GHz clock)
    await Timer(5, units="ns")

    cocotb.log.info("Starting SRAM test")

    # Write to sram
    for i in range(2):
        dut.req.value = 1
        dut.write_en.value = 1
        dut.sram_addr.value = i
        dut.write_data.value = sum(((i + j) << (j * DataWidth)) for j in range(MLEN * Parallel_Wr_Dim))  # Concatenate 8-bit values
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        # cocotb.log.info(f"Write Addr: {dut.sram_addr.value}")
        # cocotb.log.info(f"Write Data: {dut.sub_sram[1].sub_sram_1.wdata.value}")
    
    # Read from sram
    dut.req.value = 1
    dut.write_en.value = 0
    dut.sram_addr.value = 0
    dut.transposed_read = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    # cocotb.log.info(f"Read from SRAM: {dut.sub_sram[1].sub_sram_1.rdata.value}")
    
    # # Transposed Read from sram
    # dut.req.value = 1
    # dut.write_en.value = 0
    # dut.sram_addr.value = 0
    # dut.transposed_read = 1
    # await RisingEdge(dut.clk)
    # await RisingEdge(dut.clk)


    # Keep simulation running to observe clock
    await Timer(10, units="ns")

@pytest.mark.dev
def test_simple_mvsram():
    # Run tests with different params
    veri_runner(
        group = "mv_sram",
        module = "mv_sram",
        module_param_list=[
            {"DataWidth": DataWidth, "SRAM_Depth": SRAM_Depth, "MLEN": MLEN, "Parallel_Wr_Dim": Parallel_Wr_Dim, "Parallel_Rd_Dim": Parallel_Rd_Dim},
        ],
        trace = False,
    )


if __name__ == "__main__":
    test_simple_mvsram()
