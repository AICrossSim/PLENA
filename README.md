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
| [PLENA_RTL](./PLENA_RTL) | Full RTL implementation of the PLENA accelerator (work in progress) |
| [PLENA_Simulator](./PLENA_Simulator) | HBM-enabled transactional simulator |
| [PLENA_Software](./PLENA_Software) | Software stack including compiler and tools |

> **Note:** The RTL implementation ([PLENA_RTL](./PLENA_RTL)) is a work in progress and will be open sourced by the end of August 2026.

### Getting Started

```bash
# Clone with all submodules
git clone --recursive https://github.com/AICrossSim/PLENA.git

# Or initialize submodules after cloning
git submodule update --init --recursive
```

## Publication

**Combating the Memory Walls: Optimization Pathways for Long-Context Agentic LLM Inference** (ISCA 2026) [[Paper](https://doi.org/10.1109/ISCA66397.2026.00023)] [[arXiv](https://arxiv.org/abs/2509.09505)]

```bibtex
@INPROCEEDINGS{11617831,
  author={Wu, Haoran and Xiao, Can and Nie, Jiayi and Guo, Xuan and Lou, Binglei and Wong, Jeffrey T.H. and Mo, Zhiwen and Zhang, Cheng and Forys, Przemyslaw and Ai, Chengyang and Adeniran, Timi and Luk, Wayne and Fan, Hongxiang and Cheng, Jianyi and Jones, Timothy M. and Antonova, Rika and Mullins, Robert and Zhao, Aaron},
  booktitle={2026 ACM/IEEE 53rd Annual International Symposium on Computer Architecture (ISCA)}, 
  title={Combating the Memory Walls: Optimization Pathways for Long-Context Agentic Llm Inference}, 
  year={2026},
  volume={},
  number={},
  pages={100-115},
  keywords={Arrays;Modeling;Printing;Quantization (signal);Memory;Optimization;Design methodology;Systolic arrays;Large language models;Matrices;LLM Accelerator;Agentic Inference;Systolic Array;FlashAttention;Quantization},
  doi={10.1109/ISCA66397.2026.00023}}
```




