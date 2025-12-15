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


def run_simulator(
    assembly_code: str,
    layer_type: Literal["linear", "ffn", "attention", "rms_norm", "silu"] = "linear",
    model_name: Optional[str] = None,
    hidden_size: int = 128,
    output_size: Optional[int] = None,
    intermediate_size: Optional[int] = None,
    batch_size: int = 4,
    seq_len: int = 1,
) -> Dict[str, Any]:
    """
    Run full simulation pipeline: setup test data, assemble, execute, check accuracy.

    This is the main tool for testing assembly code. It handles everything:
    1. Creates random input tensors based on layer_type and dimensions
    2. Computes golden reference output using PyTorch
    3. Assembles assembly code to machine code
    4. Runs the behavioral simulator
    5. Compares output against golden reference

    Args:
        assembly_code: PLENA assembly code string
        layer_type: Type of layer ('linear', 'ffn', 'attention', 'rms_norm', 'silu')
        model_name: Model name (e.g., 'llama-3.2-1b') - if provided, auto-loads dimensions
        hidden_size: Input dimension (default 128, overridden if model_name provided)
        output_size: Output dimension for linear layer (default: same as hidden_size)
        intermediate_size: FFN intermediate size (default 4*hidden_size, only for ffn)
        batch_size: Batch size (default 4)
        seq_len: Sequence length (default 1)

    Returns:
        Dict with:
            - success: bool - True if simulation completed without errors
            - latency_ns: float - Simulation latency in nanoseconds
            - mse: float - Mean squared error vs golden output
            - match_rate: float - Percentage of values within tolerance
            - instruction_count: int - Number of instructions
            - errors: list - Any errors encountered
            - test_config: dict - The test configuration used
    """
    import torch
    from torch import nn

    # Step 0: Load dimensions from model config if model_name provided
    if model_name:
        from .workload import get_workload
        workload = get_workload(model_name, layer_type, batch_size, seq_len)
        if "error" in workload:
            return {
                "success": False,
                "latency_ns": None,
                "mse": None,
                "match_rate": None,
                "instruction_count": 0,
                "errors": [workload["error"]],
                "test_config": None,
                "submitted_assembly": assembly_code,
            }
        hidden_size = workload.get("hidden_size", hidden_size)
        intermediate_size = workload.get("intermediate_size", intermediate_size)

    # Step 1: Assemble code first to check syntax
    from .machine_code import machine_code_generation

    mc_result = machine_code_generation(assembly_code)
    if not mc_result["success"]:
        return {
            "success": False,
            "latency_ns": None,
            "mse": None,
            "match_rate": None,
            "instruction_count": 0,
            "errors": mc_result["syntax_errors"],
            "test_config": None,
            "submitted_assembly": assembly_code,  # Include code for agent to reason about
        }

    # Step 2: Setup test environment based on layer type
    try:
        test_config = _setup_test_data(
            layer_type=layer_type,
            hidden_size=hidden_size,
            output_size=output_size,
            intermediate_size=intermediate_size,
            batch_size=batch_size,
            seq_len=seq_len,
            assembly_code=assembly_code,
        )
    except Exception as e:
        return {
            "success": False,
            "latency_ns": None,
            "mse": None,
            "match_rate": None,
            "instruction_count": mc_result["instruction_count"],
            "errors": [f"Failed to setup test data: {e}"],
            "test_config": None,
            "submitted_assembly": assembly_code,
        }

    # Step 3: Run the Rust simulator
    machine_code_path = BUILD_PATH / "generated_machine_code.mem"
    hbm_path = BUILD_PATH / "hbm_for_behave_sim.bin"
    fp_sram_path = BUILD_PATH / "fp_sram.bin"

    # Verify files exist
    missing = []
    if not machine_code_path.exists():
        missing.append("machine code")
    if not hbm_path.exists():
        missing.append("HBM data")
    if not fp_sram_path.exists():
        missing.append("FP SRAM")
    if missing:
        return {
            "success": False,
            "latency_ns": None,
            "mse": None,
            "match_rate": None,
            "instruction_count": mc_result["instruction_count"],
            "errors": [f"Missing files after setup: {missing}"],
            "test_config": test_config,
            "submitted_assembly": assembly_code,
        }

    cmd = [
        "cargo",
        "run",
        "--release",
        "--",
        "--opcode",
        str(machine_code_path),
        "--hbm",
        str(hbm_path),
        "--fpsram",
        str(fp_sram_path),
        "--quiet",
    ]

    try:
        result = subprocess.run(
            cmd, cwd=PROJECT_ROOT / "behavioral_simulator", capture_output=True, text=True, timeout=120
        )
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "latency_ns": None,
            "mse": None,
            "match_rate": None,
            "instruction_count": mc_result["instruction_count"],
            "errors": ["Simulator timeout (>120s) - possible infinite loop"],
            "test_config": test_config,
            "submitted_assembly": assembly_code,
        }
    except Exception as e:
        return {
            "success": False,
            "latency_ns": None,
            "mse": None,
            "match_rate": None,
            "instruction_count": mc_result["instruction_count"],
            "errors": [f"Failed to run simulator: {e}"],
            "test_config": test_config,
            "submitted_assembly": assembly_code,
        }

    # Step 4: Parse output
    combined_output = result.stdout + "\n" + result.stderr

    if result.returncode != 0:
        error_msg = result.stderr[:5000] if result.stderr else f"Exit code {result.returncode}"
        return {
            "success": False,
            "latency_ns": None,
            "mse": None,
            "match_rate": None,
            "instruction_count": mc_result["instruction_count"],
            "errors": [f"Simulator error: {error_msg}"],
            "test_config": test_config,
            "submitted_assembly": assembly_code,
        }

    latency_ns = _parse_latency_ns(combined_output)

    # Step 5: Check accuracy
    mse = None
    match_rate = None
    golden_file = BUILD_PATH / "golden_result.txt"

    if golden_file.exists() and VRAM_DUMP_PATH.exists():
        try:
            accuracy = _check_accuracy(
                str(VRAM_DUMP_PATH),
                str(golden_file),
                batch_size=test_config["batch_size"],
                input_size=test_config["hidden_size"],
                output_size=test_config.get("output_size", test_config["hidden_size"]),
                output_in_place=test_config.get("output_in_place", False),
            )
            mse = accuracy.get("mse")
            match_rate = accuracy.get("match_rate")
        except Exception as e:
            # Non-fatal - return results but note accuracy check failed
            return {
                "success": True,
                "latency_ns": latency_ns,
                "mse": f"accuracy check error: {e}",
                "match_rate": None,
                "instruction_count": mc_result["instruction_count"],
                "errors": [],
                "test_config": test_config,
                "submitted_assembly": assembly_code,
            }

    result = {
        "success": True,
        "latency_ns": latency_ns,
        "mse": mse,
        "match_rate": match_rate,
        "instruction_count": mc_result["instruction_count"],
        "errors": [],
        "test_config": test_config,
    }

    # Add debugging hint when MSE is high
    if mse is not None and mse > 0.01:
        result["debug_hint"] = "MSE is high. Before rewriting and calling the check memory tool, trace your code line-by-line to reason about it first."

    return result


