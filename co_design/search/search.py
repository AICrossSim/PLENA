import os
from typing import Dict, Any, Union
import concurrent.futures

import optuna

from ..interface.interface import get_accuracy, get_area, get_latency
from ..interface.utils import load_toml_config, write_active_config_to_toml


def is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0

def normalize_objective(val, min_val=0.0, max_val=15.0):
    norm = (val - min_val) / (max_val - min_val + 1e-8)
    return max(0.0, min(1.0, norm))

def denormalize_objective(val, min_val, max_val):
    return val * (max_val - min_val + 1e-8) + min_val


def objective(trial: optuna.Trial, tunables: Dict[str, Any], gpu_id: int):
    config = {}
    for key, values in tunables.items():
        if isinstance(values, list) and all(isinstance(v, int) for v in values):
            if sorted(values) == list(range(min(values), max(values) + 1)):
                config[key] = trial.suggest_int(key, min(values), max(values))
            else:
                config[key] = trial.suggest_categorical(key, values)
        else:
            config[key] = trial.suggest_categorical(key, values)

    # setting simple parameter constraints, precision related for now
    try:
        sum_wt = config["WT_MXFP_MANT_WIDTH"] + config["WT_MXFP_EXP_WIDTH"]+1
        sum_act = config["ACT_MXFP_MANT_WIDTH"] + config["ACT_MXFP_EXP_WIDTH"]+1
        sum_kv = config["KV_MXFP_MANT_WIDTH"] + config["KV_MXFP_EXP_WIDTH"]+1
    except KeyError as e:
        raise optuna.TrialPruned()  # Missing expected keys → prune

    if not (is_power_of_two(sum_wt) and is_power_of_two(sum_act) and is_power_of_two(sum_kv)):
        raise optuna.TrialPruned()

    write_active_config_to_toml(
        config_path="config/config.toml",
        updated_values=config,
        output_path="config/config_sampled.toml"
    )

    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    accuracy, latency, area = run_simulation()
    # TODO: Figure out maximums
    accuracy = normalize_objective(accuracy, min_val=9, max_val=128256.0)
    latency = normalize_objective(latency, min_val=0.0, max_val=15.0)
    area = normalize_objective(area, min_val=2000.0, max_val=2183520)
    return accuracy, latency, area


def run_simulation():
    latency = get_latency()
    area = get_area()
    accuracy = get_accuracy()
    return accuracy, latency, area


def trial_worker(trial_index: int, tunables: Dict[str, Any], study_name: str, storage: str, num_gpus: int):
    import os
    gpu_id = trial_index % num_gpus
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    study = optuna.load_study(study_name=study_name, storage=storage)
    study.optimize(lambda trial: objective(trial, tunables, gpu_id=gpu_id), n_trials=1)


def search(
    config_path: str = "config/config.toml",
    n_trials: int = 300,
    visualize: bool = True,
    sampler_type: Union[str, None] = "botorch",
    num_gpus: int = 6,
    trials_per_gpu: int = 1,
):
    tunables = load_toml_config(config_path, mode="tunable_range")
    print(f"[INFO] Loaded {len(tunables)} tunable parameters.")

    storage = "sqlite:///optuna_study_with_bo.db"
    study_name = "search_bo_with_obj_normalization"

    if sampler_type == "botorch":
        from optuna.integration.botorch import BoTorchSampler
        sampler = BoTorchSampler()
    else:
        sampler = optuna.samplers.TPESampler()

    optuna.create_study(
        # TODO: Check the scaling of the objectives [0,1] [-1,1]
        # TODO: Confrim the weights related to the objectives
        directions=["minimize", "minimize", "minimize"],
        study_name=study_name,
        sampler=sampler,
        storage=storage,
        load_if_exists=True,
    )

    max_workers = num_gpus * trials_per_gpu
    print(f"[INFO] Launching {n_trials} trials across {max_workers} workers.")

    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    trial_worker, i, tunables, study_name, storage, num_gpus
                )
                for i in range(n_trials)
            ]
            # Wait for all to complete
            for future in concurrent.futures.as_completed(futures):
                future.result()
    except KeyboardInterrupt:
        print("\n[INFO] Caught KeyboardInterrupt, cancelling all jobs...")
        executor.shutdown(wait=False, cancel_futures=True)
        raise

    study = optuna.load_study(study_name=study_name, storage=storage)
    print(f"[INFO] Number of Pareto-optimal trials: {len(study.best_trials)}")

    all_trials = study.get_trials(deepcopy=False)
    complete_trials = [t for t in all_trials if t.state == optuna.trial.TrialState.COMPLETE]
    print(f"[INFO] Number of successfully completed (non-pruned) trials: {len(complete_trials)}")

    for i, trial in enumerate(study.best_trials):
        acc_norm, lat_norm, area_norm = trial.values
        acc = denormalize_objective(acc_norm, 9, 128256.0)
        lat = denormalize_objective(lat_norm, 0.0, 15.0)
        area = denormalize_objective(area_norm, 2000.0, 2183520.0)

        print(f"\n[Trial {i}]")
        print(f"  Normalized Objectives: accuracy={acc_norm:.4f}, latency={lat_norm:.4f}, area={area_norm:.4f}")
        print(f"  Denormalized Objectives: accuracy={acc:.2f}, latency={lat:.4f}, area={area:.2f}")
        print("  Parameters:")
        for key, value in trial.params.items():
            print(f"    {key}: {value}")

    if visualize:
        fig = optuna.visualization.plot_pareto_front(study)
        fig.write_html("pareto_front.html")
        print("[INFO] Saved interactive plot to pareto_front.html")
# TODO:

if __name__ == "__main__":
    import time
    from jsonargparse import CLI

    start_time = time.time()
    CLI(search)
    print(f"\n[INFO] Total search workload time: {time.time() - start_time:.2f} seconds")