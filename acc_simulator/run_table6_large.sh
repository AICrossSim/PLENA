MODEL_NAME_LIST=("meta-llama/Meta-Llama-3-70B")



# MODEL_NAME="meta-llama/Llama-2-7b-hf"
CUDA_DEVICE="cuda:1"
# --preset XWqBKVNL \
echo $MODEL_NAME
echo $CUDA_DEVICE


for model_name in "${MODEL_NAME_LIST[@]}"; do
  for x_kv_config in MXINT_4_B16_S8; do
    for w_config in MXINT_4_B16_S8; do
      CUDA_LAUNCH_BLOCKING=1 PYTHONFAULTHANDLER=1 python -m acc_simulator.cli.acc_sim \
        --model_name="$model_name" \
        --preset XqWqBqKVqNL \
        --preset_W $w_config \
        --preset_X $x_kv_config \
        --preset_Kv $x_kv_config \
        --device_id "$CUDA_DEVICE" \
        --use_gptq True\
        --online_rotate True \
        --clip_search_y True \
        --save_gptq True \
        --save_dir ${CX_DATA_HOME}/saved_models \
        --log_dir results/w_${w_config}_x_${x_kv_config}_${model_name}
    done
  done
done

