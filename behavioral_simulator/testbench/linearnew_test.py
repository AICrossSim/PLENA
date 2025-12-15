import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import nn
from compiler.asm_templates import projection_asm, preload_act_asm, reset_reg_asm, preload_addr_reg_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim


def pad64(x):
    return ((x + 63) // 64) * 64


if __name__ == "__main__":
    # Testing rectangular linear: (batch, in_features) @ (in_features, out_features) → (batch, out_features)
    in_features = 31
    out_features = 27
    batch_size = 4
    real_data_ratio = (8*8 + 8) / (8 * 8)

    

    torch.manual_seed(42)

    # -----------------------------
    # Original tensors
    # -----------------------------
    act_tensor = torch.randn(batch_size, in_features)
    original_layer = nn.Linear(in_features, out_features, bias=False)
    weights = original_layer.state_dict()

    original_output = original_layer(act_tensor)

    print("Original output shape:", original_output.shape)
    print("Original output:\n", original_output)

    # -----------------------------
    # Minimal padding to satisfy hardware
    # -----------------------------
    # batch_pad = pad64(batch_size)
    batch_pad = batch_size  # do not pad batch for minimal patch
    in_pad = pad64(in_features)
    out_pad = pad64(out_features)
    
    # fp preload used by your env
    fp_preload = [0.0, 1e-6, 1 / in_pad]

    # Pad activations
    act_tensor_pad = torch.zeros(batch_pad, in_pad, dtype=act_tensor.dtype)
    act_tensor_pad[:batch_size, :in_features] = act_tensor

    # Pad weights (layout: PyTorch is (out, in))
    W = weights["weight"]  # shape (out_features, in_features)
    W_pad = torch.zeros(out_pad, in_pad, dtype=W.dtype)
    W_pad[:out_features, :in_features] = W
    
    
    original_output_pad = torch.zeros(batch_pad, out_pad, dtype=original_output.dtype)
    original_output_pad[:batch_size, :out_features] = original_output

    # Our simulator expects (in, out)
    W_pad = W_pad.t()  # final → (in_pad, out_pad)
    
    print("Padded act shape:", act_tensor_pad.shape)
    print("Padded weight shape:", W_pad.shape)
    
    print("Padded act:\n", act_tensor_pad)
    print("Padded weight:\n", W_pad)

    # -----------------------------
    # Feed padded tensors to simulator
    # -----------------------------
    input_tensor = {
        "act_tensor": act_tensor_pad,
        "weights": W_pad,
    }

    golden_result = {
        "input_tensor": input_tensor,
        # We compare only the original non‑padded region in view_mem later
        "original_output": original_output_pad,
    }

    # -----------------------------
    # HBM LAYOUT: [act | weights]
    # -----------------------------
    def align64(x): return ((x + 63) // 64) * 64

    act_hbm_size = int(in_pad * batch_pad* real_data_ratio)
    weight_bytes = W_pad.numel()
    
    
    act_hbm_size = align64(act_hbm_size)
    weight_hbm_size = align64(weight_bytes)


    weight_hbm_offset = act_hbm_size
    weight_hbm_end = int((in_pad * batch_pad + in_pad * out_pad) * real_data_ratio)

    # -----------------------------
    # Build assembly
    # -----------------------------
    gen_assembly_code = "; Linear Test (minimal patch version)\n"
    gen_assembly_code += f"; ORIGINAL: ({batch_size},{in_features}) @ ({in_features},{out_features})\n"
    gen_assembly_code += f"; PADDED  : ({batch_pad},{in_pad}) @ ({in_pad},{out_pad})\n\n"

    # Set HBM weight pointer
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1, 2],
        available_registers=[1, 2],
        addr_reg_val=[weight_hbm_offset, weight_hbm_end],
    )

    gen_assembly_code += reset_reg_asm([1, 2, 3])

    # Preload activation (uses padded dims)
    gen_assembly_code += preload_act_asm(
        vlen=64,
        preload_len=4,
        batch=batch_pad,
        hidden_size=in_pad,
        alive_registers=[1, 2, 3, 4, 5],
        act_vram_offset=0,
        activation_offset_reg=0,
        stride_size=in_pad,
    )

    gen_assembly_code += reset_reg_asm([1, 2, 3, 4])

    # VRAM result buffer starts after activations
    result_vram_offset = in_pad * batch_pad

    # Projection kernel call
    gen_assembly_code += projection_asm(
        mlen=64,
        blen=4,
        batch=batch_pad,
        hidden_size=in_pad,
        out_features=out_pad,
        alive_registers=[1, 2, 3, 4, 5],
        w_base_hbm_offset_reg=1,
        activation_base_address=0,
        result_base_address=result_vram_offset,
        rope_enabled=False,
    )


    # sys.exit(0)
    # -----------------------------
    # Build simulator env
    # -----------------------------
    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)

    # Allocate enough bytes (minimal required)
    total_bytes = act_hbm_size + weight_hbm_size
    create_mem_for_sim(
        data_size=total_bytes,
        mode="behave_sim",
        asm="linear",
        data=None,
        specified_data_order=["act_tensor", "weights"],
    )

    # -----------------------------
    # Result tile rows: correct calculation
    # -----------------------------
    result_start_row = result_vram_offset // 64
    # num_tiles = (out_pad + 4 - 1) // 4  # each tile outputs 4 columns
    num_result_rows = (batch_pad * out_pad) // 64


    comparison_params = {
        "start_row_idx": result_start_row,
        "num_rows": num_result_rows,
        "num_batches": batch_pad,
        "elements_per_batch": out_pad,
    }

    # Save comparison params
    build_dir = Path(__file__).parent / "build"
    build_dir.mkdir(exist_ok=True)

    import json
    with open(build_dir / "comparison_params.json", "w") as f:
        json.dump(comparison_params, f, indent=2)

    with open("behavioral_simulator/testbench/linear_test.asm", "w") as f:
        f.write(gen_assembly_code)

    print("================================================")
    print(" Assembly ready.")
    print(f" Padded shape: ({batch_pad},{in_pad}) @ ({in_pad},{out_pad})")
    print(f" HBM allocated: {total_bytes} bytes")
    print(f" Result rows: {num_result_rows}")
    print("================================================")