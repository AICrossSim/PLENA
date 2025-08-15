import os
from pathlib import Path
from typing import Dict, Any, Union
import concurrent.futures

import optuna
from optuna.samplers import RandomSampler, TPESampler
from optuna.integration.botorch import BoTorchSampler

from ..interface.interface import get_accuracy, get_area, get_latency
from ..interface.utils import load_toml_config, write_active_config_to_toml, get_bit_width
from .utils import is_power_of_two, normalize_objective, post_search


LAT_MIN, LAT_MAX = 0, 2
AREA_MIN, AREA_MAX = 0, 169718611.76

def objective(trial: optuna.Trial, tunables: Dict[str, Any], gpu_id: int, set_constraints: bool = True, normalize: bool = False) -> tuple[float, float, float]:
    config = {}

    for key, values in tunables.items():
        if isinstance(values, list) and all(isinstance(v, int) for v in values):
            if sorted(values) == list(range(min(values), max(values) + 1)):
                config[key] = trial.suggest_int(key, min(values), max(values))
            else:
                config[key] = trial.suggest_categorical(key, values)
        else:
            config[key] = trial.suggest_categorical(key, values)
    
    # Patch the hw config with the total bit widths, while keeping the original config for accuracy config
    config_acc = config.copy()
    config_hw = config.copy()
    config_hw["ACT_ELEMENT_WIDTH"] = get_bit_width(config["ACT_ELEMENT_WIDTH"])
    config_hw["KV_ELEMENT_WIDTH"] = get_bit_width(config["KV_ELEMENT_WIDTH"])
    # setting simple parameter constraints, precision related for now
    # TODO: add more constraints here
    try:
        sum_nl = config["FP_EXP_WIDTH"] + config["FP_MANT_WIDTH"]+1
    except KeyError as e:
        raise optuna.TrialPruned()  # Missing expected keys → prune

    if not (is_power_of_two(sum_nl) and sum_nl <= 16):
        raise optuna.TrialPruned()

    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)

    # Now the simulator shoudld takes in the config dictionary instead of mnanually reading from the file paths
    accuracy, latency, area = run_simulation(config_hw, config_acc, model_name="meta-llama/Llama-3.2-1B")

    if set_constraints:
        # store raw metrics for constraints_func
        trial.set_user_attr("accuracy_raw", accuracy)
        trial.set_user_attr("latency_raw", latency)
        trial.set_user_attr("area_raw", area)

    if normalize:
        # TODO: Figure out maximums
        accuracy = normalize_objective(accuracy, min_val=9, max_val=128256.0)
        latency = normalize_objective(latency, min_val=0.0, max_val=15.0)
        area = normalize_objective(area, min_val=2000.0, max_val=2183520)
    return accuracy, latency, area

def constraints_func(trial: optuna.Trial):
    c_acc = (trial.user_attrs["accuracy_raw"] - 9) / (128256.0 - 9)
    c_lat = (trial.user_attrs["latency_raw"] - 0.1) / 0.1
    c_area = (trial.user_attrs["area_raw"] - 1_000_000) / 1_000_000
    return [c_acc, c_lat, c_area]


def run_simulation(config_hw: Dict[str, Any], 
                   config_acc: Dict[str, Any], 
                   model_name: str = "meta-llama/Llama-3.2-1B"):
    latency = get_latency(config_dict=config_hw, model_name=model_name)
    area = get_area(config_dict=config_hw)
    accuracy = get_accuracy(config_dict=config_acc, model_name=model_name)
    return accuracy, latency, area


def trial_worker(trial_index: int, tunables: Dict[str, Any], study_name: str, storage: str, num_gpus: int, set_constraints: bool = False):
    gpu_id = trial_index % num_gpus
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    study = optuna.load_study(study_name=study_name, storage=storage)
    study.optimize(lambda trial: objective(trial, tunables, gpu_id=gpu_id, set_constraints=set_constraints), n_trials=1)


def search(
    config_path: str = "src/definitions/config.toml",
    n_trials: int = 300,
    visualize: bool = False,
    sampler_type: Union[str, None] = "botorch",
    num_gpus: int = 8,
    trials_per_gpu: int = 1,
    normalize: bool = False,
    set_constraints: bool = False,
    parallel: bool = True
):
    tunables = load_toml_config(config_path, mode="tunable_range")
    print(f"[INFO] Loaded {len(tunables)} tunable parameters.")

    study_name = f"{sampler_type}_search"
    db_path = Path("co_design") / f"{study_name}.db"
    storage = f"sqlite:///{db_path.resolve()}"


    if sampler_type == "botorch":
        sampler = BoTorchSampler()
    elif sampler_type == "tpe":
        sampler = TPESampler()
    elif sampler_type == "random":
        sampler = RandomSampler()
    else:
        raise ValueError(f"Unknown sampler type: {sampler_type}")

    optuna.create_study(
        # TODO: Check the scaling of the objectives [0,1] [-1,1]
        directions=["minimize", "minimize", "minimize"],
        study_name=study_name,
        sampler=sampler,
        storage=storage,
        load_if_exists=True,
    )

    max_workers = num_gpus * trials_per_gpu
    print(f"[INFO] Launching {n_trials} trials across {max_workers} workers.")
    if parallel:
        # -------- Parallel Execution --------
        max_workers = num_gpus * trials_per_gpu
        print(f"[INFO] Launching {n_trials} trials across {max_workers} workers.")

        try:
            with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(
                        trial_worker, i, tunables, study_name, storage, num_gpus, set_constraints
                    )
                    for i in range(n_trials)
                ]
                for future in concurrent.futures.as_completed(futures):
                    future.result()
        except KeyboardInterrupt:
            print("\n[INFO] Caught KeyboardInterrupt, cancelling all jobs...")
            executor.shutdown(wait=False, cancel_futures=True)
            raise
    else:
        # -------- Sequential Execution --------
        study = optuna.load_study(study_name=study_name, storage=storage)
        for i in range(n_trials):
            gpu_id = i % num_gpus
            study.optimize(lambda trial: objective(trial, tunables, gpu_id, set_constraints),
                           n_trials=1)
            
    post_search(study_name, storage, normalize=normalize, visualize=visualize)

if __name__ == "__main__":
    import time
    from jsonargparse import CLI

    start_time = time.time()
    CLI(search)
    print(f"\n[INFO] Total search workload time: {time.time() - start_time:.2f} seconds")