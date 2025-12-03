"""Tool for running the behavioral simulator."""

from typing import Dict, Any, Optional
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BUILD_PATH = PROJECT_ROOT / "behavioral_simulator" / "testbench" / "build"


def run_simulator(
    assembly_code: str,
    input_data: Optional[Dict] = None,
    golden_data: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Run behavioral simulator on assembly code.

    Internally calls machine_code_generation, so Claude doesn't need to
    call it separately. This is the main tool for the generate-test loop.

    Args:
        assembly_code: PLENA assembly code string
        input_data: Optional dict of input tensors (for data setup)
        golden_data: Optional dict with golden reference for accuracy check

    Returns:
        Dict with:
            - success: bool
            - syntax_errors: List of assembly syntax errors (if any)
            - latency: Cycle count (if simulation successful)
            - accuracy: Dict with mse, mae, max_error (if golden provided)
            - hbm_usage: Memory usage stats
            - instruction_errors: List of runtime errors (if any)
    """
    # TODO: Implement full pipeline
    #
    # Step 1: Generate machine code (internal, not returned to Claude)
    # from .machine_code import machine_code_generation
    # mc_result = machine_code_generation(assembly_code)
    # if not mc_result["success"]:
    #     return {
    #         "success": False,
    #         "syntax_errors": mc_result["syntax_errors"],
    #         "latency": None,
    #         "accuracy": None,
    #         "hbm_usage": None,
    #         "instruction_errors": [],
    #     }
    #
    # Step 2: Setup simulation environment
    # from sim_env_utils.build_sys_tools import init_mem, env_setup
    # init_mem(BUILD_PATH)
    # # ... setup HBM data from input_data ...
    #
    # Step 3: Run Rust simulator
    # import subprocess
    # machine_code_path = BUILD_PATH / "generated_machine_code.mem"
    # hbm_path = BUILD_PATH / "hbm_for_behave_sim.mem"
    #
    # cmd = [
    #     "cargo", "run", "--release", "--",
    #     "--opcode", str(machine_code_path),
    #     "--hbm", str(hbm_path),
    #     "--quiet"
    # ]
    # result = subprocess.run(
    #     cmd,
    #     cwd=PROJECT_ROOT / "behavioral_simulator",
    #     capture_output=True,
    #     text=True
    # )
    #
    # if result.returncode != 0:
    #     return {
    #         "success": False,
    #         "syntax_errors": [],
    #         "latency": None,
    #         "accuracy": None,
    #         "hbm_usage": None,
    #         "instruction_errors": [result.stderr],
    #     }
    #
    # Step 4: Parse latency from stdout
    # latency = parse_latency(result.stdout)
    #
    # Step 5: Check accuracy (if golden provided)
    # accuracy = None
    # if golden_data:
    #     from behavioral_simulator.testbench.check_mem import compare_with_golden
    #     accuracy_result = compare_with_golden(
    #         bin_file=str(PROJECT_ROOT / "behavioral_simulator" / "vram_dump.bin"),
    #         golden_file=str(BUILD_PATH / "golden_result.txt"),
    #     )
    #     accuracy = {
    #         "mse": accuracy_result["mse"],
    #         "mae": accuracy_result["mae"],
    #         "max_error": accuracy_result["max_error"],
    #     }
    #
    # return {
    #     "success": True,
    #     "syntax_errors": [],
    #     "latency": latency,
    #     "accuracy": accuracy,
    #     "hbm_usage": {"estimated_bytes": ...},
    #     "instruction_errors": [],
    # }

    raise NotImplementedError("run_simulator not implemented")


def parse_latency(stdout: str) -> Optional[int]:
    """Parse cycle count from simulator output."""
    # TODO: Implement based on actual simulator output format
    # Example:
    # import re
    # match = re.search(r"Total cycles:\s*(\d+)", stdout)
    # return int(match.group(1)) if match else None
    return None
