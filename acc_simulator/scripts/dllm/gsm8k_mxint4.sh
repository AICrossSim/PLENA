#!/bin/bash
# Fast-dLLM v2 GSM8K evaluation - MXInt4 weight quantization
#
# Run with: conda activate acc-sim && bash acc_simulator/scripts/dllm/gsm8k_mxint4.sh

set -e

export HF_ALLOW_CODE_EVAL=1
export HF_DATASETS_TRUST_REMOTE_CODE=true

MODEL="Efficient-Large-Model/Fast_dLLM_v2_1.5B"
DEVICE="cuda:1"

# Quantization settings
PRESET="XWqBqKVNL"
PRESET_W="MXINT_4_B32_S8"

echo "=========================================="
echo "Fast-dLLM v2 GSM8K - MXInt4 Quantization"
echo "=========================================="
echo "Preset: ${PRESET}"
echo "Format: ${PRESET_W}"
echo "=========================================="

python -m acc_simulator.cli.acc_sim \
    --model_type dllm \
    --model_name "${MODEL}" \
    --tasks gsm8k \
    --device_id "${DEVICE}" \
    --batch_size 32 \
    --num_fewshot 0 \
    --threshold 1.0 \
    --show_speed True \
    --preset "${PRESET}" \
    --preset_W "${PRESET_W}" \
    --clip_search True

echo ""
echo "=========================================="
echo "Done!"
echo "=========================================="
