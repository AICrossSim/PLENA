import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import Tensor, nn
import torch.nn.functional as F
from test_data_gen import get_weights_path, generate_and_save_random_weights
from compiler.asm_templates import topk_mask_debug, select_vvm_debug, preload_act_asm, reset_reg_asm, preload_addr_reg_asm, topk_mask_simple
from create_sim_env import create_sim_env_dllm
from create_sim_env import create_sim_env
from sim_env_utils import build_fake_sim_env
from tools.memory_mapping.hbm_addr_map import align_addr_to_hbm_bandwidth

def get_transfer_index_topk(
    confidence: torch.Tensor,      # (B, L) float
    mask_index: torch.Tensor,      # (B, L) bool
    num_transfer_tokens: torch.Tensor,  # (B,) long
):
    """
    PyTorch implementation of Top-K mask selection.
    Mimics lines 398-412 from generate.py
    
    This function implements the V_TOPK_MASK instruction logic:
    
    Input:
        confidence:  [0.88, 0.92, 0.38, 0.96, ...]  (VRAM address 0)
        input_mask:  [1,    0,    1,    1,    ...]  (VRAM address 256)
        k = 8
    
    Processing Steps:
        Step 1: Read data from VRAM
                Read confidence vector and input mask in parallel
        
        Step 2: Mask invalid positions
                masked_conf: [0.88, -∞, 0.38, 0.96, ...]
                Set non-masked positions to negative infinity
        
        Step 3: Top-K selection
                top-8 indices: [3, 30, 0, 10, 8, 12, 16, 32]
                Find indices of k largest values using sort + threshold
        
        Step 4: Create output mask
                output: [1, 0, 0, 1, 0, ..., 1, ...]
                Scatter 1.0 to top-k positions, 0.0 elsewhere
        
        Step 5: AND with original mask
                Ensure output is 1 only where original mask was valid
        
        Step 6: Write back to VRAM (address 512)
                final_output: [1, 0, 0, 1, 0, ..., 1, ...]
    
    Args:
        confidence: (B, L) float — confidence scores for each position
        mask_index: (B, L) bool — which positions are valid for selection
        num_transfer_tokens: (B,) long — how many tokens to select per batch
    
    Returns:
        transfer_index: (B, L) bool — which positions are selected (top-k)
    """
    # Set non-masked positions to -inf
    neg_inf = torch.tensor(torch.finfo(confidence.dtype).min, device=confidence.device, dtype=confidence.dtype)
    confidence_masked = torch.where(mask_index, confidence, neg_inf)  # (B, L)
    
    # Ensure shape (B,) long
    if num_transfer_tokens.dim() == 2 and num_transfer_tokens.size(1) == 1:
        num_transfer_tokens = num_transfer_tokens.squeeze(1)
    num_transfer_tokens = num_transfer_tokens.to(dtype=torch.long, device=confidence.device)
    num_transfer_tokens = torch.clamp(num_transfer_tokens, min=0)
    
    # Sort confidences descending
    values, idx = torch.sort(confidence_masked, dim=1, descending=True)
    
    B, L = confidence_masked.shape
    # Build a mask that is True for the first k[b] columns in each row (sorted order)
    cols = torch.arange(L, device=confidence.device).unsqueeze(0).expand(B, L)   # (B, L)
    k_expanded = num_transfer_tokens.unsqueeze(1).expand(B, L)                   # (B, L)
    select_sorted = cols < k_expanded                                            # (B, L) bool
    
    # Scatter the sorted True/False back to original column order
    transfer_int = torch.zeros(B, L, device=confidence.device, dtype=torch.int8) # (B, L)
    transfer_int = transfer_int.scatter(1, idx, select_sorted.to(torch.int8))
    transfer_index = transfer_int.bool() & mask_index  # ensure we never select unmasked
    
    return transfer_index


