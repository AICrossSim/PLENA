from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from . import load_model


@dataclass(frozen=True)
class PowerResult:
    dynamic_power_w: float
    leakage_power_w_min: float
    leakage_power_w_max: float

    @property
    def leakage_power_w_avg(self) -> float:
        return (self.leakage_power_w_min + self.leakage_power_w_max) / 2

    @property
    def total_power_w_min(self) -> float:
        return self.dynamic_power_w + self.leakage_power_w_min

    @property
    def total_power_w_max(self) -> float:
        return self.dynamic_power_w + self.leakage_power_w_max

    @property
    def total_power_w_avg(self) -> float:
        return self.dynamic_power_w + self.leakage_power_w_avg


def _to_entries(memory_config: Any) -> List[Dict[str, Any]]:
    if isinstance(memory_config, list):
        return memory_config
    if isinstance(memory_config, dict):
        if "memories" in memory_config and isinstance(memory_config["memories"], list):
            return memory_config["memories"]
        if "memory_type" in memory_config or "type" in memory_config:
            return [memory_config]
    raise ValueError("memory_config must be a list or dict with 'memories'.")


def _parse_range(value_range: Any) -> Tuple[float, float]:
    if isinstance(value_range, (int, float)):
        value = float(value_range)
        return value, value
    if isinstance(value_range, str):
        if "-" in value_range:
            lo_str, hi_str = value_range.split("-", 1)
            return float(lo_str.strip()), float(hi_str.strip())
        return float(value_range.strip()), float(value_range.strip())
    raise ValueError(f"Unsupported range format: {value_range}")


def _power_density_to_w_per_gb(value_range: Any, units: str) -> Tuple[float, float]:
    lo, hi = _parse_range(value_range)
    units = units.strip()
    if units == "W/GB":
        return lo, hi
    if units == "mW/GB":
        return lo / 1000.0, hi / 1000.0
    if units == "mW/MB":
        return (lo / 1000.0) * 1024.0, (hi / 1000.0) * 1024.0
    raise ValueError(f"Unsupported power density units: {units}")


def _get_idle_mode_power_density(
    model: Dict[str, Any],
    idle_mode: Optional[str],
) -> Tuple[float, float, str]:
    modes = model.get("leakage_power", {}).get("modes", [])
    if not modes:
        return 0.0, 0.0, ""
    if idle_mode:
        for mode in modes:
            if mode.get("mode") == idle_mode:
                density = mode.get("idle_power_density", {})
                lo, hi = _power_density_to_w_per_gb(
                    density.get("value_range", 0.0),
                    density.get("units", "W/GB"),
                )
                return lo, hi, mode.get("mode", "")
    mode = modes[0]
    density = mode.get("idle_power_density", {})
    lo, hi = _power_density_to_w_per_gb(
        density.get("value_range", 0.0),
        density.get("units", "W/GB"),
    )
    return lo, hi, mode.get("mode", "")


def _dynamic_power_w(read_pj_per_bit: float, bandwidth_gb_s: float) -> float:
    # bandwidth in GB/s -> bits/s: bandwidth_gb_s * 1e9 bytes/s * 8 bits/byte
    # energy per bit in pJ -> J: * 1e-12
    return read_pj_per_bit * bandwidth_gb_s * 8e-3


def estimate_power(memory_config: Any) -> Dict[str, Any]:
    """Estimate dynamic + leakage power for one or more memory configs.

    Each entry supports:
      - memory_type (or type): string key for model JSON (e.g., "hbm3")
      - capacity_gb: float
      - bandwidth_gb_s: float
      - idle_mode: optional string matching a leakage mode name in the model
    """
    entries = _to_entries(memory_config)
    breakdown: List[Dict[str, Any]] = []
    total_dynamic = 0.0
    total_leak_min = 0.0
    total_leak_max = 0.0

    for entry in entries:
        mem_type = entry.get("memory_type") or entry.get("type")
        if not mem_type:
            raise ValueError("Each memory entry must include 'memory_type' or 'type'.")
        capacity_gb = float(entry.get("capacity_gb", 0.0))
        bandwidth_gb_s = float(entry.get("bandwidth_gb_s", 0.0))
        idle_mode = entry.get("idle_mode")

        model = load_model(str(mem_type))
        read_pj_per_bit = float(model.get("dynamic_power", {}).get("read_pj_per_bit", 0.0))
        dyn_w = _dynamic_power_w(read_pj_per_bit, bandwidth_gb_s) if bandwidth_gb_s else 0.0

        density_lo, density_hi, used_mode = _get_idle_mode_power_density(model, idle_mode)
        leak_min = density_lo * capacity_gb
        leak_max = density_hi * capacity_gb

        total_dynamic += dyn_w
        total_leak_min += leak_min
        total_leak_max += leak_max

        breakdown.append(
            {
                "memory_type": mem_type,
                "capacity_gb": capacity_gb,
                "bandwidth_gb_s": bandwidth_gb_s,
                "idle_mode": used_mode,
                "dynamic_power_w": dyn_w,
                "leakage_power_w": {
                    "min": leak_min,
                    "max": leak_max,
                    "avg": (leak_min + leak_max) / 2,
                },
                "total_power_w": {
                    "min": dyn_w + leak_min,
                    "max": dyn_w + leak_max,
                    "avg": dyn_w + (leak_min + leak_max) / 2,
                },
            }
        )

    return {
        "total_dynamic_power_w": total_dynamic,
        "total_leakage_power_w": {
            "min": total_leak_min,
            "max": total_leak_max,
            "avg": (total_leak_min + total_leak_max) / 2,
        },
        "total_power_w": {
            "min": total_dynamic + total_leak_min,
            "max": total_dynamic + total_leak_max,
            "avg": total_dynamic + (total_leak_min + total_leak_max) / 2,
        },
        "breakdown": breakdown,
    }
