import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock

@cocotb.test()
async def my_first_test(dut):
    """Basic Cocotb test for my design."""
    
    # Start clock generation
    cocotb.start_soon(Clock(dut.clk, 2, units="ns").start())  # 2ns period (1GHz clock)

    # Apply Reset
    dut.rst.value = 0
    await Timer(5, units="ns")  # Hold reset for 5ns
    dut.rst.value = 1
    await Timer(5, units="ns")  # Allow some settling time

    # Apply test stimulus
    for cycle in range(100):
        dut.sram_addr.value = 10
        dut.transpose_read.value = 0
        dut.stall.value = 0
        dut.read_en.value = 1
        await RisingEdge(dut.clk)  # Synchronize with clock edges
    
    for cycle in range(100):
        dut.sram_addr.value = 10
        dut.transpose_read.value = 1
        dut.stall.value = 0
        dut.read_en.value = 1
        await RisingEdge(dut.clk)  # Synchronize with clock edges

    # Keep simulation running to observe clock
    await Timer(500, units="ns")