class TopKMaskModule(torch.nn.Module):
    """
    Test module that wraps the Top-K mask selection logic.
    """
    def __init__(self):
        super().__init__()
        # Dummy parameter to make it a valid nn.Module
        self.dummy = nn.Parameter(torch.ones(1))

    def forward(self, confidence, mask_index, num_transfer_tokens):
        """
        Args:
            confidence: (B, L) float — confidence scores
            mask_index: (B, L) bool — valid positions mask
            num_transfer_tokens: (B,) long — k values per batch
        
        Returns:
            transfer_index: (B, L) bool — selected positions mask
        """
        return get_transfer_index_topk(confidence, mask_index, num_transfer_tokens)





if __name__ == "__main__":
    # Test parameters
    batch_size = 4
    seq_length = 64
    vlen = 64
    preload_amount = 4
    real_data_ratio = (8*8 + 8) / (8 * 8)
    hbm_data_width = 64
    fp_preload = [0.0, 1e-6, 1/seq_length]
    
    # Different k values for each batch item (number of tokens to select)
    k_values = [8, 8, 8, 8]
    
    # Generate test data
    torch.manual_seed(42)
    
    # Generate random confidence scores (simulating softmax probabilities)
    confidence = torch.rand(batch_size, seq_length, dtype=torch.float32)
    
    # Generate random mask (some positions are masked, some are not)
    mask_index = torch.rand(batch_size, seq_length) > 0.3  # ~70% positions are valid
    
    # K values for each batch
    num_transfer_tokens = torch.tensor(k_values, dtype=torch.long)
    
    # Create test module
    test_module = TopKMaskModule()
    weights = test_module.state_dict()
    
    # Run golden reference
    original_output = test_module(confidence, mask_index, num_transfer_tokens)
    original_output = original_output.float()
    mask_index = mask_index.float()
    # Prepare input tensors for simulator
    input_tensor = {
        "confidence": confidence,
        "mask_index": mask_index,  # Convert bool to float for storage
    }
    golden_result = {
        "input_tensor": input_tensor,
        "weights": weights,
        "original_output": original_output,  # Convert bool to float for comparison
    }
    
    # Generate assembly code
    gen_assembly_code = "; Top-K Mask Selection for dLLM Generation \n"

    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1,2],
        available_registers=[1,2],
        addr_reg_val=[int(align_addr_to_hbm_bandwidth(batch_size * seq_length * real_data_ratio, hbm_data_width)),int(2*align_addr_to_hbm_bandwidth(batch_size * seq_length * real_data_ratio, hbm_data_width))]
    )

    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3]
    )
    
    # Gen Activation Preload
    gen_assembly_code += preload_act_asm(
        vlen=vlen,
        preload_len=preload_amount,
        batch=batch_size,
        hidden_size=1*seq_length,
        alive_registers=[1,2,3],  # [a_actual_register, set_stride_register, result_register]
        act_vram_offset=0,
        activation_offset_reg=0
    )

    gen_assembly_code += preload_act_asm(
        vlen=vlen,
        preload_len=preload_amount,
        batch=batch_size,
        hidden_size=1*seq_length,
        alive_registers=[1,2,3],  # [a_actual_register, set_stride_register, result_register]
        act_vram_offset=batch_size*seq_length,
        activation_offset_reg=1
    )
    
    gen_assembly_code += preload_act_asm(
        vlen=vlen,
        preload_len=preload_amount,
        batch=batch_size,
        hidden_size=1*seq_length,
        alive_registers=[1,2,3],  # [a_actual_register, set_stride_register, result_register]
        act_vram_offset=2*batch_size*seq_length,
        activation_offset_reg=2
    )
    
    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3,4]
    )
    
    # Use topk_mask_debug to process all batches
    gen_assembly_code += topk_mask_debug(
        alive_registers=[1,2,3,4],
        confidence_base_address=0,
        mask_base_address=batch_size * seq_length,
        output_base_address=2 * batch_size * seq_length,
        k_values=k_values,
        vlen=vlen,
        batch_size=batch_size,
    )

    create_sim_env(input_tensor, weights, gen_assembly_code, golden_result, fp_preload)
    build_fake_sim_env(data_size=256, mode="behave_sim", asm="dllm", data=None, specified_data_order = ["confidence", "mask_index"])
