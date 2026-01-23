"""FFN test matching KernelCraft workload definition.

FFN = Linear -> SiLU -> Linear (2 weight matrices)
Formula: Y = W_down @ silu(W_up @ X)

For SwiGLU (3 weights), see swiglu_test.py
"""
import sys
from pathlib import Path
source_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, source_root)
sys.path.insert(0, str(Path(source_root) / "tools"))

import argparse
import json
import torch
import torch.nn.functional as F
from torch import Tensor, nn
from compiler.asm_templates import preload_addr_reg_asm, reset_reg_asm, preload_act_asm
from compiler.asm_templates.projection_asm import projection_asm
from compiler.asm_templates.silu_asm import silu_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim
from quant.quantizer.hardware_quantizer.mxfp import _mx_fp_quantize_hardware


def quantize_to_mxfp(tensor):
    """
    Quantize tensor to MXFP format matching hardware (E4M3 with 8-bit scale per block of 8).
    Returns the dequantized tensor (what hardware sees after HBM->VRAM load).
    """
    orig_shape = tensor.shape
    tensor_2d = tensor.reshape(-1, tensor.shape[-1])
    bm_x, _, _, _ = _mx_fp_quantize_hardware(
        tensor_2d, width=8, exponent_width=4, exponent_bias_width=8, block_size=[8]
    )
    return bm_x.reshape(orig_shape)


