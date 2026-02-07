From the **project root**:

### Installation

```bash
direnv deny .
conda env create -f acc_simulator/environment.yml
conda activate acc-sim
git submodule update --init --recursive
cd acc_simulator/third_party/fast_hadamard_transform
pip install -e .
```

### Running dLLM Evaluation

```bash
# Baseline (BF16)
bash acc_simulator/scripts/dllm/gsm8k_baseline.sh

# MXInt4 weight-only quantization
bash acc_simulator/scripts/dllm/gsm8k_mxint4.sh
```

---

## Results

diffusion block size 32
Block_cache = True
Tested on L40 single core

### Fast_dLLM_v2_1.5B

| Model | GSM8K 0-shot | Tokens/s |
|-------|--------------|----------|
| Baseline (BF16) | 0.63 (paper: 0.62) | - |
| INT4 | 0.43 | 658 |
| INT4 + no_block_cache | 0.43 | 614 |
| INT4 + x_clip | 0.37 | 672 |
| INT4 + gptq + x_clip | 0.51 | - |
| INT4 + gptq + y_clip | - | - |

### Fast_dLLM_v2_7B

| Model | GSM8K 0-shot | Tokens/s |
|-------|--------------|----------|
| Baseline (BF16) | 0.83 (paper: 0.83) | - |
| INT4 | - | - |
| INT4 + x_clip | 0.75 | 178 |
| INT4 + gptq + x_clip | 0.79 | 198 |
| INT4 + gptq + y_clip | 0.805 | - |