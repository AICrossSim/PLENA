import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import Tensor, nn
from test_data_gen import get_weights_path, generate_and_save_random_weights
from compiler.asm_templates import projection_asm, preload_act_asm, reset_reg_asm, preload_addr_reg_asm
from create_sim_env import create_sim_env
from sim_env_utils import build_sim_env


if __name__ == "__main__":
    # Testing the operation (hidden_size, hidden_size) @ (hidden_size, batch_size)
    hidden_size = 128
    batch_size = 4
    real_data_ratio = (8*8 + 8) / (8 * 8)
    fp_preload = [0.0, 1e-6, 1/hidden_size]

    torch.manual_seed(42)
    act_tensor = torch.randn(batch_size, hidden_size)
    original_layer = nn.Linear(in_features=hidden_size, out_features=hidden_size, bias=False)
    weights = original_layer.state_dict()

    original_output = original_layer(act_tensor)
    print("original_output is:\n", original_output)

    input_tensor = {
        "act_tensor": act_tensor,
        "weights": weights['weight'].t(),
    }

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": original_output
    }

    gen_assembly_code = "; Linear Test with Loop Instructions \n"

    # Set the addr offset for weight and bias
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1, 2],
        available_registers=[1, 2],
        addr_reg_val=[int(hidden_size * batch_size * real_data_ratio), int((hidden_size * (batch_size + 1) + hidden_size * hidden_size) * real_data_ratio)]
    )

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
        alive_registers=[1,2,3,4,5],
        act_vram_offset=0,
        activation_offset_reg=0,
        stride_size=hidden_size
    )

    # Reset the registers - need 7 for loop version
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3,4,5,6,7]
    )

    # Use the loop-optimized projection assembly
    gen_assembly_code += projection_asm(
        mlen=64,
        blen=4,
        batch=4,
        hidden_size=128,
        alive_registers=[1,2,3,4,5,6,7],  # Need 7 registers for loop version
        w_base_hbm_offset_reg=1,
        activation_base_address=0,
        result_base_address=hidden_size * batch_size,
        rope_enabled=False,
        use_loop_instructions=True  # Enable loop optimization
    )

    # Print generated assembly for comparison
    print("=" * 60)
    print("Generated Assembly Code (Loop Version):")
    print("=" * 60)
    print(gen_assembly_code)
    print("=" * 60)

    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    build_sim_env(data_size=256, mode="behave_sim", asm="linear", data=None, specified_data_order = ["act_tensor", "weights"])

    print("================================================")
    print("Finished generating assembly code")
    print("================================================")
