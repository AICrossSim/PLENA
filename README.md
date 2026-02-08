# PLENA: A Programmable Long-context Efficient Neural Accelerator

<table>
<tr>
<td width="300">
  <img src="doc/plena_logo.png" alt="PLENA Logo" width="300"/>
</td>
<td>

PLENA is a complete hardware–software system that realizes the above optimizations. PLENA addresses key limitations of prior LLM accelerators by providing: (i) a custom instruction set (PLENA\_ISA) for large Transformer inference; (ii) a PyTorch-to-PLENA\_ISA compiler; (iii) an HBM-enabled transactional simulator; (iv) an automated, accuracy-aware design-space exploration (DSE) flow; and (v) a full RTL implementation. We demonstrate that PLENA supports different SOTA transformer model variants (e.g., GQA, MHA and MLA, Dense and MoE).

</td>
</tr>
</table>


## Publication
* Combating the Memory Walls: Optimization Pathways for Long-Context Agentic LLM Inference, [Paper](https://arxiv.org/abs/2509.09505)
  ```
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


## PLENA System Architecture
- **PLENA\_ISA**: A custom instruction set for large Transformer inference, [Specification](https://github.com/AICrossSim/PLENA_Compiler/blob/main/doc/plena_isa_spec.md)
- **PLENA\_Compiler**: A PyTorch-to-PLENA\_ISA compiler, [Code](https://github.com/AICrossSim/PLENA_Compiler)
- **PLENA\_Simulator**: An HBM-enabled transactional simulator, [Code](https://github.com/AICrossSim/PLENA_Simulator)
- **PLENA\_RTL**: A full RTL implementation, [Code](https://github.com/AICrossSim/PLENA_RTL)


<p align="center">
  <img src="doc/PLENA_Sys.png" alt="PLENA System Architecture" width="600"/>
</p>




