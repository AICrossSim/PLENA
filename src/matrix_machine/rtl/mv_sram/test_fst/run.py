import cocotb
from cocotb.runner import get_runner
import os



def run_cocotb():
    os.environ["WAVES"] = "1"
    runner = get_runner("verilator")  # Use Verilator
    runner.build(
        verilog_sources=["simple_counter.sv"],  # RTL file
        build_dir="build",
        always=True,  # Force rebuild every time
        build_args=["--trace", "--trace-fst", "--trace-structs", "-DVM_TRACE_FST"],  # Enable tracing
        hdl_toplevel="simple_counter",  # Match the module name
    )

    runner.test(
        # python_search=["."],  # Testbench directory
        test_module="test_simple_counter",  # Name of the testbench file
        hdl_toplevel="simple_counter",
        waves=True,  # Enable waveform dumping
        # extra_args="--trace --trace-structs"
    )

if __name__ == "__main__":
    run_cocotb()
