from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .utils import parse_toml_file
from .sys_latency import build_hardware_config, build_sys_config, compute_ttft_tps
from .memory_modelling.power_model import estimate_power
from .memory_modelling.cost_model import estimate_cost


@dataclass(frozen=True)
class SearchConstraints:
    max_power_w: Optional[float] = None
    max_cost_usd: Optional[float] = None


@dataclass(frozen=True)
class SearchOptions:
    max_range_samples: int = 3
    allow_phase_specific_memory: bool = True
    allow_phase_specific_execution: bool = True
    capacity_unit: str = "MB"
    max_evaluations: int = 5000


def _sample_range(values: Iterable[Any], max_samples: int) -> List[Any]:
    vals = list(values)
    if not vals:
        return []
    if len(vals) <= max_samples:
        return vals
    mid = vals[len(vals) // 2]
    return [vals[0], mid, vals[-1]]


def _capacity_to_gb(value: float, unit: str) -> float:
    if unit.upper() == "GB":
        return float(value)
    if unit.upper() == "MB":
        return float(value) / 1024.0
    raise ValueError(f"Unsupported capacity unit: {unit}")


def _execution_factor(
    exec_choice: Dict[str, Any],
    base_br: int,
    base_bc: int,
) -> float:
    ffn_exec = {
        "Output Stationary": 1.0,
        "Activation Stationary": 1.05,
        "Weight Stationary": 1.08,
    }.get(exec_choice["ffn_execution_order"], 1.0)
    ffn_pri = {
        "Weight Priority": 1.0,
        "Activation Priority": 1.03,
    }.get(exec_choice["ffn_on_chip_storage_priority"], 1.0)
    flash_exec = {
        "Head Iteration": 1.0,
        "Weight Iteration": 1.05,
    }.get(exec_choice["flash_execution_order"], 1.0)
    flash_pri = {
        "KV Priority": 1.0,
        "Weight Priority": 1.03,
    }.get(exec_choice["flash_on_chip_storage_priority"], 1.0)

    br = max(1, int(exec_choice["flash_soft_tiling_br"]))
    bc = max(1, int(exec_choice["flash_soft_tiling_bc"]))
    tiling_factor = (base_br / br) ** 0.1 * (base_bc / bc) ** 0.1
    return ffn_exec * ffn_pri * flash_exec * flash_pri * tiling_factor


def _memory_entries_for_power_cost(
    matrix_entries: List[Dict[str, Any]],
    vector_entry: Optional[Dict[str, Any]],
    offchip_entries: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    entries = []
    entries.extend(matrix_entries)
    if vector_entry:
        entries.append(vector_entry)
    entries.extend(offchip_entries)
    return entries


def _build_memory_choice(
    matrix_type: str,
    matrix_sram: Optional[Tuple[float, float]],
    matrix_3d: Optional[Tuple[float, float]],
    vector_sram: Optional[Tuple[float, float]],
    offchip_type: str,
    offchip_hbm: Optional[Tuple[float, float]],
    offchip_ddr: Optional[Tuple[float, float]],
    capacity_unit: str,
) -> Dict[str, Any]:
    matrix_entries: List[Dict[str, Any]] = []
    if matrix_type == "SRAM" and matrix_sram:
        cap_gb = _capacity_to_gb(matrix_sram[0], capacity_unit)
        bw = matrix_sram[1]
        matrix_entries.append({"memory_type": "sram", "capacity_gb": cap_gb, "bandwidth_gb_s": bw})
        sram_capacity_gb = cap_gb
        sram_bandwidth_gb_s = bw
    elif matrix_type == "3D_STACKED" and matrix_3d:
        cap_gb = _capacity_to_gb(matrix_3d[0], capacity_unit)
        bw = matrix_3d[1]
        matrix_entries.append({"memory_type": "3d_sram", "capacity_gb": cap_gb, "bandwidth_gb_s": bw})
        sram_capacity_gb = cap_gb
        sram_bandwidth_gb_s = bw
    elif matrix_type == "COMBINED" and matrix_sram and matrix_3d:
        cap_sram_gb = _capacity_to_gb(matrix_sram[0], capacity_unit)
        bw_sram = matrix_sram[1]
        cap_3d_gb = _capacity_to_gb(matrix_3d[0], capacity_unit)
        bw_3d = matrix_3d[1]
        matrix_entries.append({"memory_type": "sram", "capacity_gb": cap_sram_gb, "bandwidth_gb_s": bw_sram})
        matrix_entries.append({"memory_type": "3d_sram", "capacity_gb": cap_3d_gb, "bandwidth_gb_s": bw_3d})
        sram_capacity_gb = cap_sram_gb + cap_3d_gb
        sram_bandwidth_gb_s = max(bw_sram, bw_3d)
    else:
        sram_capacity_gb = 0.0
        sram_bandwidth_gb_s = 0.0

    vector_entry = None
    if vector_sram:
        cap_gb = _capacity_to_gb(vector_sram[0], capacity_unit)
        bw = vector_sram[1]
        vector_entry = {"memory_type": "sram", "capacity_gb": cap_gb, "bandwidth_gb_s": bw}

    offchip_entries: List[Dict[str, Any]] = []
    if offchip_type == "HBM" and offchip_hbm:
        cap_gb = _capacity_to_gb(offchip_hbm[0], capacity_unit)
        bw = offchip_hbm[1]
        offchip_entries.append({"memory_type": "hbm3", "capacity_gb": cap_gb, "bandwidth_gb_s": bw})
        hbm_capacity_gb = cap_gb
        hbm_bandwidth_gb_s = bw
    elif offchip_type == "DDR" and offchip_ddr:
        cap_gb = _capacity_to_gb(offchip_ddr[0], capacity_unit)
        bw = offchip_ddr[1]
        offchip_entries.append({"memory_type": "lpddr5", "capacity_gb": cap_gb, "bandwidth_gb_s": bw})
        hbm_capacity_gb = cap_gb
        hbm_bandwidth_gb_s = bw
    elif offchip_type == "COMBINED" and offchip_hbm and offchip_ddr:
        cap_hbm_gb = _capacity_to_gb(offchip_hbm[0], capacity_unit)
        bw_hbm = offchip_hbm[1]
        cap_ddr_gb = _capacity_to_gb(offchip_ddr[0], capacity_unit)
        bw_ddr = offchip_ddr[1]
        offchip_entries.append({"memory_type": "hbm3", "capacity_gb": cap_hbm_gb, "bandwidth_gb_s": bw_hbm})
        offchip_entries.append({"memory_type": "lpddr5", "capacity_gb": cap_ddr_gb, "bandwidth_gb_s": bw_ddr})
        hbm_capacity_gb = cap_hbm_gb + cap_ddr_gb
        hbm_bandwidth_gb_s = bw_hbm + bw_ddr
    else:
        hbm_capacity_gb = 0.0
        hbm_bandwidth_gb_s = 0.0

    memory_entries = _memory_entries_for_power_cost(matrix_entries, vector_entry, offchip_entries)
    sys_config = build_sys_config(
        sram_capacity_gb=sram_capacity_gb,
        sram_bandwidth_gb_s=sram_bandwidth_gb_s,
        hbm_capacity_gb=hbm_capacity_gb,
        hbm_bandwidth_gb_s=hbm_bandwidth_gb_s,
    )
    return {
        "matrix_type": matrix_type,
        "vector_sram": vector_sram,
        "offchip_type": offchip_type,
        "memory_entries": memory_entries,
        "sys_config": sys_config,
    }


def _generate_compute_candidates(design_space: Dict[str, Any], max_samples: int) -> List[Dict[str, int]]:
    compute = design_space["compute"]
    cores = _sample_range(compute.core_num_range or [compute.core_num], max_samples)
    blens = _sample_range(compute.blen_range or [compute.blen], max_samples)
    mlens = _sample_range(compute.mlen_range or [compute.mlen], max_samples)
    vlens = _sample_range(compute.vlen_range or [compute.vlen], max_samples)
    candidates = []
    for core_num in cores:
        for blen in blens:
            for mlen in mlens:
                for vlen in vlens:
                    candidates.append({"core_num": core_num, "blen": blen, "mlen": mlen, "vlen": vlen})
    return candidates


def _generate_execution_candidates(design_space: Dict[str, Any], max_samples: int) -> List[Dict[str, Any]]:
    ffn = design_space["ffn"]
    flash = design_space["flash_attention"]
    ffn_exec = ffn.execution_order.get("range", []) or [ffn.execution_order.get("type")]
    ffn_pri = ffn.on_chip_storage_priority.get("range", []) or [ffn.on_chip_storage_priority.get("type")]
    flash_exec = flash.execution_order.get("range", []) or [flash.execution_order.get("type")]
    flash_pri = flash.on_chip_storage_priority.get("range", []) or [flash.on_chip_storage_priority.get("type")]
    br_range = _sample_range(flash.soft_tiling_size.get("Br", {}).get("range", []) or [flash.soft_tiling_size.get("Br", {}).get("type")], max_samples)
    bc_range = _sample_range(flash.soft_tiling_size.get("Bc", {}).get("range", []) or [flash.soft_tiling_size.get("Bc", {}).get("type")], max_samples)
    candidates = []
    for fe in ffn_exec:
        for fp in ffn_pri:
            for he in flash_exec:
                for hp in flash_pri:
                    for br in br_range:
                        for bc in bc_range:
                            candidates.append(
                                {
                                    "ffn_execution_order": fe,
                                    "ffn_on_chip_storage_priority": fp,
                                    "flash_execution_order": he,
                                    "flash_on_chip_storage_priority": hp,
                                    "flash_soft_tiling_br": br,
                                    "flash_soft_tiling_bc": bc,
                                }
                            )
    return candidates


def _generate_memory_candidates(design_space: Dict[str, Any], max_samples: int, capacity_unit: str) -> List[Dict[str, Any]]:
    memory = design_space["memory"]
    matrix_types = memory.matrix_sram.type.range or [memory.matrix_sram.type.type]
    offchip_types = memory.off_chip_storage.type.range or [memory.off_chip_storage.type.type]

    matrix_sram_caps = _sample_range(memory.matrix_sram.sram.capacity_range or [memory.matrix_sram.sram.capacity_default], max_samples)
    matrix_sram_bws = _sample_range(memory.matrix_sram.sram.bandwidth_range or [memory.matrix_sram.sram.bandwidth_default], max_samples)
    matrix_3d_caps = _sample_range(memory.matrix_sram.stacked_3d.capacity_range or [memory.matrix_sram.stacked_3d.capacity_default], max_samples)
    matrix_3d_bws = _sample_range(memory.matrix_sram.stacked_3d.bandwidth_range or [memory.matrix_sram.stacked_3d.bandwidth_default], max_samples)

    vector_caps = _sample_range(memory.vector_sram.sram.capacity_range or [memory.vector_sram.sram.capacity_default], max_samples)
    vector_bws = _sample_range(memory.vector_sram.sram.bandwidth_range or [memory.vector_sram.sram.bandwidth_default], max_samples)

    hbm_caps = _sample_range(memory.off_chip_storage.hbm.capacity_range or [memory.off_chip_storage.hbm.capacity_default], max_samples)
    hbm_bws = _sample_range(memory.off_chip_storage.hbm.bandwidth_range or [memory.off_chip_storage.hbm.bandwidth_default], max_samples)
    ddr_caps = _sample_range(memory.off_chip_storage.ddr.capacity_range or [memory.off_chip_storage.ddr.capacity_default], max_samples)
    ddr_bws = _sample_range(memory.off_chip_storage.ddr.bandwidth_range or [memory.off_chip_storage.ddr.bandwidth_default], max_samples)

    candidates = []
    for matrix_type in matrix_types:
        if matrix_type == "SRAM":
            matrix_pairs = [(cap, bw) for cap in matrix_sram_caps for bw in matrix_sram_bws]
            matrix_3d_pairs = [None]
        elif matrix_type == "3D_STACKED":
            matrix_pairs = [None]
            matrix_3d_pairs = [(cap, bw) for cap in matrix_3d_caps for bw in matrix_3d_bws]
        else:  # COMBINED
            matrix_pairs = [(cap, bw) for cap in matrix_sram_caps for bw in matrix_sram_bws]
            matrix_3d_pairs = [(cap, bw) for cap in matrix_3d_caps for bw in matrix_3d_bws]

        for vector_cap in vector_caps:
            for vector_bw in vector_bws:
                vector_pair = (vector_cap, vector_bw)
                for offchip_type in offchip_types:
                    if offchip_type == "HBM":
                        offchip_pairs = [("HBM", (cap, bw), None) for cap in hbm_caps for bw in hbm_bws]
                    elif offchip_type == "DDR":
                        offchip_pairs = [("DDR", None, (cap, bw)) for cap in ddr_caps for bw in ddr_bws]
                    else:  # COMBINED
                        offchip_pairs = [
                            ("COMBINED", (cap_h, bw_h), (cap_d, bw_d))
                            for cap_h in hbm_caps for bw_h in hbm_bws
                            for cap_d in ddr_caps for bw_d in ddr_bws
                        ]

                    for matrix_pair in matrix_pairs:
                        for matrix_3d_pair in matrix_3d_pairs:
                            for offchip_type_sel, hbm_pair, ddr_pair in offchip_pairs:
                                candidates.append(
                                    _build_memory_choice(
                                        matrix_type=matrix_type,
                                        matrix_sram=matrix_pair,
                                        matrix_3d=matrix_3d_pair,
                                        vector_sram=vector_pair,
                                        offchip_type=offchip_type_sel,
                                        offchip_hbm=hbm_pair,
                                        offchip_ddr=ddr_pair,
                                        capacity_unit=capacity_unit,
                                    )
                                )
    return candidates


def search_best_configs(
    model_param_path: str,
    design_space_path: str,
    batch_size: int,
    seq_len: int,
    output_token: int,
    constraints: Optional[SearchConstraints] = None,
    options: Optional[SearchOptions] = None,
) -> Dict[str, Any]:
    constraints = constraints or SearchConstraints()
    options = options or SearchOptions()
    design_space = parse_toml_file(design_space_path)

    compute_candidates = _generate_compute_candidates(design_space, options.max_range_samples)
    memory_candidates = _generate_memory_candidates(design_space, options.max_range_samples, options.capacity_unit)
    exec_candidates = _generate_execution_candidates(design_space, options.max_range_samples)

    base_br = int(design_space["flash_attention"].soft_tiling_size.get("Br", {}).get("type", 8))
    base_bc = int(design_space["flash_attention"].soft_tiling_size.get("Bc", {}).get("type", 8))

    best_ttft = None
    best_tps = None
    pareto: List[Dict[str, Any]] = []
    evaluated = 0
    skipped_constraints = 0

    def meets_constraints(power_cost: Dict[str, Any]) -> bool:
        if constraints.max_power_w is not None:
            if power_cost["power"]["total_power_w"]["avg"] > constraints.max_power_w:
                return False
        if constraints.max_cost_usd is not None:
            if power_cost["cost"]["total_cost_usd"] > constraints.max_cost_usd:
                return False
        return True

    precomputed_mem = []
    for mem_choice in memory_candidates:
        power = estimate_power(mem_choice["memory_entries"])
        cost = estimate_cost(mem_choice["memory_entries"])
        power_cost = {"power": power, "cost": cost}
        if not meets_constraints(power_cost):
            skipped_constraints += 1
            continue
        mem_choice = {**mem_choice, **power_cost}
        precomputed_mem.append(mem_choice)

    for compute in compute_candidates:
        hardware_config = build_hardware_config(compute["blen"], compute["mlen"], compute["vlen"])
        device_num = int(compute["core_num"])

        for mem_prefill in precomputed_mem:
            mem_decode_list = precomputed_mem if options.allow_phase_specific_memory else [mem_prefill]
            for mem_decode in mem_decode_list:
                exec_prefill_list = exec_candidates
                exec_decode_list = exec_candidates if options.allow_phase_specific_execution else None
                for exec_prefill in exec_prefill_list:
                    decode_list = exec_decode_list or [exec_prefill]
                    for exec_decode in decode_list:
                        prefill_factor = _execution_factor(exec_prefill, base_br, base_bc)
                        decode_factor = _execution_factor(exec_decode, base_br, base_bc)

                        ttft, tps = compute_ttft_tps(
                            model_param_path=model_param_path,
                            hardware_config=hardware_config,
                            prefill_sys_config=mem_prefill["sys_config"],
                            decode_sys_config=mem_decode["sys_config"],
                            batch_size=batch_size,
                            seq_len=seq_len,
                            output_token=output_token,
                            device_num=device_num,
                            prefill_exec_factor=prefill_factor,
                            decode_exec_factor=decode_factor,
                        )

                        evaluated += 1
                        if evaluated >= options.max_evaluations:
                            break

                        record = {
                            "ttft_s": ttft,
                            "tps": tps,
                            "compute": compute,
                            "prefill_memory": mem_prefill,
                            "decode_memory": mem_decode,
                            "prefill_execution": exec_prefill,
                            "decode_execution": exec_decode,
                        }

                        if best_ttft is None or record["ttft_s"] < best_ttft["ttft_s"]:
                            best_ttft = record
                        if best_tps is None or record["tps"] > best_tps["tps"]:
                            best_tps = record

                        pareto.append(record)
                    if evaluated >= options.max_evaluations:
                        break
                if evaluated >= options.max_evaluations:
                    break
            if evaluated >= options.max_evaluations:
                break
        if evaluated >= options.max_evaluations:
            break

    pareto = _pareto_frontier(pareto)
    return {
        "best_ttft": best_ttft,
        "best_tps": best_tps,
        "pareto_frontier": pareto,
        "evaluated": evaluated,
        "skipped_constraints": skipped_constraints,
    }


def _pareto_frontier(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    frontier = []
    for candidate in records:
        dominated = False
        for other in records:
            if other is candidate:
                continue
            if other["ttft_s"] <= candidate["ttft_s"] and other["tps"] >= candidate["tps"]:
                if other["ttft_s"] < candidate["ttft_s"] or other["tps"] > candidate["tps"]:
                    dominated = True
                    break
        if not dominated:
            frontier.append(candidate)
    frontier.sort(key=lambda r: (r["ttft_s"], -r["tps"]))
    return frontier
