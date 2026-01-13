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
    out_features = 256  # Rectangular matrix test
    batch_size = 8
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
        alive_registers=[1,2,3,4,5,6],
        w_base_hbm_offset_reg=1,
        activation_base_address=0,
        result_base_address=result_vram_offset,
        rope_enabled=False
    )

    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3,4,5,6]
    )

    # Set up HBM address register for storing results
    # Store results to HBM after weights
    result_hbm_offset = weight_hbm_end
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[3],
        available_registers=[3],
        addr_reg_val=[result_hbm_offset]
    )

    # Set stride register for storing (hidden_size for batch-wise storage)
    gen_assembly_code += f"S_ADDI_INT gp7, gp0, {in_features}\n"
    gen_assembly_code += f"C_SET_STRIDE_REG gp7\n"

    # Set scale register (required for mx data type)
    # Scale offset = batch * hidden_size for activations
    scale_offset = int(batch_size * out_features * real_data_ratio)
    gen_assembly_code += f"S_ADDI_INT gp8, gp0, {scale_offset}\n"
    gen_assembly_code += f"C_SET_SCALE_REG gp8\n"

    # Store results from VRAM to HBM using H_STORE_V
    # H_STORE_V rd, rs1, rs2, rstride, precision
    # rd: VRAM source address (result_vram_offset)
    # rs1: HBM offset (0, relative to a3 base)
    # rs2: HBM address register (a3)
    # rstride: 1 (use STRIDE_REG)
    # precision: 0 (Activation)
    gen_assembly_code += f"S_ADDI_INT gp9, gp0, {result_vram_offset}\n"  # VRAM source
    gen_assembly_code += f"S_ADDI_INT gp10, gp0, 0\n"  # HBM offset (0, relative to a3)
    
    # Calculate number of H_STORE_V calls needed
    # Each H_STORE_V stores STORE_V_AMOUNT * VLEN elements
    # We need to store batch_size * out_features elements
    vlen = 64
    store_v_amount = 16  # HBM_V_Writeback_Amount (typically same as batch_size)
    total_elements = batch_size * out_features
    num_store_calls = (total_elements + store_v_amount * vlen - 1) // (store_v_amount * vlen)
    
    # Store results in chunks
    for i in range(num_store_calls):
        vram_addr = result_vram_offset + i * store_v_amount * vlen
        hbm_offset = i * store_v_amount * vlen
        gen_assembly_code += f"S_ADDI_INT gp9, gp0, {vram_addr}\n"
        gen_assembly_code += f"S_ADDI_INT gp10, gp0, {hbm_offset}\n"
        gen_assembly_code += f"H_STORE_V gp9, gp10, a3, 1, 0\n"  # Store with stride

    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    create_mem_for_sim(data_size=256, mode="behave_sim", asm="h_store", data=None, specified_data_order=["act_tensor", "weights"])

    # Save comparison parameters for checking HBM content
    import json
    result_hbm_start_byte = result_hbm_offset
    result_hbm_size_bytes = int(batch_size * out_features * real_data_ratio)
    comparison_params = {
        "result_hbm_start_byte": result_hbm_start_byte,
        "result_hbm_size_bytes": result_hbm_size_bytes,
        "num_batches": batch_size,
        "elements_per_batch": out_features,
        "vlen": vlen,
        "store_v_amount": store_v_amount
    }
    build_dir = Path(__file__).parent / "build"
    with open(build_dir / "h_store_comparison_params.json", "w") as f:
        json.dump(comparison_params, f, indent=2)

    print("================================================")
    print("Finished generating assembly code")
    print(f"Result HBM location: byte {result_hbm_start_byte}, size {result_hbm_size_bytes} bytes")
    print(f"Comparison params: {comparison_params}")
    print("================================================")
