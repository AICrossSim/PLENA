import os
from pathlib import Path
from typing import Dict, Any, Union
import concurrent.futures

import optuna
from optuna.samplers import RandomSampler, TPESampler, NSGAIISampler
from optuna.integration.botorch import BoTorchSampler

from ..interface.interface import get_accuracy, get_area, get_latency
from ..interface.utils import load_toml_config, get_bit_width
from .utils import normalize_objective, post_search, check_constraints, reset_study_and_db, append_from_random


def objective(
    trial: optuna.Trial,
    tunables: Dict[str, Any],
    set_constraints: bool = True,
    normalize: bool = False,
    model_name: str | None = None,
    model_flag: int =8,
) -> tuple[float, float, float]:
    
    config: Dict[str, Any] = {}

    # Suggest values
    for key, values in tunables.items():
        if isinstance(values, list) and all(isinstance(v, int) for v in values):
            if sorted(values) == list(range(min(values), max(values) + 1)):
                config[key] = trial.suggest_int(key, min(values), max(values))
            else:
                config[key] = trial.suggest_categorical(key, values)
        else:
            config[key] = trial.suggest_categorical(key, values)

    # Patch HW config with bit-width totals; keep the original for accuracy
    config_acc = dict(config)
    config_hw = dict(config)
    config_hw["ACT_ELEMENT_WIDTH"] = get_bit_width(config["ACT_ELEMENT_WIDTH"])
    config_hw["KV_ELEMENT_WIDTH"] = get_bit_width(config["KV_ELEMENT_WIDTH"])
    config_hw["FP_EXP_WIDTH"], config_hw["FP_MANT_WIDTH"] = get_bit_width(config["FP_SETTING"])

    valid, tmp_for_print = check_constraints(config_hw, model_name=model_name)
    if not valid:
        print(tmp_for_print)
        raise optuna.TrialPruned()
    print()

    # Run your simulator
    accuracy, latency, area = run_simulation(config_hw, config_acc, model_name=model_name)

    # Store raw for constraints
    if set_constraints:
        trial.set_user_attr("accuracy_raw", accuracy)
        trial.set_user_attr("latency_raw", latency)
        trial.set_user_attr("area_raw", area)

    if model_flag == 8:
        ACC_MIN, ACC_MAX = 5, 20
    elif model_flag == 1:
        ACC_MIN, ACC_MAX = 9, 20
    LAT_MIN, LAT_MAX = 0, 10
    AREA_MIN, AREA_MAX = 120246991, 500000000
    # Optional normalization
    if normalize:
        accuracy = normalize_objective(accuracy, min_val=ACC_MIN, max_val=ACC_MAX)
        latency = normalize_objective(latency, min_val=LAT_MIN, max_val=LAT_MAX)
        area = normalize_objective(area, min_val=AREA_MIN, max_val=AREA_MAX)

    return accuracy, latency, area


def constraints_func(trial: optuna.Trial):
    c_acc = (trial.user_attrs["accuracy_raw"] - 9) / (128256.0 - 9)
    c_lat = (trial.user_attrs["latency_raw"] - 0.1) / 0.1
    c_area = (trial.user_attrs["area_raw"] - 1_000_000) / 1_000_000
    return [c_acc, c_lat, c_area]


def run_simulation(
    config_hw: Dict[str, Any],
    config_acc: Dict[str, Any],
    model_name: str = "meta-llama/Llama-3.2-1B",
    model_flag: int = None
):
    latency = get_latency(config_dict=config_hw, model_name=model_name)
    area = get_area(config_dict=config_hw)
    accuracy = get_accuracy(config_dict=config_acc, model_name=model_name, model_flag = model_flag)
    return accuracy, latency, area


def trial_worker(
    trial_index: int,
    tunables: Dict[str, Any],
    study_name: str,
    storage: str,
    num_gpus: int,
    set_constraints: bool = False,
    model_name: str | None = None,
    normalize: bool = False,
    model_flag: int = None
):
    gpu_id = trial_index % num_gpus
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    study = optuna.load_study(study_name=study_name, storage=storage)

    study.optimize(
        lambda trial: objective(
            trial,
            tunables,
            gpu_id=gpu_id,
            set_constraints=set_constraints,
            model_name=model_name,
            normalize=normalize,
            model_flag=model_flag
        ),
        n_trials=1,
    )


