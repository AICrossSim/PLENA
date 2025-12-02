import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import Tensor, nn
# from acc_simulator.quantize.quantized_layers.linear import MXFPLinearPTQ
from test_data_gen import get_weights_path, generate_and_save_random_weights
from compiler.asm_templates import projection_asm, preload_act_asm, reset_reg_asm, preload_addr_reg_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim


# TODOs: Need to integrate the MX quantizer here.
# quantized_layer = MXFPLinearPTQ.from_linear(
#     layer=original_layer,
#     x_meta=my_x_meta,
#     w_meta=my_w_meta,
#     b_meta=my_b_meta,
#     layer_type="XWB",
#     online_rotate=False,
#     clip_search_y=False
# )


if __name__ == "__main__":
    # Testing the operation (hidden_size, hidden_size) @ (hidden_size, batch_size)
    hidden_size = 128
    batch_size = 4
    real_data_ratio = (8*8 + 8) / (8 * 8)
    fp_preload = [0.0, 1e-6, 1/hidden_size]

    # Gen Weight and Test Data
    # generate_and_save_random_weights(hidden_size, hidden_size, get_weights_path('model_weights.pt'))
    
    torch.manual_seed(42)
    act_tensor = torch.randn(batch_size, hidden_size)
    original_layer = nn.Linear(in_features=hidden_size, out_features=hidden_size, bias=False)
    weights = original_layer.state_dict()
    
    original_output = original_layer(act_tensor)

    # Print weight k, (128, 128) -> print 4 quadrants of (64, 64) each
    # Quadrant indices:
    # 0: [0:64, 0:64]
    # 1: [0:64, 64:128]
    # 2: [64:128, 0:64]
    # 3: [64:128, 64:128]
    w_k = weights['weight'].t() if isinstance(weights, dict) else weights
    print("Weight k shape:", w_k.shape)
    # for idx, (r_slice, c_slice) in enumerate([
    #     (slice(0, 64), slice(0, 64)),
    #     (slice(0, 64), slice(64, 128)),
    #     (slice(64, 128), slice(0, 64)),
    #     (slice(64, 128), slice(64, 128)),
    # ]):
    #     print(f"---------- Quadrant {idx}: Rows {r_slice}, Cols {c_slice} ----------")
    #     print(w_k[r_slice, c_slice])


    # Print the matmul result of input_tensor[:, :64] and weight[0:64, 0:4]
    matmul_result_11 = act_tensor[:, :64] @ w_k[:64, :4]
    # print("act_tensor[:, :64]: \n", act_tensor[:, :64])
    # print("w_k[:64, :4]: \n", w_k[:64, :4])
    # print("Matmul result of input_tensor[:, :64] @ weight[0:64, 0:4]:")
    # print(matmul_result_11)

    matmul_result_22 = act_tensor[:, 64:] @ w_k[64:, :4]
    print("Matmul result of input_tensor[:, 64:] @ weight[64:, :4]:")
    print("act_tensor[:, 64:]: \n", act_tensor[:, 64:])
    print("w_k[64:, :4]: \n", w_k[64:, :4])
    print(matmul_result_22)

    print ("sum of two matmul results:", 
           matmul_result_11 + matmul_result_22)

    input_tensor = {
        "act_tensor": act_tensor,
        "weights": weights['weight'].t(),
    }

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": original_output
    }

    gen_assembly_code = "; Linear Test Generation \n"
    
    # Set the addr offset for weight and bias
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1, 2],
        available_registers=[1, 2],
        addr_reg_val=[int(hidden_size * batch_size * real_data_ratio), int((hidden_size * (batch_size + 1) + hidden_size * hidden_size) * real_data_ratio)]
    )

    # print("hidden_size * batch_size * real_data_ratio", hidden_size * batch_size * real_data_ratio)
    # print("(hidden_size * (batch_size + 1) + hidden_size * hidden_size) * real_data_ratio", (hidden_size * (batch_size + 1) + hidden_size * hidden_size) * real_data_ratio)
    
    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3]
    )
    
    # Gen Activation Preload
    gen_assembly_code += preload_act_asm(
        vlen=64,
        preload_len=4,
        batch=4,
        hidden_size=128,
        alive_registers=[1,2,3],
        act_vram_offset=0,
        activation_offset_reg=0,
        stride_size=hidden_size
    )

    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3,4]
    )

    gen_assembly_code += projection_asm(
        mlen=64,
        blen=4,
        batch=4,
        hidden_size=128,
        alive_registers=[1,2,3,4],
        w_base_hbm_offset_reg=1,
        activation_base_address=0,
        result_base_address=hidden_size * batch_size,
        rope_enabled=False
    )

    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    create_mem_for_sim(data_size=256, mode="behave_sim", asm="linear", data=None, specified_data_order = ["act_tensor", "weights"])

    print("================================================")
    print("Finished generating assembly code")
    print("================================================")
