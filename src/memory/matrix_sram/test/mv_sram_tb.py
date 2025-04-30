#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os

from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock

from cfl_cocotb import veri_runner, packed_array_analyser

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)

# Parameters Definition
# ---------------------
DataWidth = 8
SRAM_DEPTH = 128
MLEN = 8
Parallel_Wr_Dim = 2
Parallel_Rd_Dim = 2

@cocotb.test()
async def mv_sram_functional_test(dut):
    """Basic Cocotb test for my design."""
    
    array_analyser = packed_array_analyser(DataWidth, MLEN, Parallel_Wr_Dim, Parallel_Rd_Dim)

    # Start clock generation
    cocotb.start_soon(Clock(dut.clk, 2, units="ns").start())  # 2ns period (1GHz clock)
    await Timer(5, units="ns")

    cocotb.log.info("Starting SRAM test")

    # Write to sram
    for i in range(MLEN // Parallel_Wr_Dim):
        dut.req.value = 1
        dut.write_en.value = 1
        dut.sram_addr.value = (Parallel_Wr_Dim // Parallel_Rd_Dim) * i
        dut.write_data.value = sum(((i * MLEN * Parallel_Wr_Dim + j) << (j * DataWidth)) for j in range(MLEN * Parallel_Wr_Dim))  # Concatenate 8-bit values
        
        # raise Exception("Stop")
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        array_analyser.print_wdata_from_hbm(f"{dut.write_data.value}")
        cocotb.log.info(f"Write Addr: {dut.sram_addr.value}")
        array_analyser.print_write_data_to_sram(f"{dut.sub_sram_wdata.value}", [0])
    
    # Read from sram
    dut.req.value = 1
    dut.write_en.value = 0
    dut.sram_addr.value = 0
    dut.transposed_read.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    # cocotb.log.info(f"Read Addr: {dut.sub_sram[0].sub_sram_1.raw_rdata.value}")
    array_analyser.print_read_data_from_sram(f"{dut.sub_sram_rdata.value}", [3])
    print(dut.rdata_transform_1.in_data.value)
    await RisingEdge(dut.clk)
    print(dut.out_data.value)
    array_analyser.print_rdata_from_overall_sram(f"{dut.out_data.value}")
    

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
            {"DataWidth": DataWidth, "SRAM_DEPTH": SRAM_DEPTH, "MLEN": MLEN, "Parallel_Rd_Dim": Parallel_Rd_Dim},
        ],
        trace = False,
    )


if __name__ == "__main__":
    test_simple_mvsram()
