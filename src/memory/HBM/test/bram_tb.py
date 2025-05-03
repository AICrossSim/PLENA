#!/usr/bin/env python3

import logging
import pytest
import cocotb
import sys
import os
from pathlib import Path
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
from cfl_cocotb import veri_runner, MXBlockFPConverter
from math import ceil, log2
import math


@cocotb.test()
async def test_bram_basic(dut):
    # Start clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Helper to apply inputs
    async def write(addr, data, mask):
        dut.bram_en_o.value = 1
        dut.bram_we_o.value = 1
        dut.bram_addr_o.value = addr
        dut.bram_wdata_o.value = data
        dut.bram_wmask_o.value = mask
        await RisingEdge(dut.clk)
        dut.bram_en_o.value = 0
        dut.bram_wmask_o.value = 0
        await RisingEdge(dut.clk)

    async def read(addr):
        dut.bram_en_o.value = 1
        dut.bram_we_o.value = 0
        dut.bram_addr_o.value = addr
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        print(f"bram_rdata_i: {dut.bram_rdata_i.value}")
        data = dut.bram_rdata_i.value.integer
        dut.bram_en_o.value = 0
        await RisingEdge(dut.clk)
        return data

    # Wait a couple cycles
    dut.bram_en_o.value = 0
    dut.bram_we_o.value = 0

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    # Test read from initial file
    read_val = await read(0)
    cocotb.log.info(f"Read value at address 0x0: 0x{read_val:08x}")

    # Write and read back
    # await write(4, 0x123456789abcdef0, 0xFF)
    val = await read(1)
    print(f"Read value at address 0x4: 0x{val:08x}")
    # assert val == 0x123456789abcdef0, f"Read {val:#x}, expected 0x123456789abcdef0"

    await write(1, 0x12345678, 0xF)


    val = await read(1)
    print(f"Read value at address 0x4: 0x{val:08x}")


@pytest.mark.dev
def bram_test():
    # Run tests with different params
    veri_runner(
        group = "HBM",
        module = "bram",
        additional_include_paths = [
        ],       
        workload_path = "/home/george/Coprocessor_for_Llama/src/memory/HBM/test/simple_benchmark.mem",
        module_param_list=[
            {"DATA_WIDTH": 32, "ADDR_WIDTH": 8,  "INIT_FILE": "\"/home/george/Coprocessor_for_Llama/src/memory/HBM/test/simple_benchmark.mem\""},
        ],
        trace = True,
    )

if __name__ == "__main__":
    bram_test()

