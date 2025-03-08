import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock
import random


@cocotb.test()
async def mv_functional_test(dut):
    """Basic Cocotb test for my design."""
    
    # Start clock generation

    await Timer(5, units="ns")

    # Write to sram
    for i in range(4):
        dut.in_data.value = random.randint(0, 2**16-1)
        dut.transposed_read.value = 0
        await Timer(2, units="ns")

    for i in range(4):
        dut.in_data.value = random.randint(0, 2**16-1)
        dut.transposed_read.value = 1
        await Timer(2, units="ns")

    # Keep simulation running to observe clock
    await Timer(1, units="ns")


