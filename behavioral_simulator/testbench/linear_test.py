import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import nn
from compiler.asm_templates import projection_asm, preload_act_asm, reset_reg_asm, preload_addr_reg_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim
from asm_perf_tracker import AsmPerfTracker


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
    # Testing rectangular linear: (batch, in_features) @ (in_features, out_features) -> (batch, out_features)
    in_features = 128
    out_features = 256  # Rectangular matrix test
    batch_size = 8
    real_data_ratio = (8*8 + 8) / (8 * 8)
    fp_preload = [0.0, 1e-6, 1/in_features]

    # Gen Weight and Test Data
    # generate_and_save_random_weights(hidden_size, hidden_size, get_weights_path('model_weights.pt'))

    torch.manual_seed(42)
    act_tensor = torch.randn(batch_size, in_features)
    original_layer = nn.Linear(in_features=in_features, out_features=out_features, bias=False)
    weights = original_layer.state_dict()

    original_output = original_layer(act_tensor)
    print(f"Linear: ({batch_size}, {in_features}) @ ({in_features}, {out_features}) -> ({batch_size}, {out_features})")
    print("original_output shape:", original_output.shape)
    print("original_output is:\n", original_output)

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
        "weights": weights['weight'].t(),  # (in_features, out_features)
    }

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": original_output
    }

    # Initialize performance tracker
    perf = AsmPerfTracker("Linear Test")
    perf.assembly_code = "; Linear Test Generation (Rectangular Matrix)\n"
    perf.assembly_code += f"; Shape: ({batch_size}, {in_features}) @ ({in_features}, {out_features}) -> ({batch_size}, {out_features})\n"

    # Calculate HBM offsets
    # Layout in HBM: [activations | weights]
    act_hbm_size = int(in_features * batch_size * real_data_ratio)
    weight_hbm_offset = act_hbm_size
    weight_hbm_end = int((in_features * batch_size + in_features * out_features) * real_data_ratio)

    # Set the addr offset for weight
    perf.add_section("preload_addr_reg_asm", preload_addr_reg_asm(
        addr_reg_to_set=[1, 2],
        available_registers=[1, 2],
        addr_reg_val=[weight_hbm_offset, weight_hbm_end]
    ))

    # print("hidden_size * batch_size * real_data_ratio", hidden_size * batch_size * real_data_ratio)
    # print("(hidden_size * (batch_size + 1) + hidden_size * hidden_size) * real_data_ratio", (hidden_size * (batch_size + 1) + hidden_size * hidden_size) * real_data_ratio)

    # Reset the registers
    perf.add_section("reset_reg_asm (1st)", reset_reg_asm(
        alive_registers=[1,2,3]
    ))

    # Gen Activation Preload
    perf.add_section("preload_act_asm", preload_act_asm(
        vlen=64,
        preload_len=4,
        batch=batch_size,
        hidden_size=in_features,
        alive_registers=[1,2,3,4,5],
        act_vram_offset=0,
        activation_offset_reg=0,
        stride_size=in_features
    ))

    # Reset the registers
    perf.add_section("reset_reg_asm (2nd)", reset_reg_asm(
        alive_registers=[1,2,3,4]
    ))

    # Result is stored after activation in VRAM
    result_vram_offset = in_features * batch_size

    perf.add_section("projection_asm", projection_asm(
        mlen=64,
        blen=4,
        batch=batch_size,
        hidden_size=in_features,      # in_features (input dimension)
        out_features=out_features,     # out_features (output dimension) - rectangular support!
        alive_registers=[1,2,3,4,5,6],
        w_base_hbm_offset_reg=1,
        activation_base_address=0,
        result_base_address=result_vram_offset,
        rope_enabled=False
    ))

    # Write performance stats
    perf.write_stats()

    create_sim_env(input_tensor, perf.get_code(), golden_result, fp_preload)
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

    print("================================================")
    print("Finished generating assembly code")
    print(f"Result location: row {result_start_row}, {num_result_rows} rows")
    print(f"Comparison params: {comparison_params}")
    print("================================================")
