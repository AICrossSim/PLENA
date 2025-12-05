"""Tool for running the behavioral simulator."""

import subprocess
import re
import sys
from typing import Dict, Any, Optional, Literal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BUILD_PATH = PROJECT_ROOT / "behavioral_simulator" / "testbench" / "build"
VRAM_DUMP_PATH = PROJECT_ROOT / "behavioral_simulator" / "vram_dump.bin"

# Add paths for imports
sys.path.insert(0, str(PROJECT_ROOT / "tools"))
sys.path.insert(0, str(PROJECT_ROOT / "behavioral_simulator" / "testbench"))
sys.path.insert(0, str(PROJECT_ROOT / "compiler"))


def run_simulator(assembly_code: str) -> Dict[str, Any]:
    """
    Run behavioral simulator on assembly code.

    Internally calls machine_code_generation, so Claude doesn't need to
    call it separately. This is the main tool for the generate-test loop.

    Args:
        assembly_code: PLENA assembly code string

    Returns:
        Dict with:
            - success: bool
            - latency_ns: Latency in nanoseconds (if simulation successful)
            - mse: Mean squared error vs golden output (if golden file exists)
            - instruction_count: Number of instructions
            - errors: List of errors (if any)
    """
    from .machine_code import machine_code_generation

    # Step 1: Generate machine code
    mc_result = machine_code_generation(assembly_code)
    if not mc_result["success"]:
        return {
            "success": False,
            "latency_ns": None,
            "mse": None,
            "instruction_count": 0,
            "errors": mc_result["syntax_errors"],
        }

    # Step 2: Check required files exist
    machine_code_path = BUILD_PATH / "generated_machine_code.mem"
    hbm_path = BUILD_PATH / "hbm_for_behave_sim.bin"
    fp_sram_path = BUILD_PATH / "fp_sram.bin"

    missing_files = []
    if not machine_code_path.exists():
        missing_files.append("Machine code missing")
    if not hbm_path.exists():
        missing_files.append("HBM data missing (call setup_test_environment first)")
    if not fp_sram_path.exists():
        missing_files.append("FP SRAM missing")

    if missing_files:
        return {
            "success": False,
            "latency_ns": None,
            "mse": None,
            "instruction_count": mc_result["instruction_count"],
            "errors": missing_files,
        }

    # Step 3: Run Rust simulator
    cmd = [
        "cargo", "run", "--release", "--",
        "--opcode", str(machine_code_path),
        "--hbm", str(hbm_path),
        "--fpsram", str(fp_sram_path),
        "--quiet"
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT / "behavioral_simulator",
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "latency_ns": None,
            "mse": None,
            "instruction_count": mc_result["instruction_count"],
            "errors": ["Simulator timeout (>120s)"],
        }
    except Exception as e:
        return {
            "success": False,
            "latency_ns": None,
            "mse": None,
            "instruction_count": mc_result["instruction_count"],
            "errors": [f"Failed to run simulator: {e}"],
        }

    # Step 4: Parse simulator output
    stdout = result.stdout
    stderr = result.stderr
    combined_output = stdout + "\n" + stderr  # Latency is printed to stderr

    if result.returncode != 0:
        return {
            "success": False,
            "latency_ns": None,
            "mse": None,
            "instruction_count": mc_result["instruction_count"],
            "errors": [stderr[:500] if stderr else f"Simulator exited with code {result.returncode}"],
        }

    # Parse latency from combined output (stderr has the final latency)
    latency_ns = parse_latency_ns(combined_output)

    # Step 5: Check accuracy if golden file exists
    mse = None
    golden_file = BUILD_PATH / "golden_result.txt"
    if golden_file.exists() and VRAM_DUMP_PATH.exists():
        try:
            accuracy = check_accuracy(str(VRAM_DUMP_PATH), str(golden_file))
            mse = accuracy.get("mse")
        except Exception as e:
            mse = f"error: {e}"

    return {
        "success": True,
        "latency_ns": latency_ns,
        "mse": mse,
        "instruction_count": mc_result["instruction_count"],
        "errors": [],
    }


