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


def get_num_transfer_tokens(block_mask_index: torch.Tensor, steps: int) -> torch.Tensor:
    """
    block_mask_index: (B, L) bool – which positions are masked in the current block
    returns: (B, steps) int – how many tokens to transfer at each step per batch item
    """
    device = block_mask_index.device
    dtype = torch.long

    total = block_mask_index.sum(dim=1)                  # (B,)
    base  = torch.div(total, steps, rounding_mode='floor')  # (B,)
    rem   = total - base * steps                         # (B,)

    # Start with base for all steps
    num_transfer_tokens = base.unsqueeze(1).expand(-1, steps).to(dtype)  # (B, steps)

    # Add +1 to the first `rem[b]` steps for each batch b — without tensor slicing
    cols = torch.arange(steps, device=device).unsqueeze(0)               # (1, steps)
    add_mask = cols < rem.unsqueeze(1)                                   # (B, steps)
    num_transfer_tokens = num_transfer_tokens + add_mask.to(dtype)       # (B, steps)

    return num_transfer_tokens
    #return total
'''
class get_num_transfer_tokens(torch.nn.Module):
    def __init__(self, dim: int):
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
        print("total", x.sum(dim=1) )
        
        total = x.sum(dim=1) 
        return total

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
'''
class RMSNorm(torch.nn.Module):
    def __init__(self, eps: float = 1e-6):
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
        self.weight = nn.Parameter(torch.ones(64))

    def _norm(self, x):
        """
        Apply the RMSNorm normalization to the input tensor.

        Args:
            x (torch.Tensor): The input tensor.

        Returns:
            torch.Tensor: The normalized tensor.

        """
        print("x", x)
        print("x.mean(-1, keepdim=True)", x.mean(-1, keepdim=True))
        
        #return x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)
        return x+(x.sum(-1, keepdim=True))

    def forward(self, x):
        """
        Forward pass through the RMSNorm layer.

        Args:
            x (torch.Tensor): The input tensor.

        Returns:
            torch.Tensor: The output tensor after applying RMSNorm.

        """
        output = self._norm(x.float()).type_as(x)
        return output #* self.weight


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
        # Method 2: use max logit for numerical stability (no explicit softmax)
        
        m = logits.max(dim=-1).values                 # (B, L)
        sub_result = logits - m.unsqueeze(-1)
        exp_shifted = torch.exp(sub_result)
        denom = exp_shifted.sum(dim=-1)               # (B, L)
        reciprocal_denom = 1.0 / denom

        #exp_shifted = torch.exp(logits - m.unsqueeze(-1))  # (B, L, V)
        #denom = exp_shifted.sum(dim=-1)               # (B, L)
        #return 1.0 / denom                            # (B, L)
        return logits + reciprocal_denom.unsqueeze(-1)

    def forward(self, input):
        #x = input["input_tensor1"]
        x = input
        output = self._stable_max_method(x.float()).type_as(x)
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
    batch_size = 3
    real_data_ratio = (8*8 + 8) / (8 * 8)
    fp_preload = [0.0, 1e-6, 1/hidden_size]

    # Gen Weight and Test Data
    # generate_and_save_random_weights(hidden_size, hidden_size, get_weights_path('model_weights.pt'))
    
    torch.manual_seed(42)
    logits = torch.randn(batch_size, hidden_size, vocal_size)
    # Print input_tensor split in half along columns, as two (4, 64) tensors
    #print("input_tensor lhs (4, 64):\n", input_tensor[:, :64])
    #print("input_tensor rhs (4, 64):\n", input_tensor[:, 64:])

    input_tensor1 = logits[:,1,:]
    input_tensor2 = logits[:,2,:]
    input_tensor = input_tensor1
    #input_tensor = torch.cat([input_tensor1, input_tensor2], dim=0)
    #input_tensor = {
    #    "input_tensor1": input_tensor1,
    #    "input_tensor2": input_tensor1
    #}
    original_layer = TEST()
    weights = original_layer.state_dict()
    original_output = original_layer(input_tensor)

    golden_result = {
        "input_tensor": input_tensor,
        "weights": weights,
        "original_output": original_output
    }
    print('original_output.shape = ',original_output.shape)
    print('original_output = ',original_output)
    
    gen_assembly_code = "; DLLM Test Generation \n"
    
    # Set the addr offset for weight and bias
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1,2],
        available_registers=[1,2],
        addr_reg_val=[int(batch_size * vocal_size * real_data_ratio), int(2*batch_size * vocal_size * real_data_ratio)]
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

    '''
    gen_assembly_code += preload_act_asm(
        vlen=vlen,
        preload_len=1,
        batch=batch_size,
        hidden_size=1*vocal_size,
        alive_registers=[1,2,3],  # [a_actual_register, set_stride_register, result_register]
        act_vram_offset=(batch_size) * 0 * vocal_size,
        activation_offset_reg=0
    )
    '''
    '''
    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3,4]
    )

    
    gen_assembly_code += argmux_debug(
        alive_registers=[1,2,3],                   # [act_addr, act2_addr, scratchpad_addr]
        activation_base_address=0,                 # base address of input_tensor in VRAM
        scratchpad_base_address=2*(batch_size+1) * vocal_size,  # output region, avoid the two input regions
        vlen=vlen,
        batch_size=batch_size,
        hidden_dim=hidden_size,
        a2_base_hbm_offset_addr=(batch_size+1) * vocal_size,
    )
    
    '''
    #create_sim_env(input_tensor, weights, gen_assembly_code, golden_result, fp_preload)
    #build_fake_sim_env(data_size=512, mode="behave_sim", asm="dllm", data=None, specified_data_order = ["input_tensor1","input_tensor2"])
    

    create_sim_env(input_tensor, weights, gen_assembly_code, golden_result, fp_preload)
    build_fake_sim_env(data_size=256, mode="behave_sim", asm="dllm", data=None, specified_data_order = ["input_tensor","model_weights"])
    
    
    
    
    
    
    
    
    
    '''
    model_path = 'GSAI-ML/LLaDA-8B-Instruct'
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    print("tokenizer loaded successfully")

    device = 'cuda'
    batch_size = 4
    steps = 3
    gen_length = 16
    block_length = 16
    mask_id = 126336
    real_data_ratio = (8*8 + 8) / (8 * 8)
    vlen = 8
    fp_preload = [0.0, 1e-6, 1]

    prompt_text = "What is 25 + 37?"
    prompt = tokenizer(prompt_text)['input_ids']
    prompt = torch.tensor(prompt).to(device).unsqueeze(0)
    prompt_len = prompt.shape[1]
    x = torch.full((prompt.shape[0], prompt.shape[1] + gen_length), mask_id, dtype=torch.long).to(device)
    #x[:, :prompt.shape[1]] = prompt.clone()

    torch.manual_seed(42)
    x = torch.randn(batch_size, gen_length)

    input_tensor = (x[:, :] != mask_id).float()
    result = get_num_transfer_tokens(input_tensor, steps)
    print('result is ', result)
    #golden_result = {
    #    "input_tensor": input_tensor,
    #    "original_output": result
    #}
    

    
    original_layer = get_num_transfer_tokens(dim=batch_size)
    weights = original_layer.state_dict()

    original_output = original_layer(input_tensor)

    golden_result = {
        "input_tensor": input_tensor,
        "weights": weights,
        "original_output": original_output
    }

    gen_assembly_code = "; get_num_transfer_tokens \n"
    print('input_tensor is ', input_tensor)
    print('weights is ', weights)
    print('original_output is ', original_output)
    
    hidden_size = batch_size
     # Set the addr offset for weight and bias
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1, 2],
        available_registers=[1, 2],
        addr_reg_val=[int(hidden_size * batch_size * real_data_ratio), int((hidden_size * (batch_size + 1) + hidden_size * hidden_size) * real_data_ratio)]
    )

    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3]
    )
    
    # Gen Activation Preload
    gen_assembly_code += preload_act_asm(
        vlen=vlen,
        preload_len=4,
        batch=batch_size,
        hidden_size=gen_length,
        alive_registers=[1,2,3],
        act_vram_offset=0,
        activation_offset_reg=0
    )

    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3,4]
    )

    gen_assembly_code += dllm_asm(
        reci_hid_offset=1,
        alive_registers=[1,2,3,4],
        activation_base_address = 0,
        scratchpad_base_address = gen_length * batch_size,
        vlen=vlen,
        batch_size=batch_size,
        hidden_dim=gen_length
    )

    create_sim_env(input_tensor, weights['weight'].t(), gen_assembly_code, golden_result, fp_preload)
    build_fake_sim_env(data_size=256, mode="behave_sim", asm="rms", data=None, specified_data_order = ["input_tensor", "model_weights"])
    
    print("================================================")
    print("Finished generating assembly code")
    print("================================================")
    '''
