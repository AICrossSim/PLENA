#!/bin/bash
echo "Running baseline bf16"
python -m acc_simulator.cli.acc_sim \
  --preset original \
  --model_parallel True \
  --enable_eval_harness False \
  > acc_simulator/baseline_bf16.out 2>&1

echo "Running XWqBqKV (weights only) W8"
python -m acc_simulator.cli.acc_sim \
  --preset XWqBqKV \
  --preset_mxfp_W MXFP8_E4M3 \
  --model_parallel True \
  > acc_simulator/weights_only_w8.out 2>&1

echo "Running XqWqBqKVqNLq"
python -m acc_simulator.cli.acc_sim \
  --preset XqWqBqKVqNLq \
  --preset_mxfp_X MXFP8_E4M3 \
  --preset_mxfp_W MXFP8_E4M3 \
  --preset_mxfp_Kv MXFP8_E4M3 \
  --preset_minifloat_NL FP8_E4M3 \
  --model_parallel True \
  --enable_eval_harness False \
  > acc_simulator/XqWqBqKVqNLq.out 2>&1
