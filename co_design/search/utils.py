import optuna
import re
from pathlib import Path
import numpy as np

from ...tools.utils import load_svh_settings

def is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def log_scale(val):
    """Log scaling function: log10(1+x)."""
    return np.log1p(val) / np.log(10)

def normalize_objective(val, min_val, max_val, sym=True, use_log=False):
    """
    Normalize an objective value with optional log scaling.
    """
    if use_log:
        val = log_scale(val)
        min_val = log_scale(min_val)
        max_val = log_scale(max_val)

    if not sym:
        norm = (val - min_val) / (max_val - min_val + 1e-8)
        return max(0.0, min(1.0, norm))
    else:
        norm = 2 * (val - min_val) / (max_val - min_val + 1e-8) - 1
        return max(-1.0, min(1.0, norm))

def denormalize_objective(val, min_val, max_val, sym=True, use_log=False):
    """
    Denormalize an objective value from normalized space back to original scale.
    Inverse of normalize_objective (approximate if log scaling applied).
    """
    if use_log:
        min_val = log_scale(min_val)
        max_val = log_scale(max_val)

    if not sym:
        raw = val * (max_val - min_val + 1e-8) + min_val
    else:
        raw = (val + 1) / 2 * (max_val - min_val + 1e-8) + min_val

    if use_log:
        # Inverse of log_scale: x = 10^raw - 1
        return np.power(10, raw) - 1
    return raw


def post_search(study_name, 
                storage, 
                normalize: bool = False, 
                visualize: bool = False):
    # Print the number of Pareto-optimal trials
    study = optuna.load_study(study_name=study_name, storage=storage)
    print(f"[INFO] Number of Pareto-optimal trials: {len(study.best_trials)}")

    all_trials = study.get_trials(deepcopy=False)
    complete_trials = [t for t in all_trials if t.state == optuna.trial.TrialState.COMPLETE]
    print(f"[INFO] Number of successfully completed (non-pruned) trials: {len(complete_trials)}")

    for i, trial in enumerate(study.best_trials):
        # print(trail.value)
        if normalize:
            ACC_MIN, ACC_MAX = 9, 20
            LAT_MIN, LAT_MAX = 0, 10
            AREA_MIN, AREA_MAX = 120246991, 500000000
            acc_norm, lat_norm, area_norm = trial.values
            acc = denormalize_objective(acc_norm, ACC_MIN, ACC_MAX)
            lat = denormalize_objective(lat_norm, LAT_MIN, LAT_MAX)
            area = denormalize_objective(area_norm, AREA_MIN, AREA_MAX)
        else:
            acc, lat, area = trial.values

        print(f"\n[Trial {i}]")
        print(f"  Normalized Objectives: accuracy={acc_norm:.4f}, latency={lat_norm:.4f}, area={area_norm:.4f}")
        print(f"  Denormalized Objectives: accuracy={acc:.2f}, latency={lat:.4f}, area={area:.2f}")
        # print(f"  Normalized Objectives: accuracy={acc_norm:.4f}, latency={lat_norm:.4f}")
        # print(f"  Denormalized Objectives: accuracy={acc:.2f}, latency={lat:.4f}")
        print("  Parameters:")
        for key, value in trial.params.items():
            print(f"    {key}: {value}")

    if visualize:
        fig = optuna.visualization.plot_pareto_front(study)
        fig.write_html("pareto_front.html")
        print("[INFO] Saved interactive plot to pareto_front.html")


def reset_study_and_db(study_name: str, storage: str):
    """Delete Optuna study and its SQLite DB file if present."""
    try:
        optuna.delete_study(study_name=study_name, storage=storage)
    except Exception:
        pass

    m = re.match(r"^sqlite:///(.+)$", storage)
    if m:
        db_file = Path(m.group(1))
        for suffix in ["", "-wal", "-shm", "-journal"]:
            f = Path(str(db_file) + suffix)
            if f.exists():
                f.unlink()


def check_constraints(updated_config: dict, model_name) -> bool:
    """Return True if all constraints are satisfied, else False."""

    if model_name == "meta-llama/Llama-3.2-1B":
        HEAD_DIM = 64
        HIDDEN_DIM = 2048
    elif model_name == "meta-llama/Meta-Llama-3-8B":
        HEAD_DIM = 128
        HIDDEN_DIM = 4096
    else:
        raise ValueError(f"Unsupported model name: {model_name}")
    
    CONFIG_PATH     = "src/definitions/configuration.svh"
    PRECISION_PATH  = "src/definitions/precision.svh"

    config_settings = load_svh_settings(CONFIG_PATH)
    precision_settings = load_svh_settings(PRECISION_PATH)

    hardware_settings = {**config_settings, **precision_settings}
    precision_settings = load_svh_settings("src/definitions/precision.svh")
    for key, value in updated_config.items():
            hardware_settings[key] = value
    cfg = hardware_settings

    # precision constraints
    sum_nl = cfg["FP_EXP_WIDTH"] + cfg["FP_MANT_WIDTH"] + 1
    if not (  sum_nl <= 16):
        return False, "Precision constraint failed: sum_nl must be power of two and <= 16"

    # hardware constraints
    if not (cfg["MLEN"] >= cfg["BLEN"]):
        return False, "MLEN must be >= BLEN"
    if not (cfg["MLEN"] % cfg["BLEN"] == 0):
        return False, "MLEN must be divisible by BLEN"
    if not (cfg["MATRIX_SRAM_DEPTH"] >= 2 * cfg["MLEN"]):
        return False, "MATRIX_SRAM_DEPTH must be >= 2 * MLEN"
    if not (cfg["VECTOR_SRAM_DEPTH"] >= 2 * HEAD_DIM + (HIDDEN_DIM // cfg["VLEN"])):
        return False, "VECTOR_SRAM_DEPTH must be >= 2*HEAD_DIM + (HIDDEN_DIM // VLEN)"
    if not (cfg["FP_SRAM_DEPTH"] >= cfg["MLEN"] + 4):
        return False, "FP_SRAM_DEPTH must be >= MLEN + 4"
    if not ((cfg["MLEN"] * cfg["ACT_ELEMENT_WIDTH"] +
             (cfg["MLEN"] // cfg["BLOCK_DIM"]) * cfg["MX_SCALE_WIDTH"]) < 1510):
        return False, "MLEN bandwidth constraint failed"
    if not ((cfg["VLEN"] * cfg["ACT_ELEMENT_WIDTH"] +
             (cfg["VLEN"] // cfg["BLOCK_DIM"]) * cfg["MX_SCALE_WIDTH"]) < 1510):
        return False, "VLEN bandwidth constraint failed"

    return True, None
