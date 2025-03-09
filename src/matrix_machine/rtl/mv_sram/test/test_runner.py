import os
from pathlib import Path
from cocotb.runner import get_runner

# # Project path
project_path = Path(__file__).resolve().parent.parent

# # Verilator arguments for tracing
verilator_args = [
    "--trace",              # Enable VCD/FST tracing
    "--trace-structs",      # Capture struct signals
]

icarus_args = []

def test_my_design_runner():
    # Detect simulator from environment
    sim = os.getenv("SIM", "icarus")  # Default to Verilator
    # os.environ["WAVES"] = "1"

    # Source files (ensure 'ram_access_mapping' is defined inside these files)
    sources = [
        project_path / "subsram.sv",
        project_path / "subtile_transpose.sv",
    ]

    # Get simulator runner
    runner = get_runner(sim)

    # Build the simulation
    runner.build(
        verilog_sources=sources,
        hdl_toplevel="subsram",
        build_args=verilator_args if sim == "verilator" else icarus_args,
        always=True  # Force rebuild if source changes
    )

    # Run the test
    runner.test(
        hdl_toplevel="subsram",
        # test_args={"results_xml": "results.xml"},  # Ensure correct argument
        test_module="test_subsram",
    )


if __name__ == "__main__":
    test_my_design_runner()
