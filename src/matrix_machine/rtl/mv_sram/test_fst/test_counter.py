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
    for i in range(4):  # 2-bit counter, so it cycles 0-3
        await RisingEdge(dut.clk)
        assert dut.count.value == i, f"Counter mismatch at cycle {i}: {dut.count.value}"

    # Ensure simulation runs long enough to dump waveforms
    await Timer(100, units="ns")

    # Explicitly finish to trigger trace file generation
    os.system("pkill -SIGINT verilator")

    cocotb.log.info("Counter test passed. Verilator should generate dump.fst or dump.vcd")
