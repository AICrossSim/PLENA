MODEL_NAME_LIST=("meta-llama/Llama-2-7b-hf")
CUDA_DEVICE="cuda:3"
echo $CUDA_DEVICE

# online_rotate_list=("down_proj" "up_proj" "gate_proj" "q_proj" "k_proj" "v_proj" "o_proj")
online_rotate_list=("up_proj")
for model_name in "${MODEL_NAME_LIST[@]}"; do
  for x_kv_config in MXINT_4_B16_S8; do
    for w_config in MXINT_4_B16_S8; do
      for online_rotate_list in "${online_rotate_list[@]}"; do
        CUDA_LAUNCH_BLOCKING=1 PYTHONFAULTHANDLER=1 python -m acc_simulator.cli.acc_sim \
          --model_name="$model_name" \
          --preset XqWqBqKVqNL \
          --preset_W $w_config \
          --preset_X $x_kv_config \
          --preset_Kv $x_kv_config \
          --preset_NL MINIFLOAT_E6M5 \
          --device_id "$CUDA_DEVICE" \
          --use_gptq True \
          --online_rotate True \
          --clip_search_y True \
          --save_gptq True \
          --save_dir ${CX_DATA_HOME}/saved_models \
          --resume_from_checkpoint True \
          --log_dir results/w_${w_config}_x_${x_kv_config}_${model_name}_nl_${preset_NL}
        #   --layer_for_online_rotate $online_rotate_list \
        done
    done
  done
done

