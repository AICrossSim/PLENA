import optuna


def is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0

def normalize_objective(val, min_val, max_val, sym=True):
    """
    Normalize an objective value to either:
    - [0, 1]   if sym=False
    - [-1, 1]  if sym=True
    With Clipping.
    """
    if not sym:
        norm = (val - min_val) / (max_val - min_val + 1e-8)
        return max(0.0, min(1.0, norm))
    else:
        norm = 2 * (val - min_val) / (max_val - min_val + 1e-8) - 1
        return max(-1.0, min(1.0, norm))

def denormalize_objective(val, min_val, max_val, sym=True):
    """
    Denormalize an objective value from normalized space back to original scale.
    """
    if not sym:
        return val * (max_val - min_val + 1e-8) + min_val
    else:
        return (val + 1) / 2 * (max_val - min_val + 1e-8) + min_val

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
        if normalize:
            acc_norm, lat_norm, area_norm = trial.values
            acc = denormalize_objective(acc_norm, 9, 128256.0)
            lat = denormalize_objective(lat_norm, 0.0, 15.0)
            area = denormalize_objective(area_norm, 2000.0, 2183520.0)
        else:
            acc, lat, area = trial.values

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