def _setup_test_data(
    layer_type: str,
    hidden_size: int,
    output_size: Optional[int],
    intermediate_size: Optional[int],
    batch_size: int,
    seq_len: int,
    assembly_code: str,
) -> Dict[str, Any]:
    """Setup test environment with random data for the given layer type."""
    import shutil
    import torch
    from torch import nn

    from create_sim_env import create_sim_env
    from sim_env_utils import create_mem_for_sim

    # Clear and recreate build directory
    if BUILD_PATH.exists():
        shutil.rmtree(BUILD_PATH)
    BUILD_PATH.mkdir(parents=True, exist_ok=True)

    torch.manual_seed(42)  # Reproducible

    # Compute data ratio for quantization
    real_data_ratio = (8 * 8 + 8) / (8 * 8)

    # Default output_size to hidden_size if not specified
    out_size = output_size if output_size is not None else hidden_size

    test_config = {
        "layer_type": layer_type,
        "hidden_size": hidden_size,
        "output_size": out_size,
        "batch_size": batch_size,
        "seq_len": seq_len,
    }

    if layer_type == "linear":
        # Linear layer: (batch, hidden_size) @ (hidden_size, output_size) -> (batch, output_size)
        fp_preload = [0.0, 1e-6, 1 / hidden_size]

        act_tensor = torch.randn(batch_size * seq_len, hidden_size)
        layer = nn.Linear(hidden_size, out_size, bias=False)
        golden_output = layer(act_tensor)

        input_tensors = {
            "act_tensor": act_tensor,
            "weights": layer.weight.t(),  # Shape: (hidden_size, output_size)
        }
        data_order = ["act_tensor", "weights"]
        test_config["output_shape"] = list(golden_output.shape)
        test_config["fp_sram_layout"] = {
            "0": "0.0 (unused)",
            "1": "epsilon = 1e-6",
            "2": f"1/hidden_size = {1 / hidden_size}"
        }

    elif layer_type == "ffn":
        # FFN: up_proj, gate_proj, down_proj with SiLU activation
        inter_size = intermediate_size or (4 * hidden_size)
        test_config["intermediate_size"] = inter_size
        fp_preload = [0.0, 1e-6, 1.0]

        act_tensor = torch.randn(batch_size * seq_len, hidden_size)
        up_proj = nn.Linear(hidden_size, inter_size, bias=False)
        gate_proj = nn.Linear(hidden_size, inter_size, bias=False)
        down_proj = nn.Linear(inter_size, hidden_size, bias=False)

        # FFN forward: down(silu(gate(x)) * up(x))
        up_out = up_proj(act_tensor)
        gate_out = gate_proj(act_tensor)
        silu_gate = nn.functional.silu(gate_out)
        golden_output = down_proj(silu_gate * up_out)

        input_tensors = {
            "act_tensor": act_tensor,
            "up_weights": up_proj.weight.t(),
            "gate_weights": gate_proj.weight.t(),
            "down_weights": down_proj.weight.t(),
        }
        data_order = ["act_tensor", "up_weights", "gate_weights", "down_weights"]
        test_config["output_shape"] = list(golden_output.shape)
        test_config["fp_sram_layout"] = {
            "0": "0.0 (unused)",
            "1": "epsilon = 1e-6",
            "2": "1.0 (for scaling)"
        }

    elif layer_type == "rms_norm":
        # RMS Normalization: x / sqrt(mean(x^2) + eps)
        eps = 1e-6
        fp_preload = [0.0, eps, 1.0 / hidden_size]

        act_tensor = torch.randn(batch_size * seq_len, hidden_size)
        # RMS norm: x / sqrt(mean(x^2) + eps)
        rms = torch.sqrt(torch.mean(act_tensor**2, dim=-1, keepdim=True) + eps)
        golden_output = act_tensor / rms

        # RMS norm stores output IN-PLACE (overwrites activation at address 0)
        input_tensors = {"act_tensor": act_tensor}
        data_order = ["act_tensor"]
        test_config["output_shape"] = list(golden_output.shape)
        test_config["output_in_place"] = True  # Flag for accuracy check
        test_config["fp_sram_layout"] = {
            "0": "0.0 (unused)",
            "1": f"epsilon = {eps}",
            "2": f"1/hidden_size = {1.0 / hidden_size}"
        }

    elif layer_type == "silu":
        # SiLU activation: x * sigmoid(x) = x * (1 / (1 + exp(-x)))
        # FP SRAM layout: [0]=0.0, [1]=1.0 (for sigmoid computation)
        fp_preload = [0.0, 1.0]

        act_tensor = torch.randn(batch_size * seq_len, hidden_size)
        golden_output = nn.functional.silu(act_tensor)

        # SiLU stores output IN-PLACE
        input_tensors = {"act_tensor": act_tensor}
        data_order = ["act_tensor"]
        test_config["output_shape"] = list(golden_output.shape)
        test_config["output_in_place"] = True
        test_config["fp_sram_layout"] = {
            "0": "0.0 (for negation: 0 - x = -x)",
            "1": "1.0 (for sigmoid: 1 + exp(-x))"
        }

    else:
        raise ValueError(f"Unsupported layer_type: {layer_type}. Use 'linear', 'ffn', 'rms_norm', or 'silu'")

    # Create golden result structure
    golden_result = {"input_tensor": input_tensors, "original_output": golden_output}

    # Setup simulation environment
    create_sim_env(input_tensors, assembly_code, golden_result, fp_preload)
    create_mem_for_sim(data_size=256, mode="behave_sim", asm=layer_type, data=None, specified_data_order=data_order)

    return test_config


