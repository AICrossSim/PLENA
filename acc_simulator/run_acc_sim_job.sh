#!/bin/bash

# MODEL_NAME="meta-llama/Meta-Llama-3-8B"
MODEL_NAME="meta-llama/Llama-2-7b-hf"

# --preset XWqBKVNL \
echo $MODEL_NAME
echo "original with rotation 8B MXFP6"
CUDA_LAUNCH_BLOCKING=1 PYTHONFAULTHANDLER=1 python -m acc_simulator.cli.acc_sim \
  --model_name="$MODEL_NAME" \
  --preset XWqBKVqNL \
  --preset_X MXFP_E4M3_B16_S8 \
  --preset_W MXFP_E1M2_B16_S8 \
  --preset_KV MXFP_E4M3_B16_S8 \
  --model_parallel False \
  --use_gptq False\
  --offline_rotate True \
  --online_rotate True \
  # > acc_simulator/rotation2.out 2>&1

# echo "Running XWqBKVNL linear weights only GPTQ"
# CUDA_LAUNCH_BLOCKING=1 PYTHONFAULTHANDLER=1 python -m acc_simulator.cli.acc_sim \
#   --model_name="$MODEL_NAME" \
#   --preset XWqBKVNL \
#   --preset_mxfp_W MXFP_E2M1_B16_S8 \
#   --model_parallel True \
#   --use_gptq True\
#   > acc_simulator/weights_only_gptq.out 2>&1

# echo "Running baseline bf16"
# python -m acc_simulator.cli.acc_sim \
#   --preset original \
#   --model_parallel True \
#   --enable_eval_harness False \
#   > acc_simulator/baseline_bf16.out 2>&1

# echo "Running XWqBKVNL (weights only) W8"
# python -m acc_simulator.cli.acc_sim \
#   --preset XWqBKVNL \
#   --preset_mxfp_W MXFP_E4M3_B16_S8 \
#   --model_parallel True \
#   > acc_simulator/weights_only_w8.out 2>&1

# echo "Running XqWqBqKVqNLq"
# python -m acc_simulator.cli.acc_sim \
#   --preset XqWqBqKVqNLq \
#   --preset_mxfp_X MXFP_E4M3_B16_S8 \
#   --preset_mxfp_W MXFP_E4M3_B16_S8 \
#   --preset_mxfp_Kv MXFP_E4M3_B16_S8 \
#   --preset_minifloat_NL FP_E4M3 \
#   --model_parallel True \
#   --enable_eval_harness False \
#   > acc_simulator/XqWqBqKVqNLq.out 2>&1
