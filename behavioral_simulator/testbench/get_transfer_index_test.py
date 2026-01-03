import sys
import random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import Tensor, nn
# from acc_simulator.quantize.quantized_layers.linear import MXFPLinearPTQ
from test_data_gen import get_weights_path, generate_and_save_random_weights
from compiler.asm_templates import  preload_act_asm_scale, reset_reg_asm, preload_addr_reg_asm, get_transfer_index_performance,get_transfer_index_edge
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim
import torch.nn.functional as F

from tools.memory_mapping.hbm_addr_map import align_addr_to_hbm_bandwidth
from transformers import AutoTokenizer



# how to run this testbench?
# -> just build-behave-sim-debug get_transfer_index 2>&1 | tee simulation_dllm.log


"""
INT Memory Layout:
==================================================================================================
Address Range                                                       | Content     | Size
==================================================================================================
[0 : prompt_batch_size*gen_length)                                  | x           | prompt_batch_size*gen_length
--------------------------------------------------------------------------------------------------
[prompt_batch_size*gen_length : 2*prompt_batch_size*gen_length)     | x0          | prompt_batch_size*gen_length
==================================================================================================

VRAM Memory Layout:
==================================================================================
Address Range                                          | Content         | Size
==================================================================================
[0 : B*vlen)                                           | transfer_index  | B * vlen
----------------------------------------------------------------------------------
[B*vlen : 2*B*vlen)                                    | mask            | B * vlen
----------------------------------------------------------------------------------
[2*B*vlen : 3*B*vlen)                                  | x0_p            | B * vlen
----------------------------------------------------------------------------------
[3*B*vlen : 3*B*vlen + vocal_size_single)              | logits          | edge MODE, juts preload a chunk of logits from HBM to SRAM each time 
OR                                                     |                 |
[3*B*L + vlen : 3*B*L + vocal_size*gen_length*batch_R) | logits          | performance MODE, preload [batch_R,gen_length,vocal_size] of logits each time
==================================================================================
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
        x[transfer_index] = x0[transfer_index]
        output = torch.cat([x , x0,transfer_index], dim=0)
        return output

    def forward(self, logits, mask_index, x, num_transfer_tokens):
        """
        Args:
            logits: torch.Tensor,       # (B, voval_size)
            mask_index: torch.Tensor,   # (B, L) bool
            num_transfer_tokens,        # (B,) or (B,1) long tensor, or None when threshold is used
        
        Returns:
            transfer_index: (B, L) bool — selected positions mask
        """
        output = self._get_transfer_index(logits, mask_index, x, num_transfer_tokens).type_as(logits)
        return output


if __name__ == "__main__":
    # Testing the operation logits in shape of (batch_size, gen_length, vocal_size)
    # example [16,64,64*1984]

    # ============ Configuration ============
    # Select test mode: 'edge' or 'performance'
    TEST_MODE = 'performance'  # Change this to switch test mode
    if TEST_MODE not in ['edge', 'performance']:
        raise ValueError(f"TEST_MODE must be 'edge' or 'performance', but got '{TEST_MODE}'")
    # ========================================
    steps=1
    vocal_size = 64*4 
    vocal_size_single = 64*2
    gen_length = 64
    vlen = 64  # reminder: 1. sync this value in the "plena_settings.toml" 2.veln>gen_length
    repeat_times = vocal_size//vocal_size_single
    batch_size = 2
    batch_R = 1
    prompt_batch_size = batch_size
    mask_id=0
    preload_amount = 1
    real_data_ratio = (8*8 + 8) / (8 * 8)
    hbm_data_width = 64 # fix number according to the HBM2e setup
    fp_preload = [0.0, 0.0, 0, 1e-3]
    # Different k values for each batch item (number of tokens to select)
    k_values = [8]

    k_values_list = []
    for t in range(steps):
        k_values_list.append(k_values)
    
    torch.manual_seed(66)
    # logits shape should be (B, L, vocab_size) for get_transfer_index
    x = torch.full((prompt_batch_size, gen_length), mask_id)
    int_preload = torch.randint(low=mask_id, high=mask_id+1, size=(prompt_batch_size*gen_length,), dtype=torch.int32)
    logits = torch.randn(batch_size, gen_length * vocal_size)
    x = x.type_as(logits)

    # Generate random mask (some positions are masked, some are not)
    # mask should be (B, L) matching the sequence length
    mask = torch.rand(batch_size, gen_length) < 0.5
    
    # Pad mask to align with vlen if needed
    if gen_length < vlen:
        pad_size = vlen - gen_length
        # Pad with False (dummy values) on the right side (dim=1)
        mask_padded = torch.cat([mask, torch.zeros(batch_size, pad_size, dtype=torch.bool)], dim=1)
        # Use original mask for golden result computation
        mask_for_golden = mask
    else:
        mask_padded = mask
        mask_for_golden = mask

    # K values for each batch
    num_transfer_tokens = torch.tensor(k_values, dtype=torch.long)
    original_layer = TEST()
    # Use original mask (without padding) for golden result
    original_output = original_layer(logits.reshape(batch_size, gen_length, vocal_size), mask_for_golden, x, num_transfer_tokens)
    #original_output = torch.max(logits.reshape(batch_size, gen_length, vocal_size), dim=-1).values
    #original_output = torch.sum(logits.reshape(batch_size, gen_length, vocal_size), dim=-1)
    # Convert mask to float for quantization (simulator requires float input)
    # Use padded mask for simulation
    mask = mask_padded.type_as(logits)
    x = x.type_as(logits)

    print('x.shape= ', x.shape)
    print('logits.shape= ', logits.shape)
    print('mask.shape= ', mask.shape)
    print('num_transfer_tokens.shape= ', num_transfer_tokens.shape)
    print('original_output.shape= ', original_output.shape)
    print('repeat_times = ', repeat_times)
    
    input_tensor = {
        "logits": logits,
        "mask": mask,
        "int": int_preload,
    }

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": original_output
    }
    print('original_output.shape = ',original_output.shape)
    print('original_output = ',original_output)
    
    gen_assembly_code = "; DLLM Test Generation \n"
    
    # Set the VRAM address offsets
    transfer_idx_offset_address = 0
    mask_offset_address = (batch_size * vlen)
    x0_p_offset_address = (batch_size * vlen)*2
    logits_offset_address = (batch_size * vlen)*3
    
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1,2],
        available_registers=[1,2],
        addr_reg_val=[int(align_addr_to_hbm_bandwidth(batch_size*gen_length*vocal_size*real_data_ratio, hbm_data_width)),int(align_addr_to_hbm_bandwidth(batch_size*gen_length*vocal_size*real_data_ratio, hbm_data_width)+align_addr_to_hbm_bandwidth(batch_size*gen_length*real_data_ratio, hbm_data_width))]
    )

    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3,4,5,6,7,8]
    )
    
    
    # only preload mask (B,L)
    gen_assembly_code += preload_act_asm_scale(
        vlen=vlen,
        preload_len=preload_amount,
        batch=1,
        hidden_size=batch_size*vlen,
        scale=batch_size*vlen,
        alive_registers=[1,2,3],  # [a_actual_register, set_stride_register, result_register]
        act_hbm_offset=0,
        act_vram_offset=mask_offset_address,
        activation_offset_reg=1
    )
    
    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3,4,5,6,7,8]
    )


    if TEST_MODE == "edge":
        gen_assembly_code += get_transfer_index_edge(
            alive_registers=[4,5,6,7,8,9,10,11,12,13,14,15],
            logits_base_address=logits_offset_address,
            transfer_idx_base_address=transfer_idx_offset_address,
            mask_base_address=mask_offset_address,
            x0_p_base_address=x0_p_offset_address,
            k_values=k_values_list,
            vlen=vlen,
            preload_len=preload_amount,
            T=steps,
            repeat_times=repeat_times,
            batch_size=batch_size,
            prompt_batch_size=prompt_batch_size,
            vocal_size_single=vocal_size_single,
            gen_length=gen_length,
        )
    else:
        gen_assembly_code += get_transfer_index_performance(
            alive_registers=[4,5,6,7,8,9,10,11,12,13,14,15],
            logits_base_address=logits_offset_address,
            transfer_idx_base_address=transfer_idx_offset_address,
            mask_base_address=mask_offset_address,
            x0_p_base_address=x0_p_offset_address,
            k_values=k_values_list,
            vlen=vlen,
            preload_len=preload_amount,
            T=steps,
            batch_size=batch_size,
            prompt_batch_size=prompt_batch_size,
            batch_R=batch_R,
            vocal_size=vocal_size,
            gen_length=gen_length,
        )
    
    
    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload, int_preload)
    create_mem_for_sim(data_size=256, mode="behave_sim", asm="dllm", data=None, specified_data_order = ["logits", "mask", "int"])
