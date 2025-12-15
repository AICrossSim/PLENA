import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import nn
from compiler.asm_templates import projection_asm, preload_act_asm, reset_reg_asm, preload_addr_reg_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim

if __name__ == "__main__":
    # Conv2d parameters
    batch = 1
    in_channels = 3
    out_channels = 4
    kernel_size = 3
    input_h = input_w = 16
    stride = 1
    padding = 1
    
    # Hardware parameters
    mlen = 64
    blen = 4
    vlen = 64
    
    torch.manual_seed(42)
    
    # ============================================================
    # STEP 1: Original Conv2d and Im2col
    # ============================================================
    input_tensor_4d = torch.randn(batch, in_channels, input_h, input_w)
    conv_layer = nn.Conv2d(in_channels, out_channels, kernel_size, 
                          stride=stride, padding=padding, bias=False)
    
    golden_output = conv_layer(input_tensor_4d)
    output_h = output_w = (input_h + 2*padding - kernel_size) // stride + 1
    
    print("="*60)
    print("Original Conv2d:")
    print(f"  Input:  ({batch}, {in_channels}, {input_h}, {input_w})")
    print(f"  Output: ({batch}, {out_channels}, {output_h}, {output_w})")
    print(f"  Kernel: {kernel_size}×{kernel_size}, stride={stride}, padding={padding}")
    print("="*60)
    
    # Im2col transformation
    input_unfolded = torch.nn.functional.unfold(
        input_tensor_4d, 
        kernel_size=(kernel_size, kernel_size),
        padding=padding,
        stride=stride
    )
    
    in_features = in_channels * kernel_size * kernel_size  # K = 27
    num_patches = output_h * output_w  # 64
    effective_batch = batch * num_patches  # M = 64
    
    # Activation: (M, K)
    act_matrix = input_unfolded.transpose(1, 2).reshape(effective_batch, in_features)
    
    # Weight: (K, N)
    weight_matrix = conv_layer.weight.reshape(out_channels, in_features).t()
    
    print("\nIm2col Transformation:")
    print(f"  Activation matrix (M, K): {act_matrix.shape}")
    print(f"  Weight matrix (K, N):     {weight_matrix.shape}")
    print(f"  M = {effective_batch}, K = {in_features}, N = {out_channels}")
    
    # Verify im2col correctness
    matmul_result = act_matrix @ weight_matrix
    matmul_output = matmul_result.reshape(batch, output_h, output_w, out_channels)
    matmul_output = matmul_output.permute(0, 3, 1, 2)
    
    print(f"\nIm2col verification:")
    print(f"  Max diff: {(golden_output - matmul_output).abs().max().item():.2e}")
    print(f"  Match: {torch.allclose(golden_output, matmul_output, atol=1e-5)}")
    
    if not torch.allclose(golden_output, matmul_output, atol=1e-5):
        print("ERROR: Im2col transformation is incorrect!")
        sys.exit(1)
    
    # ============================================================
    # STEP 2: Padding to 64-multiples (same as linear_test)
    # ============================================================
    in_features_padded = ((in_features + 63) // 64) * 64
    out_features_padded = ((out_channels + 63) // 64) * 64
    effective_batch_padded = ((effective_batch + blen - 1) // blen) * blen
    
    print("\n" + "="*60)
    print("Padding to 64-multiples:")
    print(f"  K: {in_features} -> {in_features_padded}")
    print(f"  N: {out_channels} -> {out_features_padded}")
    print(f"  M: {effective_batch} -> {effective_batch_padded} (blen={blen})")
    print("="*60)
    
    # sys.exit(0)  # IGNORE
    # Pad tensors
    act_tensor_padded = torch.nn.functional.pad(
        act_matrix, 
        (0, in_features_padded - in_features, 0, effective_batch_padded - effective_batch)
    )
    
    weight_tensor_padded = torch.nn.functional.pad(
        weight_matrix,
        (0, out_features_padded - out_channels, 0, in_features_padded - in_features)
    )
    
    print(f"\nPadded matrices:")
    print(f"  act_tensor_padded:    {act_tensor_padded.shape}")
    print(f"  weight_tensor_padded: {weight_tensor_padded.shape}")
    
    # ============================================================
    # STEP 3: Generate assembly (EXACTLY like linear_test)
    # ============================================================
    real_data_ratio = (8*8 + 8) / (8 * 8)
    fp_preload = [0.0, 1e-6, 1/in_features_padded]
    
    input_tensor = {
        "act_tensor": act_tensor_padded,
        "weights": weight_tensor_padded.t(),
    }

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": golden_output
    }

    gen_assembly_code = "; Conv2d via Im2col\n"
    gen_assembly_code += f"; Original: ({batch}, {in_channels}, {input_h}, {input_w}) -> ({batch}, {out_channels}, {output_h}, {output_w})\n"
    gen_assembly_code += f"; Matmul: ({effective_batch_padded}, {in_features_padded}) @ ({in_features_padded}, {out_features_padded})\n"

    # Calculate HBM offsets (EXACTLY like linear_test)
    act_hbm_size = int(in_features_padded * effective_batch_padded * real_data_ratio)
    weight_hbm_offset = act_hbm_size
    weight_hbm_end = int((in_features_padded * effective_batch_padded + in_features_padded * out_features_padded) * real_data_ratio)

    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1, 2],
        available_registers=[1, 2],
        addr_reg_val=[weight_hbm_offset, weight_hbm_end]
    )

    gen_assembly_code += reset_reg_asm(alive_registers=[1,2,3])

    # Preload activations
    gen_assembly_code += preload_act_asm(
        vlen=vlen,
        preload_len=blen,
        batch=effective_batch_padded,
        hidden_size=in_features_padded,
        alive_registers=[1,2,3,4,5],
        act_vram_offset=0,
        activation_offset_reg=0,
        stride_size=in_features_padded
    )

    gen_assembly_code += reset_reg_asm(alive_registers=[1,2,3,4])

    # Result offset (EXACTLY like linear_test)
    result_vram_offset = in_features_padded * effective_batch_padded

    # Projection (NO real_data_ratio parameter!)
    gen_assembly_code += projection_asm(
        mlen=mlen,
        blen=blen,
        batch=effective_batch_padded,
        hidden_size=in_features_padded,
        out_features=out_features_padded,
        alive_registers=[1,2,3,4,5],
        w_base_hbm_offset_reg=1,
        activation_base_address=0,
        result_base_address=result_vram_offset,
        rope_enabled=False
    )

    # Save assembly
    asm_path = Path("behavioral_simulator/testbench/conv2d_im2col_test.asm")
    asm_path.parent.mkdir(parents=True, exist_ok=True)
    with open(asm_path, "w") as f:
        f.write(gen_assembly_code)

    # Save comparison parameters (EXACTLY like linear_test)
    import json
    result_start_row = result_vram_offset // vlen
    num_result_rows = (effective_batch_padded * out_features_padded) // vlen
    comparison_params = {
        "start_row_idx": result_start_row,
        "num_rows": num_result_rows,
        "num_batches": effective_batch_padded,
        "elements_per_batch": out_features_padded,
        "original_batch": batch,
        "original_channels": out_channels,
        "output_h": output_h,
        "output_w": output_w
    }
    
    build_dir = Path(__file__).parent / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    with open(build_dir / "comparison_params.json", "w") as f:
        json.dump(comparison_params, f, indent=2)

    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    create_mem_for_sim(
        data_size=256,
        mode="behave_sim", 
        asm="conv2d_im2col", 
        data=None, 
        specified_data_order=["act_tensor", "weights"]
    )

    print("\n" + "="*60)
    print("Finished generating conv2d test")
    print(f"Assembly saved to: {asm_path}")
    print(f"Result location: row {result_start_row}, {num_result_rows} rows")
    print("="*60)