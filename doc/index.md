# PLENA: A Programmable Long-context Efficient Neural Accelerator

![PLENA System Architecture](PLENA_Sys.png)

**PLENA** is a hardware accelerator design and optimization framework for long-context LLM inference. It provides a co-design optimization system that jointly optimizes hardware architecture, precision settings, and inference performance.

## Key Features

- **Multi-objective Optimization**: Jointly optimize accuracy, latency, and area using Bayesian optimization
- **Hardware-Software Co-design**: Unified framework for hardware parameter tuning and precision configuration
- **Flexible Precision Support**: MXFP, MXINT, and standard floating-point formats
- **Extensible Model Library**: Pre-configured support for LLaMA and Qwen model families

## Quick Start

```bash
# Install dependencies
pip install -e .

# Run optimization search
python -m co_design.search.search --config co_design/configs/config.toml
```

## Project Structure

```
PLENA/
├── co_design/              # Core co-design optimization module
│   ├── interface/          # Hardware/simulator abstraction
│   ├── search/             # Multi-objective optimization engine
│   └── configs/            # Configuration files
├── PLENA_RTL/              # SystemVerilog hardware design
├── PLENA_Simulator/        # Hardware simulator
└── doc/                    # Documentation
```

## Publication

If you use PLENA in your research, please cite:

```bibtex
@misc{wu2025combatingmemorywallsoptimization,
    title={Combating the Memory Walls: Optimization Pathways for Long-Context Agentic LLM Inference},
    author={Haoran Wu and Can Xiao and Jiayi Nie and Xuan Guo and Binglei Lou and Jeffrey T. H. Wong and Zhiwen Mo and Cheng Zhang and Przemyslaw Forys and Wayne Luk and Hongxiang Fan and Jianyi Cheng and Timothy M. Jones and Rika Antonova and Robert Mullins and Aaron Zhao},
    year={2025},
    eprint={2509.09505},
    archivePrefix={arXiv},
    primaryClass={cs.AR},
    url={https://arxiv.org/abs/2509.09505},
}
```

[Paper Link](https://arxiv.org/abs/2509.09505)
