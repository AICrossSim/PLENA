# MODEL_NAME="TinyLlama/TinyLlama-1.1B-Chat-v1.0"
MODEL_NAME="meta-llama/Meta-Llama-3-8B"

# --preset XWqBKVNL \
echo $MODEL_NAME

for x_kv_config in MXINT_4_B16_S8; do
  for w_config in MXINT_4_B16_S8; do
    CUDA_LAUNCH_BLOCKING=1 PYTHONFAULTHANDLER=1 python -m acc_simulator.cli.acc_sim \
      --model_name="$MODEL_NAME" \
      --preset XqWqBqKVqNL \
      --preset_W $w_config \
      --preset_X $x_kv_config \
      --preset_Kv $x_kv_config \
      --model_parallel False \
      --use_gptq False\
      --offline_rotate False \
      --online_rotate True \
      --clip_search_y False
  done
done
  # > acc_simulator/offline_rotate_only_with_gptq.out 2>&1

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
