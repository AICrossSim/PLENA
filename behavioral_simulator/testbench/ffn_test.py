import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import Tensor, nn
# from acc_simulator.quantize.quantized_layers.linear import MXFPLinearPTQ
from test_data_gen import get_weights_path, generate_and_save_random_weights
from compiler.asm_templates import ffn_asm, preload_addr_reg_asm, reset_reg_asm, preload_act_asm
from create_sim_env import create_sim_env
from sim_env_utils import build_sim_env


class LlamaFeedForward(nn.Module):
    """
    Standard FeedForward layer used in Llama architectures:
    y = W2(activation(W1(x)))
    where activation is typically SwiGLU in Llama2.

    Args:
        dim (int): input and output dimension (hidden size)
        inter_dim (int): intermediate/fc dimension
        activation (callable): nonlinearity to use (default: SwiGLU)
    """
    def __init__(self, dim: int, inter_dim: int, activation: str = "silu"):
        super().__init__()
        # Llama uses SwiGLU: x * silu(x)
        self.w1 = nn.Linear(dim, inter_dim, bias=False)
        print("w1:", self.w1.weight.shape)
        self.w2 = nn.Linear(dim, inter_dim, bias=False)
        print("w2:", self.w2.weight.shape)
        self.w3 = nn.Linear(inter_dim, dim, bias=False)
        print("w3:", self.w3.weight.shape)
        self.act = torch.nn.SiLU() if activation == "silu" else getattr(torch.nn, activation)()

    def forward(self, x: Tensor) -> Tensor:
        # SwiGLU: (x @ w1) * silu(x @ w3)
        print("input_tensor:\n", x)
        print("up weight:\n", self.w1.weight.t())
        up_proj = self.w1(x)
        print("up projection (all elements):")
        # INSERT_YOUR_CODE
        w1_out = self.w1(x)
        print("self.w1(x) (all elements):")
        print(w1_out)
        # INSERT_YOUR_CODE
        # Print all elements in w1_out without truncation
        with torch.no_grad():
            torch.set_printoptions(profile="full")
            print("w1_out (all elements):\n", w1_out)
            torch.set_printoptions(profile="default")
        # print("gate projection:\n", self.w2(x))
        # print("silu activation:\n", self.act(self.w1(x)))
        # print("product of silu activation and gate projection:\n", self.act(self.w1(x)) * self.w2(x))
        # print("final output:\n", self.w3(self.act(self.w1(x)) * self.w2(x)))
        return self.w3(self.act(self.w1(x)) * self.w2(x))

if __name__ == "__main__":
    # Testing the operation (hidden_size, hidden_size) @ (hidden_size, batch_size)
    hidden_size = 128
    inter_dim = 256
    batch_size = 4
    real_data_ratio = (8*8 + 8) / (8 * 8)
    fp_preload = [0.0, 1]
    mlen = 64
    blen = 4
    vlen = 64
    seq_len = 2

    torch.manual_seed(42)
    act_tensor = torch.randn(batch_size, seq_len, hidden_size)

    original_layer = LlamaFeedForward(dim=hidden_size, inter_dim=inter_dim)
    weight_up_layer = torch.randn(inter_dim, hidden_size)
    weight_gate_layer = torch.randn(inter_dim, hidden_size)
    weight_down_layer = torch.randn(hidden_size, inter_dim)

    # Set weights for w1, w2, w3 to the generated tensors
    with torch.no_grad():
        original_layer.w1.weight.copy_(weight_up_layer)
        original_layer.w2.weight.copy_(weight_gate_layer)
        original_layer.w3.weight.copy_(weight_down_layer)

    original_output = original_layer(act_tensor)
    print("original_output:", original_output)

    input_tensor = {
        "act_tensor": act_tensor.reshape(batch_size * seq_len, hidden_size),
        "weight_up_layer": weight_up_layer.t(),
        "weight_gate_layer": weight_gate_layer.t(),
        "weight_down_layer": weight_down_layer.t(),
    }

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": original_output
    }

    gen_assembly_code = "; FFN Test Generation \n"

    # Set the addr offset for weight and bias
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1, 2, 3],
        available_registers=[1, 2, 3],
        addr_reg_val=[int(hidden_size * batch_size * seq_len * real_data_ratio), 
        int(hidden_size * batch_size * seq_len * real_data_ratio) + int(hidden_size * inter_dim * real_data_ratio), 
        int(hidden_size * batch_size * seq_len * real_data_ratio) + int(hidden_size * inter_dim * real_data_ratio) + int(inter_dim * hidden_size * real_data_ratio)]
    )

    print("up_addr_hbm_val:", int(hidden_size * batch_size * seq_len * real_data_ratio))
    print("gate_addr_hbm_val:", int(hidden_size * batch_size * seq_len * real_data_ratio) + int(hidden_size * inter_dim * real_data_ratio))
    print("down_addr_hbm_val:", int(hidden_size * batch_size * seq_len * real_data_ratio) + int(hidden_size * inter_dim * real_data_ratio) + int(inter_dim * hidden_size * real_data_ratio))

    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3]
    )

    # Preload Activation
    gen_assembly_code += preload_act_asm(
        vlen=vlen,
        preload_len=4,
        batch=batch_size * seq_len,
        hidden_size=hidden_size,
        alive_registers=[1,2,3],
        act_vram_offset=0,
        activation_offset_reg=0,
        stride_size=hidden_size
    )

    # FFN Generation
    gen_assembly_code += ffn_asm(
        mlen=mlen,
        vlen=vlen,
        blen=blen,
        batch=batch_size,
        seq_len=seq_len,
        hidden_size=hidden_size,
        intermediate_size=inter_dim,
        alive_registers=[1,2,3,4,5,6,7],
        up_weight_hbm_offset_reg=1,
        gate_weight_hbm_offset_reg=2,
        down_weight_hbm_offset_reg=3,
        const_one_fp_address=1,
        activation_base_address=0
    )

    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    build_sim_env(data_size=256, mode="behave_sim", asm=None, data=None, specified_data_order = ["act_tensor", "weight_up_layer", "weight_gate_layer", "weight_down_layer"])