import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import Tensor, nn
# from acc_simulator.quantize.quantized_layers.linear import MXFPLinearPTQ
from test_data_gen import get_weights_path, generate_and_save_random_weights
from compiler.asm_templates import rms_norm_asm, select_vvm_debug, rms_norm_asm_debug, argmux_debug, projection_asm, preload_act_asm, reset_reg_asm, preload_addr_reg_asm, dllm_asm
from create_sim_env import create_sim_env, create_sim_env_dllm
from sim_env_utils import build_fake_sim_env
import torch.nn.functional as F


from transformers import AutoTokenizer



def get_transfer_index(
    logits: torch.Tensor,
    remasking: str,
    mask_index: torch.Tensor,   # (B, L) bool
    x: torch.Tensor,            # (B, L) long
    threshold: float = 0.9,
):
    """
    Returns:
        x0: (B, L) long — proposed tokens
        transfer_index: (B, L) bool — which positions to update this step
    """
    # 1) Sample proposal x0
    # Gumbel-noise for exploration; if temperature==0, add_gumbel_noise should no-op
    x0 = torch.argmax(logits, dim=-1)  # (B, L), long

    # 2) Confidence for chosen tokens (or random)
    if remasking == "low_confidence":
        # Use higher precision for softmax stability
        p = F.softmax(logits.to(torch.float64), dim=-1)
        x0_p = torch.gather(p, dim=-1, index=x0.unsqueeze(-1)).squeeze(-1)  # (B, L), float64
    elif remasking == "random":
        x0_p = torch.rand(x0.shape, device=x0.device, dtype=torch.float64)  # (B, L)
    else:
        raise NotImplementedError(remasking)

    # Only modify masked spots; keep others as original x and set their confidence to -inf
    x0 = torch.where(mask_index, x0, x)

    neg_inf = torch.tensor(torch.finfo(x0_p.dtype).min, device=x0_p.device, dtype=x0_p.dtype)
    confidence = torch.where(mask_index, x0_p, neg_inf)  # (B, L)

    # 3) Pick positions to transfer (vectorized)
    # Transfer all masked positions whose confidence >= threshold
    # (No top-k; purely threshold-based)
    transfer_index = mask_index & (confidence >= threshold)
    return x0, transfer_index



class TEST(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(128))

    def _argmux(self, x):
        
        x0 = torch.argmax(x, dim=-1)
        print('x = ',x)
        print('x0 = ',x0)
        return x0
    
    def _stable_max_method(self, logits):
        # 方式2: 利用最大logit做数值稳定处理，不显式softmax
        m = logits.max(dim=-1).values                 # (B, L)
        sub_result = logits - m.unsqueeze(-1)
        exp_shifted = torch.exp(sub_result)
        denom = exp_shifted.sum(dim=-1)               # (B, L)
        reciprocal_denom = 1.0 / denom

        #exp_shifted = torch.exp(logits - m.unsqueeze(-1))  # (B, L, V)
        #denom = exp_shifted.sum(dim=-1)               # (B, L)
        #return 1.0 / denom                            # (B, L)
        return logits + reciprocal_denom.unsqueeze(-1)

    def _select_vvm(self, x1, x2, mask):
        out = torch.where(mask, x1, x2)
        return out

    def forward(self, x1, x2, mask):
        
        output = self._select_vvm(x1.float(),x2.float(),mask.bool()).type_as(x1)
        return output


if __name__ == "__main__":
    # batch_size=4, gen_len=16
    #result is  tensor([[6, 5, 5],
    #                   [6, 5, 5],
    #                   [6, 5, 5],
    #                   [6, 5, 5]])

    #logits.shape =  torch.Size([1, 148, 126464])

    # Testing the operation (hidden_size, hidden_size) @ (hidden_size, batch_size)
    vocal_size = 64
    hidden_size = 64
    vlen = 64
    batch_size = 4
    real_data_ratio = (8*8 + 8) / (8 * 8)
    fp_preload = [0.0, 1e-6, 1/hidden_size]

    # Gen Weight and Test Data
    # generate_and_save_random_weights(hidden_size, hidden_size, get_weights_path('model_weights.pt'))
    
    torch.manual_seed(42)
    logits = torch.randn(batch_size, hidden_size, vocal_size)
    # Print input_tensor split in half along columns, as two (4, 64) tensors
    #print("input_tensor lhs (4, 64):\n", input_tensor[:, :64])
    #print("input_tensor rhs (4, 64):\n", input_tensor[:, 64:])

    input_tensor = logits[:,1,:]
    input_tensor2 = logits[:,2,:]
    mask = torch.rand_like(input_tensor) < 0.5
    original_layer = TEST()
    weights = original_layer.state_dict()
    original_output = original_layer(input_tensor,input_tensor2,mask)

    golden_result = {
        "input_tensor": input_tensor,
        "input_tensor2": input_tensor2,
        "mask": mask,
        "weights": weights,
        "original_output": original_output
    }
    print('original_output.shape = ',original_output.shape)
    print('original_output = ',original_output)
    
    gen_assembly_code = "; DLLM Test Generation \n"
    
    # Set the addr offset for weight and bias
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1,2,3,4],
        available_registers=[1,2,3,4],
        addr_reg_val=[int(batch_size * 1 * vocal_size * real_data_ratio), int(2*batch_size * 1 * vocal_size * real_data_ratio), int(3*batch_size * 1 * vocal_size * real_data_ratio), int(4*batch_size*128*real_data_ratio)]
    )

    #print("hidden_size * batch_size * real_data_ratio", hidden_size * batch_size * real_data_ratio)
    #print("(hidden_size * (batch_size + 1) + hidden_size * hidden_size) * real_data_ratio", (hidden_size * (batch_size + 1) + hidden_size * hidden_size) * real_data_ratio)

    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3]
    )
    
    # Gen Activation Preload
    gen_assembly_code += preload_act_asm(
        vlen=vlen,
        preload_len=1,
        batch=batch_size,
        hidden_size=1*vocal_size,
        alive_registers=[1,2,3],  # [a_actual_register, set_stride_register, result_register]
        act_vram_offset=0,
        activation_offset_reg=0
    )

    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3,4]
    )

    gen_assembly_code += select_vvm_debug(
        alive_registers=[1,2,3,4],
        activation_base_address = 0,
        activation2_base_address = 0,
        activation3_base_address = 0,
        scratchpad_base_address = batch_size * 1*vocal_size,
        vlen=vlen,
        batch_size=batch_size,
        hidden_dim=hidden_size
    )
    

    create_sim_env(input_tensor, input_tensor2, mask, weights['weight'].t(), gen_assembly_code, golden_result, fp_preload)
    build_fake_sim_env(data_size=256, mode="behave_sim", asm="rms", data=None, specified_data_order = ["input_tensor", "input_tensor2","mask","model_weights"])
    