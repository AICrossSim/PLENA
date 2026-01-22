from __future__ import annotations

from typing import Any, Dict, List

from . import load_model


def _to_entries(memory_config: Any) -> List[Dict[str, Any]]:
    if isinstance(memory_config, list):
        return memory_config
    if isinstance(memory_config, dict):
        if "memories" in memory_config and isinstance(memory_config["memories"], list):
            return memory_config["memories"]
        if "memory_type" in memory_config or "type" in memory_config:
            return [memory_config]
    raise ValueError("memory_config must be a list or dict with 'memories'.")


def estimate_cost(memory_config: Any) -> Dict[str, Any]:
    """Estimate memory cost for one or more memory configs.

    Each entry supports:
      - memory_type (or type): string key for model JSON (e.g., "hbm3")
      - capacity_gb: float
    """
    entries = _to_entries(memory_config)
    breakdown: List[Dict[str, Any]] = []
    total_cost = 0.0

    for entry in entries:
        mem_type = entry.get("memory_type") or entry.get("type")
        if not mem_type:
            raise ValueError("Each memory entry must include 'memory_type' or 'type'.")
        capacity_gb = float(entry.get("capacity_gb", 0.0))

        model = load_model(str(mem_type))
        cost = model.get("cost") or {}
        price_per_gb = float(cost.get("price_per_gb_usd", 0.0))
        entry_cost = capacity_gb * price_per_gb
        total_cost += entry_cost

        breakdown.append(
            {
                "memory_type": mem_type,
                "capacity_gb": capacity_gb,
                "price_per_gb_usd": price_per_gb,
                "standard_size": cost.get("standard_size"),
                "cost_usd": entry_cost,
            }
        )

    return {
        "total_cost_usd": total_cost,
        "breakdown": breakdown,
    }
