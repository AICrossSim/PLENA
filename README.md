# PLENA: A Programmable Long-context Efficient Neural Accelerator

PLENA is a complete hardware-software system for efficient long-context LLM inference. It addresses key limitations of prior LLM accelerators by providing:

- A custom instruction set (**PLENA_ISA**) for large Transformer inference
- A PyTorch-to-PLENA_ISA compiler
- An HBM-enabled transactional simulator
- An automated, accuracy-aware design-space exploration (DSE) flow
- A full RTL implementation

PLENA supports state-of-the-art Transformer model variants including GQA, MHA, MLA, Dense, and MoE architectures.

📖 **[Documentation](https://aicrosssim.github.io/PLENA_Doc/)**

## Repository Structure

This repository contains three submodules:

| Submodule | Description |
|-----------|-------------|
| [PLENA_RTL](./PLENA_RTL) | Full RTL implementation of the PLENA accelerator |
| [PLENA_Simulator](./PLENA_Simulator) | HBM-enabled transactional simulator |
| [PLENA_Software](./PLENA_Software) | Software stack including compiler and tools |

### Getting Started

```bash
# Clone with all submodules
git clone --recursive https://github.com/AICrossSim/PLENA.git

# Or initialize submodules after cloning
git submodule update --init --recursive
```

## Publication

**Combating the Memory Walls: Optimization Pathways for Long-Context Agentic LLM Inference** [[Paper](https://arxiv.org/abs/2509.09505)]

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