def parse_latency_cycles(stdout: str) -> Optional[int]:
    """Parse cycle count from simulator output."""
    # Look for patterns like "Total cycles: 1234" or "Cycles: 1234"
    patterns = [
        r"Total cycles[:\s]+(\d+)",
        r"Cycles[:\s]+(\d+)",
        r"cycle count[:\s]+(\d+)",
        r"(\d+)\s*cycles",
    ]
    for pattern in patterns:
        match = re.search(pattern, stdout, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def parse_latency_ns(output: str) -> Optional[float]:
    """Parse latency in nanoseconds from simulator output (stdout + stderr)."""
    # Look for "Simulation completed. Last instance 982.000ns"
    patterns = [
        r"Last instance\s+([\d.]+)\s*ns",
        r"Simulation completed.*?([\d.]+)\s*ns",
        r"Latency[:\s]+([\d.]+)\s*ns",
        r"Time[:\s]+([\d.]+)\s*ns",
    ]
    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def check_accuracy(bin_file: str, golden_file: str) -> Dict[str, Any]:
    """
    Compare simulator output with golden reference.

    Args:
        bin_file: Path to VRAM dump binary file
        golden_file: Path to golden_result.txt file

    Returns:
        Dict with mse, mae, max_error, match_rate
    """
    # Import check_mem functions
    sys.path.insert(0, str(PROJECT_ROOT / "behavioral_simulator" / "testbench"))
    from check_mem import compare_with_golden

    try:
        results = compare_with_golden(
            bin_file,
            golden_file,
            exp_width=8,
            man_width=7,
            num_bytes_per_val=2,
            row_dim=64,
            start_row_idx=0,
            num_rows=None,
            use_stride_mode=True
        )
        return {
            "mse": float(results["mse"]),
            "mae": float(results["mae"]),
            "max_error": float(results["max_error"]),
            "match_rate": float(results["match_rate"]),
        }
    except Exception as e:
        return {"error": str(e)}


def run_simulator_with_data(
    assembly_code: str,
    input_tensors: Dict[str, Any],
    golden_output: Any,
    fp_preload: list = None,
) -> Dict[str, Any]:
    """
    Run simulator with custom input data (advanced usage).

    This function sets up the full simulation environment including
    input data and golden reference, then runs the simulator.

    Args:
        assembly_code: PLENA assembly code string
        input_tensors: Dict of input tensors (pytorch tensors)
        golden_output: Expected output tensor for accuracy check
        fp_preload: FP SRAM preload values (default [0.0, 1.0])

    Returns:
        Same as run_simulator but with accuracy computed against golden_output
    """
    import torch
    import numpy as np

    sys.path.insert(0, str(PROJECT_ROOT / "behavioral_simulator" / "testbench"))
    from create_sim_env import create_sim_env

    sys.path.insert(0, str(PROJECT_ROOT / "tools"))
    from sim_env_utils import build_sim_env

    if fp_preload is None:
        fp_preload = [0.0, 1.0]

    # Create golden result dict
    golden_result = {
        "input_tensor": input_tensors,
        "original_output": golden_output if isinstance(golden_output, torch.Tensor) else torch.tensor(golden_output)
    }

    # Setup simulation environment
    create_sim_env(input_tensors, assembly_code, golden_result, fp_preload)

    # Build environment (quantize data, generate HBM files)
    specified_data_order = list(input_tensors.keys())
    build_sim_env(
        data_size=256,
        mode="behave_sim",
        asm=None,
        data=None,
        specified_data_order=specified_data_order
    )

    # Now run simulator
    return run_simulator(assembly_code)


def setup_test_environment(
    layer_type: Literal["linear", "projection"] = "linear",
    hidden_size: int = 128,
    batch_size: int = 4,
) -> Dict[str, Any]:
    """
    Setup test environment with random input data for a given layer type.

    This generates the HBM data files required by run_simulator.
    Call this before run_simulator if no test data exists.

    Args:
        layer_type: Type of layer to test ('linear' or 'projection')
        hidden_size: Hidden dimension size (default 128)
        batch_size: Batch size (default 4)

    Returns:
        Dict with:
            - success: bool
            - assembly_code: Generated assembly code for the test
            - golden_output_shape: Shape of expected output
            - message: Status message
    """
    import torch
    from torch import nn

    from create_sim_env import create_sim_env
    from sim_env_utils.build_env import build_sim_env
    from asm_templates import projection_asm, preload_act_asm, reset_reg_asm, preload_addr_reg_asm

    try:
        # Clear build directory
        import shutil
        if BUILD_PATH.exists():
            shutil.rmtree(BUILD_PATH)
        BUILD_PATH.mkdir(parents=True, exist_ok=True)

        real_data_ratio = (8*8 + 8) / (8 * 8)
        fp_preload = [0.0, 1e-6, 1/hidden_size]

        # Generate random test data
        torch.manual_seed(42)
        act_tensor = torch.randn(batch_size, hidden_size)
        original_layer = nn.Linear(in_features=hidden_size, out_features=hidden_size, bias=False)
        weights = original_layer.state_dict()

        original_output = original_layer(act_tensor)

        input_tensor = {
            "act_tensor": act_tensor,
            "weights": weights['weight'].t(),
        }

        golden_result = {
            "input_tensor": input_tensor,
            "original_output": original_output
        }

        # Generate assembly code
        gen_assembly_code = f"; {layer_type.capitalize()} Test Generation \n"

        # Set the addr offset for weight
        gen_assembly_code += preload_addr_reg_asm(
            addr_reg_to_set=[1, 2],
            available_registers=[1, 2],
            addr_reg_val=[
                int(hidden_size * batch_size * real_data_ratio),
                int((hidden_size * (batch_size + 1) + hidden_size * hidden_size) * real_data_ratio)
            ]
        )

        # Reset the registers
        gen_assembly_code += reset_reg_asm(alive_registers=[1,2,3])

        # Gen Activation Preload
        gen_assembly_code += preload_act_asm(
            vlen=64,
            preload_len=4,
            batch=batch_size,
            hidden_size=hidden_size,
            alive_registers=[1,2,3],
            act_vram_offset=0,
            activation_offset_reg=0,
            stride_size=hidden_size
        )

        # Reset the registers
        gen_assembly_code += reset_reg_asm(alive_registers=[1,2,3,4])

        gen_assembly_code += projection_asm(
            mlen=64,
            blen=4,
            batch=batch_size,
            hidden_size=hidden_size,
            alive_registers=[1,2,3,4],
            w_base_hbm_offset_reg=1,
            activation_base_address=0,
            result_base_address=hidden_size * batch_size,
            rope_enabled=False
        )

        # Create simulation environment
        create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
        build_sim_env(
            data_size=256,
            mode="behave_sim",
            asm=layer_type,
            data=None,
            specified_data_order=["act_tensor", "weights"]
        )

        return {
            "success": True,
            "assembly_code": gen_assembly_code,
            "golden_output_shape": list(original_output.shape),
            "message": f"Test environment setup complete for {layer_type} layer. HBM data files created.",
        }

    except Exception as e:
        return {
            "success": False,
            "assembly_code": None,
            "golden_output_shape": None,
            "message": f"Failed to setup test environment: {e}",
        }