def _parse_latency_ns(output: str) -> Optional[float]:
    """Parse latency in nanoseconds from simulator output."""
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


def _check_accuracy(
    bin_file: str,
    golden_file: str,
    batch_size: int = 4,
    input_size: int = 128,
    output_size: int = 128,
    output_in_place: bool = False,
) -> Dict[str, Any]:
    """Compare simulator output with golden reference.

    For most layers: Output is stored AFTER activations in Vector SRAM.
    For RMS norm: Output is stored IN-PLACE (overwrites activation at row 0).
    """
    from check_mem import compare_with_golden

    if output_in_place:
        # RMS norm: output overwrites input at row 0
        start_row_idx = 0
        # Number of rows = (batch_size * output_size) / 64
        num_rows = (batch_size * output_size) // 64
    else:
        # Other layers: output stored after activations
        activation_elements = batch_size * input_size
        start_row_idx = activation_elements // 64  # Each row is 64 elements
        num_rows = None

    results = compare_with_golden(
        bin_file,
        golden_file,
        exp_width=8,
        man_width=7,
        num_bytes_per_val=2,
        row_dim=64,
        start_row_idx=start_row_idx,
        num_rows=num_rows,
        use_stride_mode=True,
        num_batches=batch_size,
        elements_per_batch=output_size,
    )
    return {
        "mse": float(results["mse"]),
        "mae": float(results["mae"]),
        "max_error": float(results["max_error"]),
        "match_rate": float(results["match_rate"]),
    }
