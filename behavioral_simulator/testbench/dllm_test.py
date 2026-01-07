import sys
import random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import Tensor, nn
# from acc_simulator.quantize.quantized_layers.linear import MXFPLinearPTQ
from test_data_gen import get_weights_path, generate_and_save_random_weights
from compiler.asm_templates import  preload_act_asm_scale, reset_reg_asm, preload_addr_reg_asm, get_transfer_index_performance, get_transfer_index_edge
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim
import torch.nn.functional as F

from tools.memory_mapping.hbm_addr_map import align_addr_to_hbm_bandwidth
from transformers import AutoTokenizer
from fastdllm.model.modeling_llada import LLaDAModelLM



# how to run this testbench?
# -> just build-behave-sim-debug dllm 2>&1 | tee simulation_dllm.log

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
    #print('mask_index.shape= ', mask_index.shape)
    #print('x0_p.shape= ', x0_p.shape)
    #print('neg_inf.shape= ', neg_inf.shape)
    confidence = torch.where(mask_index, x0_p, neg_inf)  # (B, L)
    #print('confidence.shape= ', confidence.shape)

    # Ensure shape (B,) long
    if num_transfer_tokens.dim() == 2 and num_transfer_tokens.size(1) == 1:
        num_transfer_tokens = num_transfer_tokens.squeeze(1)
    num_transfer_tokens = num_transfer_tokens.to(dtype=torch.long, device=confidence.device)
    num_transfer_tokens = torch.clamp(num_transfer_tokens, min=0)

    # Sort confidences descending (masked positions are valid; others are -inf)
    # idx: (B, L) gives positions in original sequence sorted by confidence
    values, idx = torch.sort(confidence, dim=1, descending=True)

    B, L = confidence.shape
    #print('confidence.shape= ', confidence.shape)
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


"""
INT Memory Layout:
==================================================================================================
Address Range                                                       | Content     | Size
==================================================================================================
[0 : prompt_batch_size*hidden_size)                                 | x           | prompt_batch_size*hidden_size
--------------------------------------------------------------------------------------------------
[prompt_batch_size*hidden_size : 2*prompt_batch_size*hidden_size)   | x0          | prompt_batch_size*hidden_size
==================================================================================================

VRAM Memory Layout:
==================================================================================
Address Range                                     | Content         | Size
==================================================================================
[0 : B*L)                                         | transfer_index  | B * L
----------------------------------------------------------------------------------
[B*L : 2*B*L)                                     | mask            | B * L
----------------------------------------------------------------------------------
[2*B*L : 3*B*L)                                   | x0_p            | B * L
----------------------------------------------------------------------------------
                                                  |                 | (transfer_index result)
[3*B*L : 3*B*L + vocal_size_single)               | temp            | vocal_size_single
                                                  |                 | (for exp(logits-max))
                                                  |                 |
[3*B*L + vlen : 3*B*L + vocal_size_single + veln) | logits          | vocal_size_single
                                                  |                 | *** OVERLAPS with temp ***
                                                  |                 | (offset +vlen from temp)
==================================================================================

Memory Reuse Strategy:
    - temp and logits OVERLAP by (vocal_size_single - vlen) elements
    - When processing logits in vlen-sized chunks:
        * Process logits[i*vlen : (i+1)*vlen]
        * Compute exp() and store in temp[i*vlen : (i+1)*vlen]
        * By the time we need temp[0:vlen], logits[0:vlen] is already consumed
    - This saves (vocal_size_single - vlen) elements of VRAM

Example (vocal_size_single=640, vlen=64):
    temp:   [256, 896)
    logits: [320, 960)  ← starts vlen elements after temp
    overlap:[320, 896)  ← 576 elements shared between temp and logits
"""

