# Getting Started

This guide will help you set up and run PLENA for hardware-software co-design optimization.

## Prerequisites

- Python 3.8+
- CUDA-compatible GPU (for simulator)
- Git (for submodules)

## Installation

### 1. Clone the Repository

```bash
git clone --recursive https://github.com/your-org/PLENA.git
cd PLENA
```

!!! note
    The `--recursive` flag is required to fetch the RTL and Simulator submodules.

### 2. Install Python Dependencies

```bash
pip install -e .
```

This installs the following key dependencies:

- `optuna` - Hyperparameter optimization framework
- `botorch` - Bayesian optimization library
- `toml` - Configuration file parsing
- `jsonargparse` - CLI argument parsing

### 3. Initialize Submodules (if needed)

```bash
git submodule update --init --recursive
```

## Running Your First Optimization

### Basic Usage

```bash
python -m co_design.search.search --config co_design/configs/config.toml
```

### Configuration Options

The main configuration file `co_design/configs/config.toml` contains:

| Section | Description |
|---------|-------------|
| `CONFIG` | Hardware parameters (BLEN, MLEN, VLEN) |
| `PRECISION` | Element widths and FP formats |
| `INSTR` | Instruction parameters |

### Optimization Samplers

PLENA supports multiple optimization algorithms:

```bash
# BoTorch (default - Bayesian optimization)
python -m co_design.search.search --sampler botorch

# TPE (Tree-structured Parzen Estimator)
python -m co_design.search.search --sampler tpe

# NSGA-II (Multi-objective evolutionary algorithm)
python -m co_design.search.search --sampler nsga2

# Random baseline
python -m co_design.search.search --sampler random
```

## Understanding the Output

After optimization completes, you'll receive:

1. **Pareto-optimal solutions** - Configurations that represent the best trade-offs
2. **Metrics visualization** - Plots showing accuracy vs latency vs area
3. **Configuration files** - Optimal settings ready for deployment

## Next Steps

- [Architecture Overview](architecture.md) - Understand the system design
- [Configuration Reference](configuration.md) - Detailed parameter documentation
- [Hardware Constraints](constraints.md) - Design space limitations
