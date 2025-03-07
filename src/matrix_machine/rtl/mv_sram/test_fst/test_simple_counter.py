import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import os

@cocotb.test()
async def counter_test(dut):
    """Test the simple 2-bit counter"""

    # Start a clock with 10ns period
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset the counter
    dut.rst_n.value = 0
    dut.en.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1  # Release reset

    # Enable counter and check counting
    dut.en.value = 1
    for i in range(4):  # 2-bit counter, so count 0,1,2,3, then wraps to 0
        await RisingEdge(dut.clk)
        assert dut.count.value == i, f"Counter mismatch at cycle {i}: {dut.count.value}"

    # Let simulation run longer to ensure tracing
    await Timer(500, units="ns")

    # Explicitly stop Verilator (forces it to flush waveforms)
    os.system("pkill -SIGINT verilator")

    cocotb.log.info("Counter test completed, Verilator should have written dump.fst")
