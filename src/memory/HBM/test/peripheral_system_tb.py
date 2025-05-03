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
async def test_peripheral_basic(dut):
    # Start clock
    cocotb.start_soon(Clock(dut.clk, 5, units="ns").start())
    print("Read test...")
    dut.fetch_en.value      = 1
    dut.fetch_addr.value    = 0
    dut.write_en.value      = 0
    await Timer(20, units="ns")
    print(f"DUT fetch data: {dut.fetch_data.value}")


    print("monitor tl_master")
    print(f"-<host_d_ready: {dut.tl_master_init.host_d_ready.value}")
    print(f"-<host_a_ready: {dut.tl_master_init.host_a_ready.value}")
    print(f"-<tl_state: {dut.tl_master_init.state.value}")

    print("Write test...")
    dut.fetch_en.value      = 1
    dut.write_en.value      = 1
    dut.fetch_addr.value    = 0
    dut.write_data.value    = 0x8765

    await Timer(20, units="ns")

    print("monitor tl_master")
    print(f"tl_state: {dut.tl_master_init.state.value}")
    print(f"next_opcode: {dut.tl_master_init.next_a_opcode.value}")

    print("monitor fake bram signal")
    print(f"host_link_a_valid: {dut.fake_hbm.host_link_a_valid.value}")
    print(f"host_link_a: {dut.fake_hbm.host_link_a.value}")


    print(f"bram_wdata_o:   {dut.fake_hbm.bram_wdata.value}")
    print(f"bram_addr_o:    {dut.fake_hbm.bram_addr.value}")
    print(f"bram_en_o:      {dut.fake_hbm.bram_en.value}")
    print(f"bram_we_o:      {dut.fake_hbm.bram_we.value}")
    print(f"bram_wmask:     {dut.fake_hbm.bram_wmask.value}")
    
    
    print("Confirm test...")
    dut.fetch_en.value      = 1
    dut.fetch_addr.value    = 0
    dut.write_en.value      = 0
    await Timer(10, units="ns")
    print("monitor tl_master")
    print(f"tl_state: {dut.tl_master_init.state.value}")
    print(f"next_opcode: {dut.tl_master_init.next_a_opcode.value}")

    await Timer(10, units="ns")
    print(f"bram_addr_o:    {dut.fake_hbm.bram_addr.value}")
    print(f"bram_en_o:      {dut.fake_hbm.bram_en.value}")
    print(f"bram_we_o:      {dut.fake_hbm.bram_we.value}")
    print(f"bram_rdata:     {dut.fake_hbm.bram_rdata.value}")
    await Timer(10, units="ns")
    print(f"DUT fetch data: {dut.fetch_data.value}")



@pytest.mark.dev
def bram_test():
    # Run tests with different params
    veri_runner(
        group = "HBM",
        module = "peripheral_system",
        additional_include_paths = [
        ],       
        workload_path = "/home/george/Coprocessor_for_Llama/src/memory/HBM/test/simple_benchmark.txt",
        module_param_list=[
            {"DATA_WIDTH": 16, "ADDR_WIDTH": 32, "BRAM_ADDR_WIDTH": 16, "INIT_FILE": "\"/home/george/Coprocessor_for_Llama/src/memory/HBM/test/simple_benchmark.mem\""},
        ],
        definitions_path = "../../../../src/memory/HBM/TileLink_Lib",
        trace = True,
    )

if __name__ == "__main__":
    bram_test()

