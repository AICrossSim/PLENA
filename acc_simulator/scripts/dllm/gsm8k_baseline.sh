#!/bin/bash
# Fast-dLLM v2 GSM8K evaluation - Baseline (no quantization)
#
# Run with: conda activate acc-sim && bash acc_simulator/scripts/dllm/gsm8k_baseline.sh

set -e

export HF_ALLOW_CODE_EVAL=1
export HF_DATASETS_TRUST_REMOTE_CODE=true

MODEL="Efficient-Large-Model/Fast_dLLM_v2_1.5B"
DEVICE="cuda:0"

echo "=========================================="
echo "Fast-dLLM v2 GSM8K - Baseline (BF16)"
echo "=========================================="

python -m acc_simulator.cli.dllm_sim \
    --model_name "${MODEL}" \
    --tasks gsm8k \
    --device_id "${DEVICE}" \
    --batch_size 32 \
    --num_fewshot 0 \
    --threshold 1.0 \
    --show_speed True

echo ""
echo "=========================================="
echo "Done!"
echo "=========================================="
