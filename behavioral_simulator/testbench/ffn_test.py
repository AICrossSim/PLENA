import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import Tensor, nn
# from acc_simulator.quantize.quantized_layers.linear import MXFPLinearPTQ
from test_data_gen import get_weights_path, generate_and_save_random_weights
from compiler.asm_templates import batched_matmul_asm, preload_addr_reg_asm, reset_reg_asm
from create_sim_env import create_sim_env
from sim_env_utils import build_fake_sim_env


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
        self.w3 = nn.Linear(dim, inter_dim, bias=False)  # for SwiGLU, "gate" proj
        self.w2 = nn.Linear(inter_dim, dim, bias=False)
        self.act = torch.nn.SiLU() if activation == "silu" else getattr(torch.nn, activation)()

    def forward(self, x: Tensor) -> Tensor:
        # SwiGLU: (x @ w1) * silu(x @ w3)
        return self.w2(self.act(self.w1(x)) * self.w3(x))

