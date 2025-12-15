import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import nn
from compiler.asm_templates import projection_asm, preload_act_asm, reset_reg_asm, preload_addr_reg_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim


if __name__ == "__main__":
    # Testing rectangular linear: (batch, in_features) @ (in_features, out_features) -> (batch, out_features)
    in_features = 128
    out_features = 64  # Rectangular matrix test
    batch_size = 4
    real_data_ratio = (8*8 + 8) / (8 * 8)
    fp_preload = [0.0, 1e-6, 1/in_features]

    torch.manual_seed(42)
    act_tensor = torch.randn(batch_size, in_features)
    original_layer = nn.Linear(in_features=in_features, out_features=out_features, bias=False)
    weights = original_layer.state_dict()

    original_output = original_layer(act_tensor)
    print(f"Linear: ({batch_size}, {in_features}) @ ({in_features}, {out_features}) -> ({batch_size}, {out_features})")
    print("original_output shape:", original_output.shape)
    print("original_output is:\n", original_output)
    
    print("weight shape:", weights['weight'].shape)
    sys.exit(0)

    # Weight is stored as (out_features, in_features) in PyTorch, we transpose for our layout
    # Our layout: (in_features, out_features) for matmul: act @ weight
    input_tensor = {
        "act_tensor": act_tensor,
        "weights": weights['weight'].t(),  # (in_features, out_features)
    }

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": original_output
    }
    
    print("original_output shape:", original_output.shape)

    gen_assembly_code = "; Linear Test Generation (Rectangular Matrix)\n"
    gen_assembly_code += f"; Shape: ({batch_size}, {in_features}) @ ({in_features}, {out_features}) -> ({batch_size}, {out_features})\n"

    # Calculate HBM offsets
    # Layout in HBM: [activations | weights]
    act_hbm_size = int(in_features * batch_size * real_data_ratio)
    weight_hbm_offset = act_hbm_size
    weight_hbm_end = int((in_features * batch_size + in_features * out_features) * real_data_ratio)

    # Set the addr offset for weight
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1, 2],
        available_registers=[1, 2],
        addr_reg_val=[weight_hbm_offset, weight_hbm_end]
    )

    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3]
    )

    # Gen Activation Preload
    gen_assembly_code += preload_act_asm(
        vlen=64,
        preload_len=4,
        batch=batch_size,
        hidden_size=in_features,
        alive_registers=[1,2,3,4,5],
        act_vram_offset=0,
        activation_offset_reg=0,
        stride_size=in_features
    )

    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3,4]
    )

    # Result is stored after activation in VRAM
    result_vram_offset = in_features * batch_size

    gen_assembly_code += projection_asm(
        mlen=64,
        blen=4,
        batch=batch_size,
        hidden_size=in_features,      # in_features (input dimension)
        out_features=out_features,     # out_features (output dimension) - rectangular support!
        alive_registers=[1,2,3,4,5],
        w_base_hbm_offset_reg=1,
        activation_base_address=0,
        result_base_address=result_vram_offset,
        rope_enabled=False
    )
    
    # sys.exit(0)

    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    create_mem_for_sim(data_size=256, mode="behave_sim", asm="linear", data=None, specified_data_order=["act_tensor", "weights"])

    # Save comparison parameters for view_mem.py
    import json
    result_start_row = result_vram_offset // 64  # Row where results start
    num_result_rows = (batch_size * out_features) // 64
    comparison_params = {
        "start_row_idx": result_start_row,
        "num_rows": num_result_rows,
        "num_batches": batch_size,
        "elements_per_batch": out_features
    }
    build_dir = Path(__file__).parent / "build"
    with open(build_dir / "comparison_params.json", "w") as f:
        json.dump(comparison_params, f, indent=2)
    
    with open("behavioral_simulator/testbench/linear_test.asm", "w") as f:
        f.write(gen_assembly_code)

    print("================================================")
    print("Finished generating assembly code")
    print(f"Result location: row {result_start_row}, {num_result_rows} rows")
    print(f"Comparison params: {comparison_params}")
    print("================================================")
