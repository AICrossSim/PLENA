import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
import random


@cocotb.test()
async def mv_functional_test(dut):
    """Basic Cocotb test for my design."""
    
    # Start clock generation
    cocotb.start_soon(Clock(dut.clk, 2, units="ns").start())  # 2ns period (1GHz clock)

    await Timer(5, units="ns")

    # Write to sram
    for i in range(8):
        dut.req.value = 1
        dut.write_en.value = 1
        dut.addr.value = i
        dut.wdata.value = random.randint(0, 2**16-1)
        await RisingEdge(dut.clk)
    
    
    # Read from sram untransposed
    for i in range(2):
        dut.req.value = 1
        dut.write_en.value = 0
        dut.transposed_read.value = 0
        dut.addr.value = 0
        dut.parallel_rd_index.value = i
        await RisingEdge(dut.clk)

    # Read from sram transposed
    for i in range(2):
        dut.req.value = 1
        dut.write_en.value = 0
        dut.transposed_read.value = 1
        dut.addr.value = 0
        dut.parallel_rd_index.value = i
        await RisingEdge(dut.clk)

    # Keep simulation running to observe clock
    await Timer(10, units="ns")


