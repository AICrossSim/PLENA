import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import argparse
import torch
from torch import Tensor, nn
from test_data_gen import get_weights_path, generate_and_save_random_weights
from compiler.asm_templates import rms_norm_asm, preload_act_asm, reset_reg_asm, preload_addr_reg_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim
from quant.quantizer.hardware_quantizer.mxfp import _mx_fp_quantize_hardware
from config_utils import update_plena_config, get_comparison_params


def quantize_to_mxfp(tensor):
    """
    Quantize tensor to MXFP format matching hardware (E4M3 with 8-bit scale per block of 8).
    """
    orig_shape = tensor.shape
    bm_x, _, _, _ = _mx_fp_quantize_hardware(
        tensor, width=8, exponent_width=4, exponent_bias_width=8, block_size=[8]
    )
    return bm_x.reshape(orig_shape)


# Taken from LLAMA RMSNorm implementation
class RMSNorm(torch.nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        """
        Initialize the RMSNorm normalization layer.

        Args:
            dim (int): The dimension of the input tensor.
            eps (float, optional): A small value added to the denominator for numerical stability. Default is 1e-6.

        Attributes:
            eps (float): A small value added to the denominator for numerical stability.
            weight (nn.Parameter): Learnable scaling parameter.

        """
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def _norm(self, x):
        """
        Apply the RMSNorm normalization to the input tensor.

        Args:
            x (torch.Tensor): The input tensor.

        Returns:
            torch.Tensor: The normalized tensor.

        """
        print("x", x)
        print("x.pow(2)", x.pow(2))
        print("x.pow(2).mean(-1, keepdim=True)", x.pow(2).mean(-1, keepdim=True))

        return x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)

    def forward(self, x):
        """
        Forward pass through the RMSNorm layer.

        Args:
            x (torch.Tensor): The input tensor.

        Returns:
            torch.Tensor: The output tensor after applying RMSNorm.

        """
        output = self._norm(x.float()).type_as(x)
        return output * self.weight


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RMSNorm test for behavioral simulator")
    parser.add_argument("--n", type=int, default=None, help="Total elements (batch * hidden)")
    parser.add_argument("--hidden", type=int, default=None, help="Hidden size")
    parser.add_argument("--config", type=str, default="C1",
                        choices=["C1", "C2", "C3", "C4", "C5"],
                        help="PLENA workload config")
    args = parser.parse_args()

    # RMSNorm workload configurations: (n, hidden_size)
    # n = total elements = batch_size * hidden_size
    RMS_CONFIGS = {
        "C1": (256, 64),      # batch=4
        "C2": (512, 128),     # batch=4
        "C3": (1024, 256),    # batch=4
        "C4": (2048, 512),    # batch=4
        "C5": (4096, 1024),   # batch=4
    }

    # Use explicit args if provided, otherwise use config preset
    if args.n is not None and args.hidden is not None:
        n_total = args.n
        hidden_size = args.hidden
        print(f"Using custom config: n={n_total}, hidden={hidden_size}")
    else:
        n_total, hidden_size = RMS_CONFIGS[args.config]
        print(f"Using PLENA config {args.config}: n={n_total}, hidden={hidden_size}")

    # Derive batch_size from n and hidden_size
    batch_size = n_total // hidden_size
    assert batch_size * hidden_size == n_total, f"n={n_total} must be divisible by hidden={hidden_size}"
    assert batch_size >= 1, "batch_size must be at least 1"

    real_data_ratio = (8*8 + 8) / (8 * 8)
    fp_preload = [0.0, 1e-6, 1/hidden_size]
    vlen = 64

    # Gen Weight and Test Data
    # generate_and_save_random_weights(hidden_size, hidden_size, get_weights_path('model_weights.pt'))

    torch.manual_seed(42)
    act_tensor = torch.randn(batch_size, hidden_size, dtype=torch.bfloat16)
    # Print input_tensor split in half along columns, as two (4, 64) tensors
    print("act_tensor lhs (4, 64):\n", act_tensor[:, :64])
    print("act_tensor rhs (4, 64):\n", act_tensor[:, 64:])

    original_layer = RMSNorm(dim=hidden_size)
    weights = original_layer.state_dict()

    # Quantize input to MXFP to match hardware precision
    act_mxfp = quantize_to_mxfp(act_tensor).to(act_tensor.dtype)

    input_tensor = {
        "act_tensor": act_tensor,
        "weights": weights['weight'].t(),
    }

    # Compute golden with MXFP-quantized input
    original_output = original_layer(act_mxfp)

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": original_output
    }

    gen_assembly_code = "; RMSNorm Test Generation \n"

    # print("hidden_size * batch_size * real_data_ratio", hidden_size * batch_size * real_data_ratio)
    # print("(hidden_size * (batch_size + 1) + hidden_size * hidden_size) * real_data_ratio", (hidden_size * (batch_size + 1) + hidden_size * hidden_size) * real_data_ratio)


    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3]
    )

    # Gen Activation Preload
    gen_assembly_code += preload_act_asm(
        vlen=vlen,
        preload_len=4,
        batch=batch_size,
        hidden_size=hidden_size,
        alive_registers=[1,2,3,4,5],
        act_vram_offset=0,
        activation_offset_reg=0,
        stride_size=hidden_size
    )

    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3,4]
    )

    gen_assembly_code += rms_norm_asm(
        _eps_offset=1,
        reci_hid_offset=2,
        alive_registers=[1,2,3,4,5],
        activation_base_address = 0,
        scratchpad_base_address = hidden_size * batch_size,
        vlen=vlen,
        batch_size=batch_size,
        hidden_dim=hidden_size
    )

    # Update plena_settings.toml with test-specific vlen/mlen
    update_plena_config(vlen=vlen, mlen=vlen)

    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    create_mem_for_sim(data_size=256, mode="behave_sim", asm="rms", data=None, specified_data_order = ["act_tensor", "weights"])

    # Save comparison parameters for view_mem.py
    # RMS stores result at activation_base_address (overwrites input in-place)
    import json
    result_vram_offset = 0  # activation_base_address
    comparison_params = get_comparison_params(
        vlen=vlen,
        batch_size=batch_size,
        hidden_size=hidden_size,
        result_vram_offset=result_vram_offset
    )
    build_dir = Path(__file__).parent / "build"
    with open(build_dir / "comparison_params.json", "w") as f:
        json.dump(comparison_params, f, indent=2)

    print("================================================")
    print("Finished generating assembly code")
    print(f"Result location: row {comparison_params['start_row_idx']}, {comparison_params['num_rows']} rows")
    print(f"Comparison params: {comparison_params}")
    print("================================================")
