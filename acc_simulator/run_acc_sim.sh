MODEL_NAME="meta-llama/Meta-Llama-3-70B"
# MODEL_NAME="meta-llama/Llama-2-7b-hf"
CUDA_DEVICE="cuda:1"
# --preset XWqBKVNL \
echo $MODEL_NAME
echo $CUDA_DEVICE
echo "original with rotation 8B MXFP6"

CUDA_LAUNCH_BLOCKING=1 PYTHONFAULTHANDLER=1 \
python -m acc_simulator.cli.acc_sim \
  --model_name="$MODEL_NAME" \
  --preset XqWqBqKVqNL \
  --preset_X MXINT_4_B4_S8 \
  --preset_W MXINT_4_B4_S8 \
  --preset_Kv MXINT_4_B4_S8 \
  --device_id "$CUDA_DEVICE" \
  --use_gptq True \
  --offline_rotate False \
  --online_rotate False \
  --clip_search_y True \
  --log_dir results \
  --save_gptq True \
#   > save_8b_gptq.log 2>&1