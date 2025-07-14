
import json
from datetime import datetime
from zoneinfo import ZoneInfo 
from pathlib import Path

import torch
from torch import nn


def create_experiment_log_dir(base_dir: str = "logs") -> Path:
    # Always store logs inside acc_simulator/logs regardless of current working directory
    root_dir = Path(__file__).resolve().parent.parent 
    log_root = root_dir / base_dir 
    timestamp = datetime.now(ZoneInfo("Europe/London")).strftime("%Y%m%d-%H%M%S")
    log_dir = log_root / f"run-{timestamp}"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create symlink to latest
    latest_link = log_root / "latest"
    if latest_link.is_symlink() or latest_link.exists():
        latest_link.unlink()
    latest_link.symlink_to(log_dir, target_is_directory=True)

    return log_dir


def save_args(log_dir: Path, args: dict):
    def make_serializable(obj):
        if isinstance(obj, (Path, torch.dtype)):
            return str(obj)
        elif hasattr(obj, "__dict__"):
            return {k: make_serializable(v) for k, v in vars(obj).items()}
        elif isinstance(obj, (list, tuple)):
            return [make_serializable(v) for v in obj]
        elif isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        else:
            try:
                json.dumps(obj)
                return obj
            except TypeError:
                return str(obj)

    serializable_args = make_serializable(args)
    with open(log_dir / "args.json", "w") as f:
        json.dump(serializable_args, f, indent=2)


def save_results(log_dir: Path, results: dict):
    def make_serializable(obj):
        if isinstance(obj, (Path,)):
            return str(obj)
        elif isinstance(obj, torch.dtype):
            return str(obj)
        elif isinstance(obj, (list, tuple)):
            return [make_serializable(x) for x in obj]
        elif isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        else:
            try:
                json.dumps(obj)
                return obj
            except TypeError:
                return str(obj)

    results = make_serializable(results)

    with open(log_dir / "results.json", "w") as f:
        json.dump(results, f, indent=2)


def print_all_layers(model: nn.Module):
    print("=== Model Layers and Devices ===")
    for name, layer in model.named_modules():
        try:
            device = next(layer.parameters()).device
        except StopIteration:
            device = "No parameters"
        print(f"{name}: {type(layer).__name__} | device: {device}")
    print("====================")


def validate_and_sanitize_quant_args(
    preset: str,
    preset_mxfp_X: str | None,
    preset_mxfp_W: str | None,
    preset_mxfp_Kv: str | None,
    preset_minifloat_NL: str | None,
    preset_minifloat_X: str | None,
) -> tuple[str | None, str | None, str | None, str | None]:
    """
    Validate and sanitize quantization flags based on the preset string.

    Ensures that:
    - If a quantization type (e.g., Xq, Wq) is specified in the preset,
      the corresponding format must be provided.
    - If not specified in the preset, any provided format is ignored with a warning.

    Raises:
        AssertionError: If the preset is not one of the allowed values.
        ValueError: If a required quantization format is missing.

    Returns:
        A tuple of (preset_mxfp_X, preset_mxfp_W, preset_mxfp_Kv, preset_minifloat_NL),
        with unused arguments set to None.
    """
    allowed_presets = [
        "XqWqBqKVqNLq", "XWBKVNLq",
        "XWqBqKVq", "XWqBqKV", "XWqBqKVq", "original", "XqWqBqKVq"
    ]

    assert preset in allowed_presets, f"Unsupported preset: '{preset}'"

    def check_and_clear(flag: str, arg_value: str | None, arg_name: str) -> str | None:
        if flag in preset:
            if arg_value is None:
                raise ValueError(f"Preset includes '{flag}' but '{arg_name}' is not specified.")
            return arg_value
        else:
            if arg_value is not None:
                print(f"[Warning] '{arg_name}' is provided but '{flag}' not in preset. Ignoring it.")
            return None

    preset_mxfp_X = check_and_clear("Xq", preset_mxfp_X, "preset_mxfp_X")
    preset_minifloat_X = check_and_clear("Xq", preset_minifloat_X, "preset_minifloat_X")
    preset_mxfp_W = check_and_clear("Wq", preset_mxfp_W, "preset_mxfp_W")
    preset_mxfp_Kv = check_and_clear("KVq", preset_mxfp_Kv, "preset_mxfp_Kv")
    preset_minifloat_NL = check_and_clear("NLq", preset_minifloat_NL, "preset_minifloat_NL")

    return preset_mxfp_X, preset_mxfp_W, preset_mxfp_Kv, preset_minifloat_X, preset_minifloat_NL
