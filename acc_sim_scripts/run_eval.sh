#!/bin/bash

# Exit on error
set -e

# === Config ===
MODEL_ARCH="llama"
MODEL_NAME="meta-llama/Llama-2-7b-hf"
QUANT_CONFIG="acc_simulator/config/config_minifloat.toml"
TASK="wikitext"
MAX_BATCH_SIZE=4
DEVICE_MAP="auto"
RUN_PYTORCH=false  # Set to true to bypass quantization

# === Command Construction ===
CMD="python -m acc_simulator.eval.cli_harness_eval \
  --model_arch $MODEL_ARCH \
  --model_name $MODEL_NAME \
  --quant_config $QUANT_CONFIG \
  --task $TASK \
  --max_batch_size $MAX_BATCH_SIZE \
  --device_map $DEVICE_MAP"

if [ "$RUN_PYTORCH" = true ]; then
  CMD="$CMD --run_pytorch"
fi

# === Logging and Execution ===
echo "[INFO] Running evaluation for task: $TASK"
echo "[INFO] Command: $CMD"
eval $CMD
