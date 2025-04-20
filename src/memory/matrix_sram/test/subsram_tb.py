
import logging
import pytest
import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
import random

from cfl_cocotb import veri_runner, packed_array_analyser

logger = logging.getLogger("testbench")
logger.setLevel(logging.INFO)


DataWidth = 8
SRAM_DEPTH = 128
SubSRAMIndex = 0
MLEN = 8
Parallel_Wr_Dim = 4
Parallel_Rd_Dim = 2

@cocotb.test()
async def mv_functional_test(dut):
    """Basic Cocotb test for my design."""
    
    # Start clock generation
    cocotb.start_soon(Clock(dut.clk, 2, units="ns").start())  # 2ns period (1GHz clock)

    await Timer(5, units="ns")

    # Write to sram
    for i in range(MLEN // Parallel_Wr_Dim):
        dut.req.value = 1
        dut.write_en.value = 1
        dut.addr.value = (Parallel_Wr_Dim // Parallel_Rd_Dim) * i
        dut.wdata.value = random.randint(0, 2**(DataWidth * Parallel_Rd_Dim * Parallel_Wr_Dim)-1)
        await RisingEdge(dut.clk)
        cocotb.log.info(f"Write Addr: {dut.addr.value}")
        cocotb.log.info(f"Write data: {dut.wdata.value}")
    
    
    # Read from sram untransposed
    cocotb.log.info("Read from sram untransposed")
    for i in range(MLEN // Parallel_Rd_Dim):
        dut.req.value = 1
        dut.write_en.value = 0
        dut.transposed_read.value = 0
        dut.addr.value = i
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        cocotb.log.info(f"Raw Read data: {dut.raw_rdata.value}")
        # cocotb.log.info(f"Read data: {dut.smst.out_data.value}")
        cocotb.log.info(f"Read data: {dut.rdata.value}")

    # Read from sram transposed
    cocotb.log.info("Read from sram transposed")
    for i in range(2):
        dut.req.value = 1
        dut.write_en.value = 0
        dut.transposed_read.value = 1
        dut.addr.value = i
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        cocotb.log.info(f"sram_index : {dut.sram_index.value}")
        cocotb.log.info(f"addr_offset: {dut.addr_offset.value}")
        cocotb.log.info(f"transposed addr: {dut.addr_for_sub_sram.value}")
        cocotb.log.info(f"Raw Read data: {dut.raw_rdata.value}")
        # cocotb.log.info(f"Read data: {dut.smst.out_data.value}")
        cocotb.log.info(f"Read data: {dut.rdata.value}")

    # Keep simulation running to observe clock
    await Timer(10, units="ns")




@pytest.mark.dev
def test_simple_subsram():
    # Run tests with different params
    veri_runner(
        group = "mv_sram",
        module = "subsram",
        module_param_list=[
            {"DataWidth": DataWidth, "SRAM_DEPTH": SRAM_DEPTH, "MLEN": MLEN, "SubSRAMIndex": SubSRAMIndex, "Parallel_Wr_Amount": Parallel_Wr_Dim, "PARALLEL_DIM": Parallel_Rd_Dim},
        ],
        trace = False,
    )


if __name__ == "__main__":
    test_simple_subsram()