def search(
    model_name: str = "meta-llama/Meta-Llama-3-8B",
    config_path: str = "src/definitions/config.toml",
    n_trials: int = 80,
    visualize: bool = False,
    sampler_type: Union[str, None] = "botorch",
    num_gpus: int = 8,                 # ignored for parallel=False single-GPU run
    trials_per_gpu: int = 1,           # ignored for parallel=False
    normalize: bool = True,
    set_constraints: bool = False,
    parallel: bool = False,
    seed: int = 42,
    restart_study: bool = True,
    gpu_id: int =0,
    study_name: str = None,
    model_flag: int = 8,
):
    # --- Pin all work to a single GPU once ---
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)

    tunables = load_toml_config(config_path, mode="tunable_range")
    print(f"[INFO] Loaded {len(tunables)} tunable parameters.")

    if model_flag == 8:
        model_name = "meta-llama/Meta-Llama-3-8B"
    elif model_flag == 1:
        model_name = "meta-llama/Llama-3.2-1B"
    print(model_flag)
    print(model_name)
    random_study_name = f"Random_{seed}_{model_flag}b"
    random_db_path = Path("co_design") / f"db_{seed}_{model_flag}b" / f"{random_study_name}.db"
    random_storage = f"sqlite:///{random_db_path.resolve()}"

    if not study_name:
        study_name = f"{sampler_type}_search_with_area"
    db_path = Path("co_design") / f"db_{seed}_{model_flag}b" / f"{study_name}.db"
    storage = f"sqlite:///{db_path.resolve()}"

    # Sampler
    if sampler_type == "botorch":
        sampler = BoTorchSampler(seed=seed, consider_running_trials=True)
    elif sampler_type == "tpe":
        sampler = TPESampler(seed=seed)
    elif sampler_type == "random":
        sampler = RandomSampler(seed=seed)
    elif sampler_type == "ns":
        sampler = NSGAIISampler(seed=seed)
    else:
        raise ValueError(f"Unknown sampler type: {sampler_type}")
    print(sampler)

    if restart_study:
        reset_study_and_db(study_name, storage)
        load_if_exists = False
    else:
        load_if_exists = True

    study = optuna.create_study(
        directions=["minimize", "minimize", "minimize"],
        study_name=study_name,
        sampler=sampler,
        storage=storage,
        load_if_exists=load_if_exists,
    )

    if sampler_type != "random" and restart_study:
        append_from_random(
            random_storage=random_storage,
            random_study_name=random_study_name,
            target_study=study,
            tunables=tunables,
            n=10,
        )
    print("Validating", study.sampler)

    # --- Sequential (single GPU, single node) ---
    if not parallel:
        print(f"[INFO] Launching {n_trials} trials sequentially on GPU {gpu_id}.")
        for _ in range(n_trials):
            study.optimize(
                lambda trial: objective(
                    trial,
                    tunables,
                    set_constraints,
                    normalize=normalize,
                    model_name=model_name,
                ),
                n_trials=1,
            )
            print(study.sampler)
    else:
        try:
            max_workers = 1
            with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(
                        trial_worker,
                        i,
                        tunables,
                        study_name,
                        storage,
                        num_gpus,
                        set_constraints,
                        model_name,
                        normalize,
                        model_flag=model_flag
                    )
                    for i in range(n_trials)
                ]
                for future in concurrent.futures.as_completed(futures):
                    future.result()
        except KeyboardInterrupt:
            print("\n[INFO] Caught KeyboardInterrupt, cancelling all jobs...")
            executor.shutdown(wait=False, cancel_futures=True)
            raise
 
    post_search(study_name, storage, normalize=normalize, visualize=visualize, model_flag=model_flag)


if __name__ == "__main__":
    import time
    from jsonargparse import CLI

    start_time = time.time()
    CLI(search)
    print(f"\n[INFO] Total search workload time: {time.time() - start_time:.2f} seconds")
