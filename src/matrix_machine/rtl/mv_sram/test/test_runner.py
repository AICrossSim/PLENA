import os
from pathlib import Path
from cocotb.runner import get_runner

# Project path
project_path = Path(__file__).resolve().parent.parent

# Verilator-specific arguments for better waveform tracing
verilator_args = [
    "--trace",               # Enable standard VCD tracing
    "--trace-structs",       # Capture struct signals
    "--trace-params",        # Trace parameters
    "--trace-underscore",    # Include signals starting with "_"
    "--trace-fst",           # Enable FST (faster than VCD)
    "--trace-max-array", "1024",  # Ensure large arrays are dumped
    "--public-flat-rw",      # Prevent Verilator from optimizing signals away
]

def test_my_design_runner():
    # Detect simulator from environment variable
    sim = os.getenv("SIM", "verilator")  # Default to Verilator

    # Source files (ensure this contains 'ram_access_mapping' module)
    sources = [project_path / "tr_2p_ram.sv"]

    # Get appropriate runner
    runner = get_runner(sim)

    # Build the simulation (force recompile with always=True)
    runner.build(
        sources=sources,
        hdl_toplevel="ram_access_mapping",
        build_args=verilator_args,
        always=True  # Ensures rebuild when the source changes
    )

    # Run the test
    runner.test(
        hdl_toplevel="ram_access_mapping",
        test_module="test_tr_2p_ram"  # Remove the comma
    )

if __name__ == "__main__":
    test_my_design_runner()
