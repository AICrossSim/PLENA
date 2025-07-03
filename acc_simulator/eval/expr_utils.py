
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