class TEST(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(128))

    def _get_transfer_index(
        self,
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
        #print('mask_index.shape= ', mask_index.shape)
        #print('x0_p.shape= ', x0_p.shape)
        #print('neg_inf.shape= ', neg_inf.shape)
        confidence = torch.where(mask_index, x0_p, neg_inf)  # (B, L)
        #print('confidence.shape= ', confidence.shape)

        # Ensure shape (B,) long
        if num_transfer_tokens.dim() == 2 and num_transfer_tokens.size(1) == 1:
            num_transfer_tokens = num_transfer_tokens.squeeze(1)
        num_transfer_tokens = num_transfer_tokens.to(dtype=torch.long, device=confidence.device)
        num_transfer_tokens = torch.clamp(num_transfer_tokens, min=0)

        # Sort confidences descending (masked positions are valid; others are -inf)
        # idx: (B, L) gives positions in original sequence sorted by confidence
        values, idx = torch.sort(confidence, dim=1, descending=True)

        B, L = confidence.shape
        #print('confidence.shape= ', confidence.shape)
        # Build a mask that is True for the first k[b] columns in each row (sorted order)
        cols = torch.arange(L, device=confidence.device).unsqueeze(0).expand(B, L)   # (B, L)
        k_expanded = num_transfer_tokens.unsqueeze(1).expand(B, L)                   # (B, L)
        select_sorted = cols < k_expanded                                            # (B, L) bool

        # Scatter the sorted True/False back to original column order
        # Use integer scatter then cast to bool (scatter_ on bool can be finicky across versions)
        transfer_int = torch.zeros(B, L, device=confidence.device, dtype=torch.int8) # (B, L)
        transfer_int = transfer_int.scatter(1, idx, select_sorted.to(torch.int8))
        transfer_index = transfer_int.bool() & mask_index  # ensure we never select unmasked
        x[transfer_index] = x0[transfer_index]
        output = torch.cat([x , x0, transfer_index], dim=0)
        return x

    def forward(self, logits, mask_index, x, num_transfer_tokens):
        """
        Args:
            logits: torch.Tensor,       # (B, voval_size)
            mask_index: torch.Tensor,   # (B, L) bool
            num_transfer_tokens,        # (B,) or (B,1) long tensor, or None when threshold is used
        
        Returns:
            transfer_index: (B, L) bool — selected positions mask
        """
        output = self._get_transfer_index(logits, mask_index, x, num_transfer_tokens)
        return output


if __name__ == "__main__":

    # target logits.shape =  torch.Size([1, 64, 126464]) 126464=64*1976

    # Testing the operation logits in shape of (batch_size, hidden_size, vocal_size)
    # the largest setup for vocal_size and vocal_size_single is 64*1976 and 64*494 respectively
    torch.manual_seed(68)

    # ============================================================
    # Running generate of fastdllm
    # ============================================================
    model_path = 'GSAI-ML/LLaDA-8B-Instruct'
    device = 'cuda:2'
    steps = 1
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
    
    
    # ============================================================
    # Running TEST on CPU
    # ============================================================
    
    # Set up simulator parameters
    vocal_size = 64*1976
    vocal_size_single = 64*494  #64*494
    hidden_size = gen_length
    vlen = 64
    repeat_times = vocal_size//vocal_size_single
    batch_size = prompt.shape[0]
    prompt_batch_size = batch_size
    preload_amount = 1
    real_data_ratio = (8*8 + 8) / (8 * 8)
    hbm_data_width = 64
    fp_preload = [0.0, 0.0, 0, 1e-3]
    
    if(prompt.shape[1] < gen_length):
        x = torch.full((prompt.shape[0], prompt.shape[1] + gen_length), mask_id, dtype=torch.long).to(device)
    else:
        raise ValueError(f"prompt length is too long: {prompt.shape[1]}")
    x[:, :prompt.shape[1]] = prompt.clone()
    
    block_mask_index = (x[:, prompt.shape[1]:prompt.shape[1] + block_length] == mask_id)
    num_transfer_tokens = get_num_transfer_tokens(block_mask_index, steps)
    print('num_transfer_tokens = ',num_transfer_tokens)

    # ============================================================
    # Running TEST on CPU with T time steps (parameterized)
    # ============================================================
    
    # Initialize storage for all time steps
    logits_cpu_list = []
    mask_cpu_list = []
    k_values_list = []
    
    # Initialize x_cpu for the first iteration
    x_cpu = torch.full((prompt_batch_size, hidden_size), mask_id, dtype=torch.long)
    test_x = x_cpu.clone()
    
    # Run T iterations
    for t in range(steps):
        print(f"Running TEST iteration T={t+1}/{steps}")
        
        # Update x with previous iteration results (skip for first iteration)
        if t > 0:
            x[:, prompt.shape[1]:] = test_x.clone().to(device)
        
        # Run model inference
        logits = model(x).logits
        logits_wo_prompt = logits[:, prompt.shape[1]:, :]  # (B, L, V)
        
        # Prepare data for CPU test
        logits_cpu = logits_wo_prompt.cpu()  # (B, L, V) on cpu
        
        # Compute mask based on current x state
        if t == 0:
            mask_cpu = (x[:, prompt.shape[1]:] == mask_id).cpu()
            x_cpu = torch.full((prompt_batch_size, hidden_size), mask_id, dtype=torch.long)
        else:
            x_cpu = test_x.clone()  # Use result from previous iteration
            mask_cpu = (x_cpu == mask_id)  # Only positions still equal to mask_id are masked
        
        # Get k values for this time step
        k_values = num_transfer_tokens.cpu()[:, t]  # Shape (B,) - current step's k values
        
        # Store for simulator
        logits_cpu_list.append(logits_cpu)
        mask_cpu_list.append(mask_cpu)
        k_values_list.append(k_values)
        
        # Run TEST layer
        original_layer = TEST()
        original_output = original_layer(logits_cpu, mask_cpu, x_cpu, k_values)
        test_x = original_output  # Extract the updated x for next iteration

    
    # ============================================================
    # Compare TEST vs generate
    # ============================================================
    # Show differences if any
    if not torch.equal(tokens.long(), test_x[0].long()):
        diff_mask = tokens.long() != test_x[0].long()
        diff_indices = torch.where(diff_mask)[0]
        print(f"\n Found {len(diff_indices)} differences at positions: {diff_indices.tolist()[:20]}")
        for idx in diff_indices[:5]:  # Show first 5 differences
            print(f"   Position {idx}: generate={tokens[idx].item()}, TEST={test_x[0, idx].item():.0f}")
    
    
    print(f"\n{'='*80}")
    print(f"Golden Result Summary:")
    print(f"{'='*80}")
    print(f"TEST output shape: {original_output.shape}")
    print(f"Generate tokens shape: {tokens.shape}")
    print(f"\nTEST output (first 10): {original_output[0, :10]}")
    print(f"Generate tokens (first 10): {tokens[:10]}")
    
    
    # ============================================================
    # Running SIMULATOR on CPU
    # ============================================================
    print(f"\n{'='*80}")
    print(f"Simulator Running with T={steps} time steps..")
    print(f"{'='*80}")
    
    int_preload = torch.randint(low=mask_id, high=mask_id+1, size=(prompt_batch_size*hidden_size,), dtype=torch.int32)

    # Concatenate all time steps
    input_tensor = {
        "logits": torch.cat(logits_cpu_list, dim=0),  # Concatenate all T logits along batch dimension
        "mask": torch.cat(mask_cpu_list, dim=0).type_as(logits_cpu_list[0]), # Convert mask to float for vram store (simulator requires float input)
        "int": int_preload,
    }

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": original_output
    }

    # Set the VRAM address offsets (T is now parameterized as steps)
    transfer_idx_offset_address = 0
    mask_offset_address = (batch_size * hidden_size)*steps
    x0_p_offset_address = (batch_size * hidden_size)*steps*2
    logits_offset_address = (batch_size * hidden_size)*steps*3 + vlen
    
    gen_assembly_code = "; DLLM Test Generation \n"

    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1,2],
        available_registers=[1,2],
        addr_reg_val=[int(align_addr_to_hbm_bandwidth(batch_size*hidden_size*vocal_size*real_data_ratio, hbm_data_width)),int(align_addr_to_hbm_bandwidth(batch_size*hidden_size*vocal_size*real_data_ratio, hbm_data_width)+align_addr_to_hbm_bandwidth(batch_size*hidden_size*real_data_ratio, hbm_data_width))]
    )

    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3,4,5,6,7,8]
    )
    
    # only preload mask (B,L)
    gen_assembly_code += preload_act_asm_scale(
        vlen=vlen,
        preload_len=preload_amount,
        batch=batch_size*steps,
        hidden_size=hidden_size,
        scale=batch_size*hidden_size*steps,
        alive_registers=[1,2,3],  # [a_actual_register, set_stride_register, result_register]
        act_hbm_offset=0,
        act_vram_offset=mask_offset_address,
        activation_offset_reg=1
    )
    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3,4,5,6,7,8]
    )
    # Use the collected k_values from all T iterations
    # TODO: Currently utilizing an outdated version of the transfer index asm 
    # Need to update to use the performance and edge versions where appropriate
    gen_assembly_code += get_transfer_index_edge(
        alive_registers=[4,5,6,7,8,9,10,11,12,13,14,15],
        logits_base_address=logits_offset_address,
        mask_base_address=mask_offset_address,
        transfer_idx_base_address=0,
        x0_p_base_address=x0_p_offset_address,
        k_values=k_values_list,
        vlen=vlen,
        T=steps,
        repeat_times=repeat_times,
        batch_size=batch_size,
        prompt_batch_size=prompt_batch_size,
        vocal_size_single=vocal_size_single,
        gen_length=gen_length, 
        preload_len=preload_amount
    )
    
    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload, int_preload)
    create_mem_for_sim(data_size=256, mode="behave_sim", asm="dllm", data=None, specified_data_order = ["logits", "mask", "int"])
    
    
    