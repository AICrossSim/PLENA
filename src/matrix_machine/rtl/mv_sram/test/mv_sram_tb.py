#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os

from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock

# # Absolute path to your package directory
# cocotb_tool_path = "/home/george/Coprocessor_for_Llama/tools/cfl_cocotb"

# # Ensure the path exists and is not already in sys.path
# if os.path.exists(cocotb_tool_path) and cocotb_tool_path not in sys.path:
#     sys.path.append(cocotb_tool_path)

# print("Updated sys.path:", sys.path)

from cfl_cocotb.runner import veri_runner


logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)

@cocotb.test()
async def mv_sram_functional_test(dut):
    """Basic Cocotb test for my design."""
    
    # Start clock generation
    cocotb.start_soon(Clock(dut.clk, 2, units="ns").start())  # 2ns period (1GHz clock)
    await Timer(5, units="ns")

    # Write to sram
    for i in range(8):
        dut.req.value = 1
        dut.write_en.value = 1
        dut.addr.value = i
        dut.wdata.value = sum(((i + j) << (j * 8)) for j in range(8))  # Concatenate 8-bit values
        await RisingEdge(dut.clk)

    # Keep simulation running to observe clock
    await Timer(10, units="ns")

@pytest.mark.dev
def test_simple_mvsram():
    # Run tests with different params
    veri_runner(
        group = "mv_sram",
        module = "mv_sram",
        module_param_list=[
            {"DataWidth": 8, "SRAM_Depth": 128, "MLEN": 8, "Parallel_Wr_Dim": 2, "Parallel_Rd_Dim": 2},
        ],
        trace = True,
    )


if __name__ == "__main__":
    test_simple_mvsram()
