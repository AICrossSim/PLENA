import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import argparse
import torch
from torch import Tensor, nn
from compiler.asm_templates import ffn_asm, preload_addr_reg_asm, reset_reg_asm, preload_act_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim
from quant.quantizer.hardware_quantizer.mxfp import _mx_fp_quantize_hardware
from config_utils import update_plena_config, get_comparison_params


def quantize_to_mxfp(tensor):
    """
    Quantize tensor to MXFP format matching hardware (E4M3 with 8-bit scale per block of 8).
    Uses the same quantizer as the behavioral simulator's memory loader.
    Returns the dequantized tensor (what hardware sees after HBM->VRAM load).
    """
    orig_shape = tensor.shape
    # Hardware quantizer expects 2D input, flatten all but last dim
    tensor_2d = tensor.reshape(-1, tensor.shape[-1])
    bm_x, _, _, _ = _mx_fp_quantize_hardware(
        tensor_2d, width=8, exponent_width=4, exponent_bias_width=8, block_size=[8]
    )
    return bm_x.reshape(orig_shape)


class LlamaFeedForward(nn.Module):
    """
    Standard FeedForward layer used in Llama architectures:
    y = W3(activation(W1(x)) * W2(x))
    where activation is SwiGLU in Llama2.
    """
    def __init__(self, dim: int, inter_dim: int):
        super().__init__()
        self.w1 = nn.Linear(dim, inter_dim, bias=False)  # up projection
        self.w2 = nn.Linear(dim, inter_dim, bias=False)  # gate projection
        self.w3 = nn.Linear(inter_dim, dim, bias=False)  # down projection
        self.act = torch.nn.SiLU()

    def forward(self, x: Tensor) -> Tensor:
        return self.w3(self.act(self.w1(x)) * self.w2(x))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FFN testbench configuration")
    parser.add_argument("--hidden-size", type=int, default=128, help="Hidden size (model dim)")
    parser.add_argument("--inter-dim", type=int, default=256, help="Intermediate FFN dimension")
    parser.add_argument("--batch-size", type=int, default=4, help="Batch size")
    parser.add_argument("--seq-len", type=int, default=2, help="Sequence length")
    parser.add_argument("--vlen", type=int, default=64, help="Vector length")
    parser.add_argument("--mlen", type=int, default=64, help="Matrix tile length")
    parser.add_argument("--blen", type=int, default=4, help="Batch tile length")
    args = parser.parse_args()

    hidden_size = args.hidden_size
    inter_dim = args.inter_dim
    batch_size = args.batch_size
    seq_len = args.seq_len
    real_data_ratio = (8*8 + 8) / (8 * 8)
    fp_preload = [0.0, 1.0]  # [0]=0.0, [1]=1.0 for SiLU
    mlen = args.mlen
    blen = args.blen
    vlen = args.vlen
    hbm_m_prefetch_amount = mlen

    torch.manual_seed(42)
    act_tensor = torch.randn(batch_size, seq_len, hidden_size, dtype=torch.bfloat16)

    ffn = LlamaFeedForward(dim=hidden_size, inter_dim=inter_dim).bfloat16()

    weight_up_layer = torch.randn(inter_dim, hidden_size, dtype=torch.bfloat16)
    weight_gate_layer = torch.randn(inter_dim, hidden_size, dtype=torch.bfloat16)
    weight_down_layer = torch.randn(hidden_size, inter_dim, dtype=torch.bfloat16)

    # Quantize all inputs to MXFP to match hardware precision
    act_mxfp = quantize_to_mxfp(act_tensor).to(act_tensor.dtype)
    weight_up_mxfp = quantize_to_mxfp(weight_up_layer).to(act_tensor.dtype)
    weight_gate_mxfp = quantize_to_mxfp(weight_gate_layer).to(act_tensor.dtype)
    weight_down_mxfp = quantize_to_mxfp(weight_down_layer).to(act_tensor.dtype)

    # Set quantized weights
    with torch.no_grad():
        ffn.w1.weight.copy_(weight_up_mxfp)
        ffn.w2.weight.copy_(weight_gate_mxfp)
        ffn.w3.weight.copy_(weight_down_mxfp)

    # Compute golden with MXFP-quantized inputs
    original_output = ffn(act_mxfp)

    input_tensor = {
        "act_tensor": act_tensor.reshape(batch_size * seq_len, hidden_size),
        "weight_up_layer": weight_up_layer.t(),
        "weight_gate_layer": weight_gate_layer.t(),
        "weight_down_layer": weight_down_layer.t(),
    }

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": original_output.flatten()
    }

    gen_assembly_code = "; FFN Test Generation \n"

    # Set the addr offset for weights
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1, 2, 3],
        available_registers=[1, 2, 3],
        addr_reg_val=[
            int(hidden_size * batch_size * seq_len * real_data_ratio),
            int(hidden_size * batch_size * seq_len * real_data_ratio) + int(hidden_size * inter_dim * real_data_ratio),
            int(hidden_size * batch_size * seq_len * real_data_ratio) + int(hidden_size * inter_dim * real_data_ratio) + int(inter_dim * hidden_size * real_data_ratio)
        ]
    )

    # Reset the registers
    gen_assembly_code += reset_reg_asm(alive_registers=[1,2,3])

    # Preload Activation
    gen_assembly_code += preload_act_asm(
        vlen=vlen,
        preload_len=4,
        batch=batch_size * seq_len,
        hidden_size=hidden_size,
        alive_registers=[1,2,3,4,5],
        act_vram_offset=0,
        activation_offset_reg=0,
        stride_size=hidden_size
    )

    # FFN with loop instructions
    gen_assembly_code += ffn_asm(
        mlen=mlen,
        vlen=vlen,
        blen=blen,
        batch=batch_size,
        seq_len=seq_len,
        hidden_size=hidden_size,
        intermediate_size=inter_dim,
        alive_registers=[1,2,3,4,5,6,7,8,9,10],
        up_weight_hbm_offset_reg=1,
        gate_weight_hbm_offset_reg=2,
        down_weight_hbm_offset_reg=3,
        const_one_fp_address=1,
        activation_base_address=0,
        use_loop_instructions=True
    )

    # Update plena_settings.toml with test-specific vlen/mlen/blen and prefetch amount
    update_plena_config(
        vlen=vlen,
        mlen=mlen,
        blen=blen,
        hbm_m_prefetch_amount=hbm_m_prefetch_amount
    )

    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    create_mem_for_sim(data_size=256, mode="behave_sim", asm=None, data=None,
                       specified_data_order=["act_tensor", "weight_up_layer", "weight_gate_layer", "weight_down_layer"])

    # Save comparison parameters for view_mem.py
    import json
    effective_batch = batch_size * seq_len
    result_vram_offset = 0
    comparison_params = get_comparison_params(
        vlen=vlen,
        batch_size=effective_batch,
        hidden_size=hidden_size,
        result_vram_offset=result_vram_offset
    )
    build_dir = Path(__file__).parent / "build"
    with open(build_dir / "comparison_params.json", "w") as f:
        json.dump(comparison_params, f, indent=2)

    print("================================================")
    print("Finished generating FFN test assembly code")
    print(f"Result location: row {comparison_params['start_row_idx']}, {comparison_params['num_rows']} rows")
    print(f"Comparison params: {comparison_params}")
    print("================================================")
