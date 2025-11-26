import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import Tensor, nn
# from acc_simulator.quantize.quantized_layers.linear import MXFPLinearPTQ
from test_data_gen import get_weights_path, generate_and_save_random_weights
from compiler.asm_templates import  select_vvm_debug, preload_act_asm, reset_reg_asm, preload_addr_reg_asm,get_transfer_index_debug,get_transfer_index_long_debug
from create_sim_env import create_sim_env, create_sim_env_dllm
from sim_env_utils import build_fake_sim_env
import torch.nn.functional as F

from tools.memory_mapping.hbm_addr_map import align_addr_to_hbm_bandwidth
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



def generate(model, prompt, steps=128, gen_length=128, block_length=128, temperature=0.,
             remasking='low_confidence', mask_id=126336, threshold=None, factor=None):
    '''
    Args:
        model: Mask predictor.
        prompt: A tensor of shape (1, L).
        steps: Sampling steps, less than or equal to gen_length.
        gen_length: Generated answer length.
        block_length: Block length, less than or equal to gen_length. If less than gen_length, it means using semi_autoregressive remasking.
        temperature: Categorical distribution sampling temperature.
        cfg_scale: Unsupervised classifier-free guidance scale.
        remasking: Remasking strategy. 'low_confidence' or 'random'.
        mask_id: The toke id of [MASK] is 126336.
    '''
    x = torch.full((prompt.shape[0], prompt.shape[1] + gen_length), mask_id, dtype=torch.long).to(model.device)
    x[:, :prompt.shape[1]] = prompt.clone()

    assert gen_length % block_length == 0
    num_blocks = gen_length // block_length

    assert steps % num_blocks == 0
    steps = steps // num_blocks

    nfe = 0
    for num_block in range(num_blocks):
        block_mask_index = (x[:, prompt.shape[1] + num_block * block_length: prompt.shape[1] + (num_block + 1) * block_length] == mask_id)
        num_transfer_tokens = get_num_transfer_tokens(block_mask_index, steps)
        i = 0
        while True:
            nfe += 1
            mask_index = (x == mask_id)
            logits = model(x).logits
            mask_index[:, prompt.shape[1] + (num_block + 1) * block_length:] = 0
            x0, transfer_index = get_transfer_index(logits, temperature, remasking, mask_index, x, num_transfer_tokens[:, i], threshold)
            x[transfer_index] = x0[transfer_index]
            i += 1
            if (x[:, prompt.shape[1] + num_block * block_length: prompt.shape[1] + (num_block + 1) * block_length] == mask_id).sum() == 0:
                break
    return x, nfe

  

class TEST(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(128))

    def _get_transfer_index(
        self,
        logits: torch.Tensor,       # (B, L, vocal_size)
        mask_index: torch.Tensor,   # (B, L) bool
        num_transfer_tokens,        # (B,) or (B,1) long tensor, or None when threshold is used
    ):
        """
        Returns:
            logits: (B, L, V)
            mask_index: (B, L)
            num_transfer_tokens: (B)
        """
        x0 = torch.argmax(logits, dim=-1)  # (B, L), long

        # 2) Confidence for chosen tokens (or random)
        p = F.softmax(logits.to(torch.float64), dim=-1)
        x0_p = torch.gather(p, dim=-1, index=x0.unsqueeze(-1)).squeeze(-1)  # (B, L), float64

        # Only modify masked spots; keep others as original x and set their confidence to -inf
        #x0 = torch.where(mask_index, x0, x)
        
        neg_inf = torch.tensor(torch.finfo(x0_p.dtype).min, device=x0_p.device, dtype=x0_p.dtype)
        print('mask_index.shape= ', mask_index.shape)
        print('x0_p.shape= ', x0_p.shape)
        print('neg_inf.shape= ', neg_inf.shape)
        confidence = torch.where(mask_index, x0_p, neg_inf)  # (B, L)
        print('confidence.shape= ', confidence.shape)

        # Ensure shape (B,) long
        if num_transfer_tokens.dim() == 2 and num_transfer_tokens.size(1) == 1:
            num_transfer_tokens = num_transfer_tokens.squeeze(1)
        num_transfer_tokens = num_transfer_tokens.to(dtype=torch.long, device=confidence.device)
        num_transfer_tokens = torch.clamp(num_transfer_tokens, min=0)

        # Sort confidences descending (masked positions are valid; others are -inf)
        # idx: (B, L) gives positions in original sequence sorted by confidence
        values, idx = torch.sort(confidence, dim=1, descending=True)

        B, L = confidence.shape
        print('confidence.shape= ', confidence.shape)
        # Build a mask that is True for the first k[b] columns in each row (sorted order)
        cols = torch.arange(L, device=confidence.device).unsqueeze(0).expand(B, L)   # (B, L)
        k_expanded = num_transfer_tokens.unsqueeze(1).expand(B, L)                   # (B, L)
        select_sorted = cols < k_expanded                                            # (B, L) bool

        # Scatter the sorted True/False back to original column order
        # Use integer scatter then cast to bool (scatter_ on bool can be finicky across versions)
        transfer_int = torch.zeros(B, L, device=confidence.device, dtype=torch.int8) # (B, L)
        transfer_int = transfer_int.scatter(1, idx, select_sorted.to(torch.int8))
        transfer_index = transfer_int.bool() & mask_index  # ensure we never select unmasked

        return transfer_index  

    def _stable_max_method(self, logits):
        # Method 2: use max logit for numerical stability (no explicit softmax)
        #logits # (B, L, V)
        m = logits.max(dim=-1).values                 # (B, L)
        sub_result = logits - m.unsqueeze(-1)         # (B, L, V)
        exp_shifted = torch.exp(sub_result)           # (B, L, V)
        denom = exp_shifted.sum(dim=-1)               # (B, L)
        reciprocal_denom = 1.0 / denom                # (B, L)

        print('reciprocal_denom = ', reciprocal_denom)
        #return logits + reciprocal_denom.unsqueeze(-1)
        return reciprocal_denom

    def forward(self, logits, mask_index, num_transfer_tokens):
        """
        Args:
            logits: torch.Tensor,       # (B, voval_size)
            mask_index: torch.Tensor,   # (B, L) bool
            num_transfer_tokens,        # (B,) or (B,1) long tensor, or None when threshold is used
        
        Returns:
            transfer_index: (B, L) bool — selected positions mask
        """
        output = self._get_transfer_index(logits, mask_index, num_transfer_tokens).type_as(logits)
        #output = self._stable_max_method(logits).type_as(logits)
        return output


