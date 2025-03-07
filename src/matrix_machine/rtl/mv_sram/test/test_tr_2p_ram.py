import cocotb
from cocotb.triggers import Timer
from cocotb.clock import Clock

@cocotb.test()
async def my_first_test(dut):
    """Basic Cocotb test for my design."""
    
    # Start clock generation
    cocotb.start_soon(Clock(dut.clk, 2, units="ns").start())  # 2ns period (1GHz clock)

    # Apply Reset
    dut.rst.value = 1
    await Timer(5, units="ns")  # Hold reset for 5ns
    dut.rst.value = 0
    await Timer(5, units="ns")  # Allow some settling time

    # Apply test stimulus
    for cycle in range(1000):
        dut.sram_addr.value = 10
        dut.transpose_read.value = 0
        dut.stall.value = 0
        dut.read_en.value = 1
        await Timer(2, units="ns")  # Align with clock period
    
    # Log and check outputs
    # dut._log.info("sub_sram_addr_array = %s", dut.sub_sram_addr_array.value)
    # assert int(dut.my_signal_2.value) == 0, "ERROR: my_signal_2 is not 0!"
