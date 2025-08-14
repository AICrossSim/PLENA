# MODEL_NAME="meta-llama/Meta-Llama-3-8B"
# MODEL_NAME="meta-llama/Llama-2-7b-hf"
MODEL_NAME="meta-llama/Llama-3.2-1B"

CUDA_DEVICE="cuda:0"
# --preset XWqBKVNL \
echo $MODEL_NAME
echo $CUDA_DEVICE

CUDA_LAUNCH_BLOCKING=1 PYTHONFAULTHANDLER=1 \
python -m acc_simulator.cli.acc_sim \
  --model_name="$MODEL_NAME" \
  --preset XqWqBqKVqNL \
  --preset_X MXINT_4_B16_S8 \
  --preset_W MXINT_4_B16_S8 \
  --preset_Kv MXINT_4_B16_S8 \
  --device_id "$CUDA_DEVICE" \
  --use_gptq True \
  --online_rotate True \
  --clip_search_y True \
  --log_dir results \
  --save_gptq True \
  --cali_batch_size 32 \
#   > save_8b_gptq.log 2>&1