class FFN(nn.Module):
    """
    2-weight FFN: Y = W_down @ silu(W_up @ X)

    Matches kernel_agents/workloads/ml/ffn.py
    """
    def __init__(self, hidden_size: int, intermediate_size: int):
        super().__init__()
        self.w_up = nn.Linear(hidden_size, intermediate_size, bias=False)
        self.w_down = nn.Linear(intermediate_size, hidden_size, bias=False)
        self.act = torch.nn.SiLU()

    def forward(self, x: Tensor) -> Tensor:
        return self.w_down(self.act(self.w_up(x)))

    def forward_with_bf16_intermediates(self, x: Tensor) -> Tensor:
        """
        Forward pass matching hardware: float32 accumulation, BF16 intermediate storage.
        Each stage writes to VRAM (BF16), causing precision loss that accumulates.
        """
        x_f32 = x.float()
        w_up_f32, w_down_f32 = self.w_up.weight.float(), self.w_down.weight.float()

        # Stage 1: up projection
        up_out = F.linear(x_f32, w_up_f32).to(torch.bfloat16)

        # Stage 2: SiLU activation
        silu_out = self.act(up_out.float()).to(torch.bfloat16)

        # Stage 3: down projection
        return F.linear(silu_out.float(), w_down_f32).to(torch.bfloat16)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FFN (2-weight) test for behavioral simulator")
    parser.add_argument("--batch", type=int, default=None, help="Batch size")
    parser.add_argument("--hidden", type=int, default=None, help="Hidden size")
    parser.add_argument("--inter", type=int, default=None, help="Intermediate size")
    parser.add_argument("--config", type=str, default="default",
                        choices=["default", "C1", "C2", "C3"],
                        help="Configuration preset")
    args = parser.parse_args()

    # FFN configurations matching KernelCraft
    # (batch, hidden_size, intermediate_size)
    FFN_CONFIGS = {
        "default": (4, 128, 512),   # KernelCraft default
        "C1": (4, 64, 256),
        "C2": (4, 128, 512),
        "C3": (8, 256, 1024),
    }

    # Use explicit args if provided, otherwise use config preset
    if args.batch is not None and args.hidden is not None and args.inter is not None:
        batch_size, hidden_size, intermediate_size = args.batch, args.hidden, args.inter
        print(f"Using custom config: batch={batch_size}, hidden={hidden_size}, inter={intermediate_size}")
    else:
        batch_size, hidden_size, intermediate_size = FFN_CONFIGS[args.config]
        print(f"Using config '{args.config}': batch={batch_size}, hidden={hidden_size}, inter={intermediate_size}")

    # Hardware parameters
    real_data_ratio = (8*8 + 8) / (8 * 8)  # 1.125 for MXFP overhead
    fp_preload = [0.0, 1.0]  # [0]=0.0, [1]=1.0 for SiLU
    mlen = 64
    blen = 4
    vlen = 64

    torch.manual_seed(42)
    act_tensor = torch.randn(batch_size, hidden_size, dtype=torch.bfloat16)

    ffn = FFN(hidden_size=hidden_size, intermediate_size=intermediate_size).bfloat16()

    # Use Xavier/Glorot initialization to keep values in reasonable range
    scale_up = 1.0 / (hidden_size ** 0.5)
    scale_down = 1.0 / (intermediate_size ** 0.5)
    weight_up = torch.randn(intermediate_size, hidden_size, dtype=torch.bfloat16) * scale_up
    weight_down = torch.randn(hidden_size, intermediate_size, dtype=torch.bfloat16) * scale_down

    # Quantize all inputs to MXFP to match hardware precision
    act_mxfp = quantize_to_mxfp(act_tensor).to(act_tensor.dtype)
    weight_up_mxfp = quantize_to_mxfp(weight_up).to(act_tensor.dtype)
    weight_down_mxfp = quantize_to_mxfp(weight_down).to(act_tensor.dtype)

    # Set quantized weights
    with torch.no_grad():
        ffn.w_up.weight.copy_(weight_up_mxfp)
        ffn.w_down.weight.copy_(weight_down_mxfp)

    # Compute golden with MXFP-quantized inputs and BF16 intermediates
    original_output = ffn.forward_with_bf16_intermediates(act_mxfp)

    # Weights transposed for PLENA memory layout: [in_features, out_features]
    input_tensor = {
        "act_tensor": act_mxfp,
        "weight_up": weight_up_mxfp.t(),      # [hidden_size, intermediate_size]
        "weight_down": weight_down_mxfp.t(),  # [intermediate_size, hidden_size]
    }

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": original_output.flatten()
    }

    # HBM memory layout:
    # [0, act_size): activations
    # [act_size, act_size + up_size): up weights
    # [act_size + up_size, ...): down weights
    act_size = int(batch_size * hidden_size * real_data_ratio)
    up_size = int(hidden_size * intermediate_size * real_data_ratio)

    gen_assembly_code = "; FFN Test Generation\n"
    gen_assembly_code += "; Formula: Y = W_down @ silu(W_up @ X)\n"
    gen_assembly_code += f"; Config: batch={batch_size}, hidden={hidden_size}, intermediate={intermediate_size}\n\n"

    # Set addr registers for weights
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1, 2],
        available_registers=[1, 2],
        addr_reg_val=[
            act_size,             # a1 -> up weights
            act_size + up_size,   # a2 -> down weights
        ]
    )

    # Reset registers
    gen_assembly_code += reset_reg_asm(alive_registers=[1, 2, 3, 4, 5, 6, 7, 8])

    # Preload activations from HBM to VRAM
    gen_assembly_code += preload_act_asm(
        vlen=vlen,
        preload_len=1,
        batch=batch_size,
        hidden_size=hidden_size,
        alive_registers=[1, 2, 3, 4, 5],
        act_vram_offset=0,
        activation_offset_reg=0,
        stride_size=hidden_size
    )

    # VRAM layout:
    # [0, batch*hidden): input
    # [batch*hidden, batch*hidden + batch*intermediate): up output
    # Final output overwrites input at [0, batch*hidden)
    input_vram = 0
    up_out_vram = batch_size * hidden_size
    output_vram = 0

    # Stage 1: Up projection
    gen_assembly_code += "\n; Stage 1: Up Projection\n"
    gen_assembly_code += projection_asm(
        mlen=mlen,
        blen=blen,
        batch=batch_size,
        hidden_size=hidden_size,
        alive_registers=[1, 2, 3, 4, 5, 6],
        w_base_hbm_offset_reg=1,
        activation_base_address=input_vram,
        result_base_address=up_out_vram,
        out_features=intermediate_size,
    )

    # Stage 2: SiLU activation
    gen_assembly_code += "\n; Stage 2: SiLU Activation\n"
    gen_assembly_code += silu_asm(
        const_one_fp_address=1,
        alive_registers=[1, 2, 3],
        activation_base_address=up_out_vram,
        scratchpad_base_address=input_vram,
        vlen=vlen,
        batch_size=batch_size,
        hidden_dim=intermediate_size,
    )

    # Stage 3: Down projection
    gen_assembly_code += "\n; Stage 3: Down Projection\n"
    gen_assembly_code += projection_asm(
        mlen=mlen,
        blen=blen,
        batch=batch_size,
        hidden_size=intermediate_size,
        alive_registers=[1, 2, 3, 4, 5, 6],
        w_base_hbm_offset_reg=2,
        activation_base_address=up_out_vram,
        result_base_address=output_vram,
        out_features=hidden_size,
    )

    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    create_mem_for_sim(data_size=256, mode="behave_sim", asm=None, data=None,
                       specified_data_order=["act_tensor", "weight_up", "weight_down"])

    # Save comparison parameters
    result_start_row = output_vram // vlen
    num_result_rows = (batch_size * hidden_size) // vlen
    comparison_params = {
        "start_row_idx": result_start_row,
        "num_rows": num_result_rows,
        "num_batches": batch_size,
        "elements_per_batch": hidden_size
    }
    build_dir = Path(__file__).parent / "build"
    with open(build_dir / "comparison_params.json", "w") as f:
        json.dump(comparison_params, f, indent=2)

    print("================================================")
    print("FFN test generated")
    print(f"Config: batch={batch_size}, hidden={hidden_size}, intermediate={intermediate_size}")
    print(f"Result: row {result_start_row}, {num_result_rows} rows")
    print("================================================")
