import sys
from pathlib import Path
import argparse
import torch
from torch import nn

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Local imports
from test_data_gen import get_weights_path, generate_and_save_random_weights
from compiler.asm_templates import (
    projection_asm,
    preload_act_asm,
    reset_reg_asm,
    preload_addr_reg_asm,
)
from create_sim_env import create_sim_env
from sim_env_utils import build_fake_sim_env


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run linear projection simulation")
    parser.add_argument("--mlen", type=int, default=64,)
    parser.add_argument("--bs", type=int, default=16, help="Batch size")
    parser.add_argument("--hs", type=int, default=128, help="Hidden size")
    args = parser.parse_args()

    mlen = args.mlen
    batch_size = args.bs
    hidden_size = args.hs

    real_data_ratio = (8 * 8 + 8) / (8 * 8)
    fp_preload = [0.0, 1e-6, 1 / hidden_size]

    torch.manual_seed(42)
    input_tensor = torch.randn(batch_size, hidden_size)
    original_layer = nn.Linear(in_features=hidden_size, out_features=hidden_size, bias=False)
    weights = original_layer.state_dict()

    w_k = weights["weight"] if isinstance(weights, dict) else weights
    original_output = original_layer(input_tensor)

    golden_result = {
        "input_tensor": input_tensor,
        "weights": weights,
        "original_output": original_output,
    }

    gen_assembly_code = "; Linear Test Generation \n"

    # Set the addr offset for weight and bias
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1, 2],
        available_registers=[1, 2],
        addr_reg_val=[
            int(hidden_size * batch_size * real_data_ratio),
            int((hidden_size * (batch_size + 1) + hidden_size * hidden_size) * real_data_ratio),
        ],
    )

    print("hidden_size * batch_size * real_data_ratio =", hidden_size * batch_size * real_data_ratio)
    print(
        "(hidden_size * (batch_size + 1) + hidden_size * hidden_size) * real_data_ratio =",
        (hidden_size * (batch_size + 1) + hidden_size * hidden_size) * real_data_ratio,
    )

    # Reset registers
    gen_assembly_code += reset_reg_asm(alive_registers=[1, 2, 3])

    # Gen Activation Preload
    gen_assembly_code += preload_act_asm(
        vlen=mlen,
        preload_len=4,
        batch=batch_size,
        hidden_size=hidden_size,
        alive_registers=[1, 2, 3],
        act_vram_offset=0,
        activation_offset_reg=0,
    )

    # Reset registers
    gen_assembly_code += reset_reg_asm(alive_registers=[1, 2, 3, 4])

    # Projection step
    gen_assembly_code += projection_asm(
        mlen=mlen,
        blen=4,
        batch=batch_size,
        hidden_size=hidden_size,
        alive_registers=[1, 2, 3, 4],
        head_dim=hidden_size,
        w_base_hbm_offset_reg=1,
        rope_hbm_offset_reg=0,
        rope_on_chip_address=0,
        activation_base_address=0,
        result_base_address=hidden_size * batch_size,
        rope_enabled=False,
    )

    create_sim_env(input_tensor, weights["weight"].t(), gen_assembly_code, golden_result, fp_preload)

    build_fake_sim_env(
        data_size=256,
        mode="behave_sim",
        asm="linear",
        data=None,
        specified_data_order=["input_tensor", "weights"],
    )