if __name__ == "__main__":
    # batch_size=4, gen_len=16
    #result is  tensor([[6, 5, 5],
    #                   [6, 5, 5],
    #                   [6, 5, 5],
    #                   [6, 5, 5]])

    #logits.shape =  torch.Size([1, 148, 126464])

    # Testing the operation (hidden_size, hidden_size) @ (hidden_size, batch_size)
    vocal_size = 64*4
    vocal_size_single = 128
    hidden_size = 64
    vlen = 64
    repeat_times = vocal_size//vocal_size_single
    batch_size = 4
    preload_amount = 1
    real_data_ratio = (8*8 + 8) / (8 * 8)
    hbm_data_width = 64
    fp_preload = [0.0, 1e-6]
    # Different k values for each batch item (number of tokens to select)
    k_values = [8, 8, 8, 8]
    
    torch.manual_seed(68)
    # logits shape should be (B, L, vocab_size) for get_transfer_index
    logits = torch.randn(batch_size, hidden_size * vocal_size)

    # Generate random mask (some positions are masked, some are not)
    # mask should be (B, L) matching the sequence length
    mask = torch.rand(batch_size, hidden_size) < 0.5

    # K values for each batch
    num_transfer_tokens = torch.tensor(k_values, dtype=torch.long)
    original_layer = TEST()
    weights = original_layer.state_dict()
    original_output = original_layer(logits.reshape(batch_size, hidden_size, vocal_size), mask, num_transfer_tokens)
    #original_output = 1.0/torch.sum(logits.reshape(batch_size, hidden_size, vocal_size), dim=-1)
    # Convert mask to float for quantization (simulator requires float input)
    mask = mask.type_as(logits)

    print('logits.shape= ', logits.shape)
    print('mask.shape= ', mask.shape)
    print('num_transfer_tokens.shape= ', num_transfer_tokens.shape)
    print('original_output.shape= ', original_output.shape)
    print('repeat_times = ', repeat_times)

    
    input_tensor = {
        "logits": logits,
        "mask": mask,
    }

    golden_result = {
        "input_tensor": input_tensor,
        "weights": weights,
        "original_output": original_output
    }
    print('original_output.shape = ',original_output.shape)
    print('original_output = ',original_output)
    
    gen_assembly_code = "; DLLM Test Generation \n"
    
    # Set the addr offset for mask
    logits_offset_address = (batch_size * hidden_size)
    mask_offset_address = (batch_size * hidden_size) + (vocal_size_single)
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1,2],
        available_registers=[1,2],
        addr_reg_val=[int(align_addr_to_hbm_bandwidth(batch_size*hidden_size*vocal_size * real_data_ratio, hbm_data_width)),int(2*align_addr_to_hbm_bandwidth(batch_size * hidden_size * vocal_size * real_data_ratio, hbm_data_width))]
    )


    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3,4,5,6,7,8]
    )
    
    '''
    # Gen logtis Preload (B,L,V)
    gen_assembly_code += preload_act_asm(
        vlen=vlen,
        preload_len=preload_amount,
        batch=batch_size,
        hidden_size=hidden_size*vocal_size,
        alive_registers=[1,2,3],  # [a_actual_register, set_stride_register, result_register]
        act_hbm_offset=hidden_size*vocal_size,
        act_vram_offset=logits_offset_address,
        activation_offset_reg=0
    )
    '''

    
    # 只预加载 mask (B,L)
    gen_assembly_code += preload_act_asm(
        vlen=vlen,
        preload_len=preload_amount,
        batch=batch_size,
        hidden_size=hidden_size,
        scale=batch_size*hidden_size,
        alive_registers=[1,2,3],  # [a_actual_register, set_stride_register, result_register]
        act_hbm_offset=0,
        act_vram_offset=mask_offset_address,
        activation_offset_reg=1
    )
    

    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3,4,5,6,7,8]
    )

    
    gen_assembly_code += get_transfer_index_long_debug(
        alive_registers=[4,5,6,7,8,9,10,11,12],
        logits_base_address=logits_offset_address,
        mask_base_address=mask_offset_address,
        output_base_address=0,
        temp_base_address=mask_offset_address + batch_size * hidden_size,
        x0_p_base_address=mask_offset_address + batch_size * hidden_size + vocal_size_single,
        k_values=k_values,
        vlen=vlen,
        repeat_times=repeat_times,
        batch_size=batch_size,
        vocal_size_single=vocal_size_single,
        hidden_size=hidden_size,
    )
    
    
    create_sim_env(input_tensor, weights, gen_assembly_code, golden_result, fp_preload)
    build_fake_sim_env(data_size=256, mode="behave_sim", asm="dllm", data=None, specified_data_order = ["logits", "mask"])
