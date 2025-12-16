import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import Tensor, nn
# from acc_simulator.quantize.quantized_layers.linear import MXFPLinearPTQ
from test_data_gen import get_weights_path, generate_and_save_random_weights
from compiler.asm_templates import ffn_asm, preload_addr_reg_asm, reset_reg_asm, preload_act_asm, rms_norm_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim


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
    act_tensor = torch.rand(batch_size, seq_len, hidden_size)

    ffn = LlamaFeedForward(dim=hidden_size, inter_dim=inter_dim)
    rms_norm = RMSNorm(dim=hidden_size)

    weight_up_layer = torch.randn(inter_dim, hidden_size)
    weight_gate_layer = torch.randn(inter_dim, hidden_size)
    weight_down_layer = torch.randn(hidden_size, inter_dim)

    # Set weights for w1, w2, w3 to the generated tensors
    with torch.no_grad():
        ffn.w1.weight.copy_(weight_up_layer)
        ffn.w2.weight.copy_(weight_gate_layer)
        ffn.w3.weight.copy_(weight_down_layer)

    original_output = rms_norm(ffn(act_tensor))

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

    # Preload Activation (needs 5 registers)
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

    # FFN Generation - Choose optimization mode:
    # use_loop_instructions=True: Loop version (185 lines, ~57k ns)
    # use_fused_up_gate=True: Fused Up+Gate (activation reuse optimization)
    USE_FUSED_OPTIMIZATION = False  # Set to True to test fused optimization

    if USE_FUSED_OPTIMIZATION:
        # Fused version needs 12 registers (gp1-gp12)
        gen_assembly_code += ffn_asm(
            mlen=mlen,
            vlen=vlen,
            blen=blen,
            batch=batch_size,
            seq_len=seq_len,
            hidden_size=hidden_size,
            intermediate_size=inter_dim,
            alive_registers=[1,2,3,4,5,6,7,8,9,10,11,12],
            up_weight_hbm_offset_reg=1,
            gate_weight_hbm_offset_reg=2,
            down_weight_hbm_offset_reg=3,
            const_one_fp_address=1,
            activation_base_address=0,
            use_fused_up_gate=False
        )

        # Reset the registers
        gen_assembly_code += reset_reg_asm(
            alive_registers=[1,2,3,4,5,6,7,8,9,10,11,12]
        )

        gen_assembly_code += rms_norm_asm(
            _eps_offset=1,
            reci_hid_offset=2,
            alive_registers=[1,2,3,4,5],
            activation_base_address = 0,
            scratchpad_base_address = hidden_size * batch_size,
            vlen=64,
            batch_size=4,
            hidden_dim=128
        )

    else:
        # Loop version needs 10 registers (gp1-gp10)
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
        # Reset the registers
        gen_assembly_code += reset_reg_asm(
            alive_registers=[1,2,3,4,5,6,7,8,9,10,11,12]
        )

        gen_assembly_code += rms_norm_asm(
            _eps_offset=1,
            reci_hid_offset=2,
            alive_registers=[1,2,3,4,5],
            activation_base_address = 0,
            scratchpad_base_address = hidden_size * batch_size * seq_len,
            vlen=vlen,
            batch_size=batch_size * seq_len,
            hidden_dim=hidden_size
        )

    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    create_mem_for_sim(data_size=256, mode="behave_sim", asm=None, data=None, specified_data_order = ["act_tensor", "weight_up_layer", "weight_gate_layer", "weight_down_layer"])

    # Save comparison parameters for view_mem.py
    # FFN stores result at activation_base_address (overwrites input)
    import json
    result_vram_offset = 0  # activation_base_address
    effective_batch = batch_size * seq_len
    result_start_row = result_vram_offset // vlen
    num_result_rows = (effective_batch * hidden_size) // vlen
    comparison_params = {
        "start_row_idx": result_start_row,
        "num_rows": num_result_rows,
        "num_batches": effective_batch,
        "elements_per_batch": hidden_size
    }
    build_dir = Path(__file__).parent / "build"
    with open(build_dir / "comparison_params.json", "w") as f:
        json.dump(comparison_params, f, indent=2)

    print("================================================")
    print("Finished generating assembly code")
    print(f"Result location: row {result_start_row}, {num_result_rows} rows")
    print(f"Comparison params: {comparison_params}")
    print("================================================")