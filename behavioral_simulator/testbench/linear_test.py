import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import Tensor, nn
# from acc_simulator.quantize.quantized_layers.linear import MXFPLinearPTQ
from test_data_gen import get_weights_path, generate_and_save_random_weights
from compiler.asm_templates import projection_asm, preload_act_asm, reset_reg_asm, preload_addr_reg_asm
from create_sim_env import create_sim_env



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

    # Gen Weight and Test Data
    # generate_and_save_random_weights(hidden_size, hidden_size, get_weights_path('model_weights.pt'))
    
    torch.manual_seed(42)
    input_tensor = torch.randn(batch_size, hidden_size)
    original_layer = nn.Linear(in_features=hidden_size, out_features=hidden_size)
    weights = original_layer.state_dict()


    original_output = original_layer(input_tensor)

    golden_result = {
        "input_tensor": input_tensor,
        "weights": weights,
        "original_output": original_output
    }

    gen_assembly_code = "; Linear Test Generation \n"
    
    # Set the addr offset for weight and bias
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1, 2],
        available_registers=[1, 2],
        addr_reg_val=[int(hidden_size * batch_size * real_data_ratio), int((hidden_size * (batch_size + 1) + hidden_size * hidden_size) * real_data_ratio)]
    )

    print("hidden_size * batch_size * real_data_ratio", hidden_size * batch_size * real_data_ratio)
    print("(hidden_size * (batch_size + 1) + hidden_size * hidden_size) * real_data_ratio", (hidden_size * (batch_size + 1) + hidden_size * hidden_size) * real_data_ratio)

    # Gen Activation Preload
    gen_assembly_code += preload_act_asm(
        vlen=64,
        preload_len=1,
        batch=4,
        hidden_size=128,
        alive_registers=[1,2],
        activation_offset_reg=0
    )

    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2]
    )

    gen_assembly_code += projection_asm(
        mlen=64,
        blen=4,
        batch=4,
        hidden_size=128,
        alive_registers=[1,2,3,4,5,6,7,8],
        head_dim=128,
        w_base_hbm_offset_reg=1,
        rope_hbm_offset_reg=0,
        rope_on_chip_address=0,
        activation_base_address=0,
        result_base_address=0,
        rope_enabled=False
    )

    # print("input_tensor shape", input_tensor.shape)
    # exit()
    create_sim_env(input_tensor, weights, gen_assembly_code, golden_result)