# Architecture Overview

PLENA follows a modular architecture designed for hardware-software co-design optimization.

![System Architecture](PLENA_Sys.png)

## System Components

### 1. Co-Design Module (`co_design/`)

The core optimization framework consists of three main components:

#### Interface Layer (`co_design/interface/`)

Abstracts hardware and simulator interactions for cost modeling:

- **`interface.py`** - High-level functions for querying hardware metrics
    - `get_area()` - Resource utilization using the utilisation model
    - `get_latency()` - Overall latency computation for LLM inference
    - `get_accuracy()` - Accuracy evaluation via simulator

- **`utils.py`** - Configuration parsing utilities
    - `parse_precision_config()` - Extract precision settings from TOML
    - `get_bit_width()` - Convert format strings (MXFP, MXINT, FP) to bit widths
    - `write_active_config_to_toml()` - Persist configuration changes

#### Search Engine (`co_design/search/`)

Multi-objective Bayesian optimization for hardware design:

- **`search.py`** - Main search orchestration
    - `objective()` - Multi-objective function (accuracy, latency, area)
    - `search()` - Entry point supporting BoTorch, TPE, NSGA-II, Random samplers
    - `trial_worker()` - Parallel trial execution

- **`utils.py`** - Search utilities
    - `check_constraints()` - Hardware constraint validation
    - `normalize_objective()` - Objective normalization for multi-objective optimization
    - `post_search()` - Pareto-optimal solution analysis

### 2. RTL Module (`PLENA_RTL/`)

SystemVerilog hardware design (git submodule):

- Hardware configuration definitions (`src/definitions/configuration.svh`)
- Precision settings (`src/definitions/precision.svh`)
- Cost models (`tools/cost_model/`)

### 3. Simulator Module (`PLENA_Simulator/`)

Hardware simulation framework (git submodule):

- LLaMA model evaluation (`acc_simulator/cli/acc_sim.py`)
- Accuracy benchmarking for various precision configurations

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Configuration (TOML)                      │
│         Hardware params, Precision, Instructions             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Optuna Optimization Loop                    │
│  ┌─────────┐   ┌─────────────┐   ┌──────────────────────┐   │
│  │ Sample  │──▶│  Validate   │──▶│  Run Simulator       │   │
│  │ Params  │   │ Constraints │   │  (accuracy, latency) │   │
│  └─────────┘   └─────────────┘   └──────────────────────┘   │
│       ▲                                      │               │
│       │              ┌───────────────────────┘               │
│       │              ▼                                       │
│  ┌─────────────────────────────────────┐                    │
│  │  Normalize & Update Pareto Front    │                    │
│  └─────────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Pareto-Optimal Solutions                        │
│    Configurations with best accuracy/latency/area tradeoffs │
└─────────────────────────────────────────────────────────────┘
```

## Optimization Objectives

PLENA optimizes three objectives simultaneously:

| Objective | Description | Source |
|-----------|-------------|--------|
| **Accuracy** | Model accuracy on evaluation tasks | Simulator |
| **Latency** | End-to-end inference time | Latency cost model |
| **Area** | Hardware resource utilization | Utilisation model |

## Supported Samplers

| Sampler | Algorithm | Best For |
|---------|-----------|----------|
| `botorch` | Bayesian Optimization | Sample-efficient exploration |
| `tpe` | Tree-structured Parzen Estimator | High-dimensional spaces |
| `nsga2` | NSGA-II | Multi-objective evolutionary search |
| `random` | Random Search | Baseline comparison |
