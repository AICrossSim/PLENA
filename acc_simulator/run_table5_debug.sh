MODEL_NAME="TinyLlama/TinyLlama-1.1B-Chat-v1.0"
CUDA_DEVICE="cuda:0"
echo $MODEL_NAME
echo $CUDA_DEVICE


for x_kv_config in MXINT_4_B16_S8; do
  for w_config in MXINT_4_B16_S8; do
    CUDA_LAUNCH_BLOCKING=1 PYTHONFAULTHANDLER=1 python -m acc_simulator.cli.acc_sim \
      --model_name="$MODEL_NAME" \
      --preset XqWqBqKVqNL \
      --preset_W $w_config \
      --preset_X $x_kv_config \
      --preset_Kv $x_kv_config \
      --device_id "$CUDA_DEVICE" \
      --use_gptq False\
      --online_rotate False \
      --clip_search_y False \
      --save_gptq False \
      --save_dir ${CX_DATA_HOME}/saved_config/${x_kv_config} \
      --log_dir results/w_${w_config}_x_${x_kv_config}
  done
done

