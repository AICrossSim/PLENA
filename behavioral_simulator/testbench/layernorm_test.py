import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import Tensor, nn
# from acc_simulator.quantize.quantized_layers.linear import MXFPLinearPTQ
from test_data_gen import get_weights_path, generate_and_save_random_weights
from compiler.asm_templates import layer_norm_asm, preload_act_asm, reset_reg_asm, preload_addr_reg_asm
from create_sim_env import create_sim_env
from sim_env_utils import build_sim_env


# Taken from standard LayerNorm implementation
class LayerNorm(torch.nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        """
        Initialize the LayerNorm normalization layer.

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
        Apply the LayerNorm normalization to the input tensor.

        Args:
            x (torch.Tensor): The input tensor.

        Returns:
            torch.Tensor: The normalized tensor.

        """
        print("x", x)
        mean = x.mean(-1, keepdim=True)
        print("mean", mean)
        var = x.var(-1, keepdim=True, unbiased=False)
        print("var", var)
        x_normalized = (x - mean) / torch.sqrt(var + self.eps)
        print("x_normalized", x_normalized)

        return x_normalized

    def forward(self, x):
        """
        Forward pass through the LayerNorm layer.

        Args:
            x (torch.Tensor): The input tensor.

        Returns:
            torch.Tensor: The output tensor after applying LayerNorm.

        """
        output = self._norm(x.float()).type_as(x)
        return output * self.weight

if __name__ == "__main__":
    # Testing the operation (hidden_size, hidden_size) @ (hidden_size, batch_size)
    hidden_size = 128
    batch_size = 4
    real_data_ratio = (8*8 + 8) / (8 * 8)
    fp_preload = [0.0, 1e-6, 1/hidden_size]

    # Gen Weight and Test Data
    # generate_and_save_random_weights(hidden_size, hidden_size, get_weights_path('model_weights.pt'))

    torch.manual_seed(42)
    act_tensor = torch.randn(batch_size, hidden_size)
    # Print input_tensor split in half along columns, as two (4, 64) tensors
    print("act_tensor lhs (4, 64):\n", act_tensor[:, :64])
    print("act_tensor rhs (4, 64):\n", act_tensor[:, 64:])

    original_layer = LayerNorm(dim=hidden_size)
    weights = original_layer.state_dict()

    input_tensor = {
        "act_tensor": act_tensor,
        "weights": weights['weight'].t(),
    }

    original_output = original_layer(act_tensor)

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": original_output
    }

    gen_assembly_code = "; LayerNorm Test Generation \n"

    # print("hidden_size * batch_size * real_data_ratio", hidden_size * batch_size * real_data_ratio)
    # print("(hidden_size * (batch_size + 1) + hidden_size * hidden_size) * real_data_ratio", (hidden_size * (batch_size + 1) + hidden_size * hidden_size) * real_data_ratio)


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
        alive_registers=[1,2,3],
        act_vram_offset=0,
        activation_offset_reg=0,
        stride_size=hidden_size
    )

    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3]
    )

    gen_assembly_code += layer_norm_asm(
        _eps_offset=1,
        reci_hid_offset=2,
        alive_registers=[1,2,3,4],
        activation_base_address = 0,
        scratchpad_base_address = hidden_size * batch_size,
        vlen=64,
        batch_size=4,
        hidden_dim=128
    )

    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    build_sim_env(data_size=256, mode="behave_sim", asm="layernorm", data=None, specified_data_order = ["act_tensor", "weights"])

    print("================================================")
    print("Finished generating assembly code")
    print("================================================")