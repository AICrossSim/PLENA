#!/bin/bash
echo "Running baseline bf16"
python -m acc_simulator.cli.acc_sim \
  --preset original \
  --model_parallel True \
  --enable_eval_harness False \
  > acc_simulator/baseline_bf16.out 2>&1

echo "Running XWqBqKVNL (weights only) W8"
python -m acc_simulator.cli.acc_sim \
  --preset XWqBqKVNL \
  --preset_mxfp_W MXFP_E4M3_B16_S16 \
  --model_parallel True \
  > acc_simulator/weights_only_w8.out 2>&1

echo "Running XqWqBqKVqNLq"
python -m acc_simulator.cli.acc_sim \
  --preset XqWqBqKVqNLq \
  --preset_mxfp_X MXFP_E4M3_B16_S8 \
  --preset_mxfp_W MXFP_E4M3_B16_S8 \
  --preset_mxfp_Kv MXFP_E4M3_B16_S8 \
  --preset_minifloat_NL FP_E4M3 \
  --model_parallel True \
  --enable_eval_harness False \
  > acc_simulator/XqWqBqKVqNLq.out 2>&1
