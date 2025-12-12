"""Tool for debugging simulation results by viewing memory contents."""

import sys
from typing import Dict, Any, Optional
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BUILD_PATH = PROJECT_ROOT / "behavioral_simulator" / "testbench" / "build"
VRAM_DUMP_PATH = PROJECT_ROOT / "behavioral_simulator" / "vram_dump.bin"

sys.path.insert(0, str(PROJECT_ROOT / "behavioral_simulator" / "testbench"))


def debug_view_memory(
    assembly_code: str = "",
    num_rows: int = 8,
    start_row: int = 8,
    show_golden: bool = True,
    num_batches: int = 4,
    hidden_size: int = 128,
    skip_reorder: bool = False,
) -> Dict[str, Any]:
    """
    View simulator memory output and compare with golden reference for debugging.

    Use this tool when MSE is high to understand what went wrong:
    - See actual values produced by your assembly code
    - Compare side-by-side with expected golden values
    - Identify patterns (all zeros = not computed, wrong values = incorrect addressing)

    Args:
        assembly_code: The assembly code being debugged (required for context)
        num_rows: Number of rows to display (default 8, each row = 64 values)
        start_row: Starting row index (default 0)
        show_golden: Whether to show golden reference values (default True)
        num_batches: Number of batches in the output (default 4, set to match your test config)
        hidden_size: Hidden dimension size (default 128, set to match your test config)
        skip_reorder: Skip stride reordering - use for raw memory view (default False)

    Returns:
        Dict with simulated values, golden values, per-row error analysis, and the code being debugged
    """
    from check_mem import (
        read_bin_file_as_array,
        parse_golden_output,
        reorder_stride_mode,
    )

    result = {
        "success": False,
        "simulated_values": None,
        "golden_values": None,
        "row_analysis": [],
        "error": None,
        "assembly_code": assembly_code,
    }

    # Check if files exist
    if not VRAM_DUMP_PATH.exists():
        result["error"] = f"VRAM dump not found: {VRAM_DUMP_PATH}. Run simulator first."
        return result

    golden_file = BUILD_PATH / "golden_result.txt"
    if show_golden and not golden_file.exists():
        result["error"] = f"Golden file not found: {golden_file}"
        return result

    try:
        # Read simulated output
        simulated = read_bin_file_as_array(
            str(VRAM_DUMP_PATH),
            exp_width=8,
            man_width=7,
            row_dim=64,
            num_bytes_per_val=2,
            start_row_idx=start_row,
            num_rows=None,
        )

        # Reorder from stride mode to batch-wise layout (unless skipped)
        if not skip_reorder and num_batches > 0 and hidden_size > 0:
            try:
                simulated = reorder_stride_mode(simulated, num_batches=num_batches, elements_per_batch=hidden_size)
            except (IndexError, ValueError) as e:
                # If reorder fails, return raw data with warning
                result["warning"] = f"Stride reorder failed ({e}), showing raw memory. Try skip_reorder=True or adjust num_batches/hidden_size."

        # Read golden if requested
        golden = None
        if show_golden:
            golden_full = parse_golden_output(str(golden_file))
            # Extract corresponding section
            start_idx = start_row * 64
            end_idx = start_idx + len(simulated)
            golden = golden_full[start_idx:end_idx] if end_idx <= len(golden_full) else golden_full[start_idx:]

        result["success"] = True

        # Format values for display (show first/last few per row)
        sim_rows = []
        gold_rows = []
        row_analysis = []

        values_per_row = 64
        num_display_rows = min(num_rows, max(1, len(simulated) // values_per_row))

        for i in range(num_display_rows):
            start = i * values_per_row
            end = min(start + values_per_row, len(simulated))
            sim_row = simulated[start:end]

            if len(sim_row) == 0:
                continue

            # Show summary: first 4, ..., last 4
            sim_summary = [f"{v:.4f}" for v in sim_row[:4]] + ["..."] + [f"{v:.4f}" for v in sim_row[-4:]]
            sim_rows.append(f"Row {start_row + i}: [{', '.join(sim_summary)}]")

            row_info = {
                "row": start_row + i,
                "sim_min": float(np.min(sim_row)),
                "sim_max": float(np.max(sim_row)),
                "sim_mean": float(np.mean(sim_row)),
                "sim_nonzero": int(np.count_nonzero(sim_row)),
            }

            if golden is not None and end <= len(golden):
                gold_row = golden[start:end]
                gold_summary = [f"{v:.4f}" for v in gold_row[:4]] + ["..."] + [f"{v:.4f}" for v in gold_row[-4:]]
                gold_rows.append(f"Row {start_row + i}: [{', '.join(gold_summary)}]")

                # Per-row error
                row_mse = float(np.mean((sim_row - gold_row) ** 2))
                row_mae = float(np.mean(np.abs(sim_row - gold_row)))
                row_info["golden_min"] = float(np.min(gold_row))
                row_info["golden_max"] = float(np.max(gold_row))
                row_info["row_mse"] = row_mse
                row_info["row_mae"] = row_mae

            row_analysis.append(row_info)

        result["simulated_summary"] = sim_rows
        result["golden_summary"] = gold_rows if golden is not None else None
        result["row_analysis"] = row_analysis

        # Overall stats
        result["overall"] = {
            "total_values": len(simulated),
            "simulated_range": [float(np.min(simulated)), float(np.max(simulated))] if len(simulated) > 0 else [0, 0],
            "num_zeros": int(np.sum(simulated == 0)),
            "num_nans": int(np.sum(np.isnan(simulated))),
        }

        if golden is not None and len(golden) > 0:
            min_len = min(len(simulated), len(golden))
            if min_len > 0:
                mse = float(np.mean((simulated[:min_len] - golden[:min_len]) ** 2))
                result["overall"]["mse"] = mse
            result["overall"]["golden_range"] = [float(np.min(golden)), float(np.max(golden))]

    except Exception as e:
        result["error"] = str(e)

    return result
