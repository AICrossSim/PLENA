from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


_MODEL_DIR = Path(__file__).resolve().parent


def load_model(memory_type: str) -> Dict[str, Any]:
    """Load a single memory model JSON by memory_type.

    Example: load_model("hbm3") -> loads hbm3.json
    """
    file_name = f"{memory_type.strip().lower()}.json"
    path = _MODEL_DIR / file_name
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_all_models() -> Dict[str, Dict[str, Any]]:
    """Load all memory model JSON files in this directory."""
    models: Dict[str, Dict[str, Any]] = {}
    for path in sorted(_MODEL_DIR.glob("*.json")):
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        key = data.get("memory_type", path.stem).lower()
        models[key] = data
    return models
