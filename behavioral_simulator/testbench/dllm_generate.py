import sys
import random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import Tensor, nn
# from acc_simulator.quantize.quantized_layers.linear import MXFPLinearPTQ
from test_data_gen import get_weights_path, generate_and_save_random_weights
from compiler.asm_templates import  preload_act_asm_scale, reset_reg_asm, preload_addr_reg_asm, get_transfer_index_long_debug
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim
import torch.nn.functional as F

from tools.memory_mapping.hbm_addr_map import align_addr_to_hbm_bandwidth
from transformers import AutoTokenizer
from fastdllm.model.modeling_llada import LLaDAModelLM



########## Code copied from FastdLLM for reference ############
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


def get_transfer_index(
    logits: torch.Tensor,       # (B, L, vocal_size)
    mask_index: torch.Tensor,   # (B, L) bool
    x: torch.Tensor,            # (B, L)
    num_transfer_tokens,        # (B,) or (B,1) long tensor, or None when threshold is used
):
    """
    Returns:
        logits: (B, L, V)
        mask_index: (B, L)
        num_transfer_tokens: (B)
    """
    x0 = torch.argmax(logits, dim=-1)  # (B, L), long
    m = logits.max(dim=-1).values

    # 2) Confidence for chosen tokens (or random)
    p = F.softmax(logits.to(torch.float64), dim=-1)
    x0_p = torch.gather(p, dim=-1, index=x0.unsqueeze(-1)).squeeze(-1)  # (B, L), float64

    # Only modify masked spots; keep others as original x and set their confidence to -inf
    x0 = torch.where(mask_index, x0, x)
    
    neg_inf = torch.tensor(torch.finfo(x0_p.dtype).min, device=x0_p.device, dtype=x0_p.dtype)
    confidence = torch.where(mask_index, x0_p, neg_inf)  # (B, L)

    # Ensure shape (B,) long
    if num_transfer_tokens.dim() == 2 and num_transfer_tokens.size(1) == 1:
        num_transfer_tokens = num_transfer_tokens.squeeze(1)
    num_transfer_tokens = num_transfer_tokens.to(dtype=torch.long, device=confidence.device)
    num_transfer_tokens = torch.clamp(num_transfer_tokens, min=0)

    # Sort confidences descending (masked positions are valid; others are -inf)
    # idx: (B, L) gives positions in original sequence sorted by confidence
    values, idx = torch.sort(confidence, dim=1, descending=True)

    B, L = confidence.shape
    # Build a mask that is True for the first k[b] columns in each row (sorted order)
    cols = torch.arange(L, device=confidence.device).unsqueeze(0).expand(B, L)   # (B, L)
    k_expanded = num_transfer_tokens.unsqueeze(1).expand(B, L)                   # (B, L)
    select_sorted = cols < k_expanded                                            # (B, L) bool

    # Scatter the sorted True/False back to original column order
    # Use integer scatter then cast to bool (scatter_ on bool can be finicky across versions)
    transfer_int = torch.zeros(B, L, device=confidence.device, dtype=torch.int8) # (B, L)
    transfer_int = transfer_int.scatter(1, idx, select_sorted.to(torch.int8))
    transfer_index = transfer_int.bool() & mask_index  # ensure we never select unmasked
    
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
            # Keep batch dimension: use slicing instead of indexing
            logits_wo_prompt = logits[:, prompt.shape[1]:, :]          # (B, L, V)
            mask_index_wo_prompt = mask_index[:, prompt.shape[1]:]     # (B, L)
            x_wo_prompt = x[:, prompt.shape[1]:]                       # (B, L)
            x0, transfer_index = get_transfer_index(logits_wo_prompt, mask_index_wo_prompt, x_wo_prompt, num_transfer_tokens[:, i])
            # Apply transfer - only update the generation part (after prompt)
            x_gen = x[:, prompt.shape[1]:]
            x_gen[transfer_index] = x0[transfer_index]
            x = torch.cat([x[:, :prompt.shape[1]], x_gen], dim=1)
            i += 1

            
            if (x[:, prompt.shape[1] + num_block * block_length: prompt.shape[1] + (num_block + 1) * block_length] == mask_id).sum() == 0:
                break
    return x, nfe

###############################################################

if __name__ == "__main__":

    # target logits.shape =  torch.Size([1, 64, 126464]) 126464=64*1976

    # Testing the operation logits in shape of (batch_size, hidden_size, vocal_size)
    # the largest setup for vocal_size and vocal_size_single is 64*1976 and 64*494 respectively
    torch.manual_seed(68)

    # ============================================================
    # Running generate of fastdllm
    # ============================================================
    model_path = 'GSAI-ML/LLaDA-8B-Instruct'
    device = 'cuda'
    steps = 5
    gen_length = 64
    block_length = 64
    mask_id = 126336
    
    # Load tokenizer
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    
    # Load model
    print("\nLoading model...")
    model = LLaDAModelLM.from_pretrained(
        model_path,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16
    ).to(device).eval()

    prompt_text = "What is 6 + 8? and What is the capital of UK?"
    prompt = tokenizer(prompt_text)['input_ids']
    prompt = torch.tensor(prompt).to(device).unsqueeze(0)
    prompt_len = prompt.shape[1]

    # Generate
    output, nfe = generate(
        model, prompt,
        steps=steps,
        gen_length=gen_length,
        block_length=block_length,
        temperature=0.,
        remasking='low_confidence',
        mask_id=mask_id
    )
    
    tokens = output[0, prompt_len:].cpu()
    generated_text = tokenizer.decode(tokens, skip_special_tokens=True)

    result = {
        'prompt': prompt,
        'generated_text': generated_text,
        'prompt_length': prompt_len,
        'gen_length': len(tokens),
        'nfe': nfe,
        'generated_tokens': tokens,
    }
    print(result)
    
    