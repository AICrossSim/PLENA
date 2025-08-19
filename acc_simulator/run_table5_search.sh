MODEL_NAME="meta-llama/Llama-2-7b-hf"
CUDA_DEVICE="cuda:0"
echo $MODEL_NAME
echo $CUDA_DEVICE


config_list=(
  "--clip_search False --online_rotate False --use_gptq False --clip_search_y False"
  "--clip_search True --online_rotate False --use_gptq False --clip_search_y False"
  "--clip_search True --online_rotate True --use_gptq False --clip_search_y False"
  "--clip_search True --online_rotate True --use_gptq True --clip_search_y False"
  "--clip_search True --online_rotate True --use_gptq True --clip_search_y True"
  )
for x_kv_config in MXINT_4_B16_S8; do
  for w_config in MXINT_4_B16_S8; do
    for config in "${config_list[@]}"; do
      CUDA_LAUNCH_BLOCKING=1 PYTHONFAULTHANDLER=1 python -m acc_simulator.cli.acc_sim \
        --model_name="$MODEL_NAME" \
        --preset XqWqBqKVqNL \
        --preset_W $w_config \
        --preset_X $x_kv_config \
        --preset_Kv $x_kv_config \
        --device_id "$CUDA_DEVICE" \
        --save_dir ${CX_DATA_HOME}/saved_models \
        --resume_from_checkpoint True \
        --log_dir results/w_${w_config}_x_${x_kv_config} \
        $config \
      # --save_gptq False \
    done
  done
done

