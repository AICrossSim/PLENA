# Search Module

The search module (`co_design/search/`) implements multi-objective Bayesian optimization for hardware design space exploration.

## Module Overview

```
co_design/search/
├── search.py      # Main search orchestration
├── utils.py       # Search utilities
└── patch_bo.py    # Custom BoTorch kernel
```

## Core Functions

### `search()`

Main entry point for optimization.

```python
def search(
    config_path: str,
    sampler: str = "botorch",
    n_trials: int = 100,
    n_jobs: int = 1,
    seed: int = 42
) -> optuna.Study:
    """
    Run multi-objective optimization search.

    Args:
        config_path: Path to configuration TOML file
        sampler: Optimization algorithm ("botorch", "tpe", "nsga2", "random")
        n_trials: Number of optimization trials
        n_jobs: Number of parallel workers
        seed: Random seed for reproducibility

    Returns:
        Optuna study object with results
    """
```

**Usage:**
```bash
python -m co_design.search.search \
    --config co_design/configs/config.toml \
    --sampler botorch \
    --n_trials 100
```

---

### `objective()`

Multi-objective function for optimization.

```python
def objective(trial: optuna.Trial, config: dict) -> Tuple[float, float, float]:
    """
    Evaluate a single configuration.

    Args:
        trial: Optuna trial object
        config: Base configuration

    Returns:
        Tuple of (accuracy, latency, area)

    Note:
        - Accuracy is maximized (returned as negative for minimization)
        - Latency and area are minimized
    """
```

---

### `run_simulation()`

Executes evaluation on proposed configurations.

```python
def run_simulation(config: dict) -> dict:
    """
    Run hardware simulation for a configuration.

    Args:
        config: Complete hardware + precision configuration

    Returns:
        Dictionary with metrics:
        {
            "accuracy": float,
            "latency": float,
            "area": float
        }
    """
```

---

### `trial_worker()`

Parallel trial execution support.

```python
def trial_worker(
    study: optuna.Study,
    objective_func: Callable,
    n_trials: int
) -> None:
    """
    Worker function for parallel optimization.

    Args:
        study: Shared Optuna study
        objective_func: Objective function to optimize
        n_trials: Number of trials for this worker
    """
```

## Utility Functions

### `check_constraints()`

Validates hardware constraints.

```python
def check_constraints(config: dict) -> bool:
    """
    Check if configuration satisfies all hardware constraints.

    Args:
        config: Hardware configuration

    Returns:
        True if valid, False otherwise

    Checks:
        - MLEN >= BLEN
        - MLEN % BLEN == 0
        - SRAM depth requirements
        - HBM prefetch constraints
        - Precision bit width constraints
    """
```

---

### `normalize_objective()`

Normalizes objectives for multi-objective optimization.

```python
def normalize_objective(
    values: Tuple[float, float, float],
    bounds: dict
) -> Tuple[float, float, float]:
    """
    Normalize objective values to [0, 1] range.

    Args:
        values: Raw (accuracy, latency, area) tuple
        bounds: Min/max bounds for each objective

    Returns:
        Normalized objective tuple
    """
```

---

### `post_search()`

Analyzes and visualizes Pareto-optimal solutions.

```python
def post_search(study: optuna.Study, output_dir: str) -> List[dict]:
    """
    Post-process optimization results.

    Args:
        study: Completed Optuna study
        output_dir: Directory for output files

    Returns:
        List of Pareto-optimal configurations

    Outputs:
        - pareto_front.png: Visualization of Pareto front
        - pareto_configs.json: Optimal configurations
        - optimization_history.csv: Trial history
    """
```

---

### `append_from_random()`

Warm-starts optimization with random samples.

```python
def append_from_random(
    study: optuna.Study,
    config: dict,
    n_samples: int = 10
) -> None:
    """
    Add random samples to study for warm-start.

    Args:
        study: Optuna study to populate
        config: Configuration with tunable ranges
        n_samples: Number of random samples to add
    """
```

## Supported Samplers

| Sampler | Class | Description |
|---------|-------|-------------|
| `botorch` | `BoTorchSampler` | Bayesian optimization with Gaussian Processes |
| `tpe` | `TPESampler` | Tree-structured Parzen Estimator |
| `nsga2` | `NSGAIISampler` | Non-dominated Sorting Genetic Algorithm II |
| `random` | `RandomSampler` | Uniform random sampling |
