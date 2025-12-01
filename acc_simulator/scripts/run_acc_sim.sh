# MODEL_NAME="meta-llama/Meta-Llama-3-8B"
MODEL_NAME="meta-llama/Llama-2-13b-hf"
# MODEL_NAME="meta-llama/Llama-3.2-1B"

# MODEL_NAME="nvidia/Nemotron-H-8B-Base-8K"
# MODEL_NAME="state-spaces/mamba-2.8b-hf"
CUDA_DEVICE="cuda:6"
# --preset XWqBKVNL \
echo $MODEL_NAME
echo $CUDA_DEVICE

# --preset_W MXFP_E2M1_B16_S8 \

CUDA_LAUNCH_BLOCKING=1 PYTHONFAULTHANDLER=1 \
python -m acc_simulator.cli.acc_sim \
  --model_name="$MODEL_NAME" \
  --preset XWqBqKVNL \
  --preset_X MINIFLOAT_E3M4 \
  --preset_W MINIFLOAT_E3M4 \
  --preset_Kv MXINT_4_B16_S8 \
  --preset_NL FP_E3M4 \
  --device_id "$CUDA_DEVICE" \
  --use_gptq False \
  --online_rotate False \
  --clip_search False \
  --clip_search_y False \
  --log_dir results \
  --save_dir ckpt \
  --cali_batch_size 64 \
