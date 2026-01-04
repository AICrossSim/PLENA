import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import Tensor, nn
# from acc_simulator.quantize.quantized_layers.linear import MXFPLinearPTQ
from test_data_gen import get_weights_path, generate_and_save_random_weights
from compiler.asm_templates import argmax_debug, stable_max_softmax_method, preload_act_asm_scale, reset_reg_asm, preload_addr_reg_asm
from create_sim_env import create_sim_env
from sim_env_utils import create_mem_for_sim
import torch.nn.functional as F

from tools.memory_mapping.hbm_addr_map import align_addr_to_hbm_bandwidth

class TEST(torch.nn.Module):
    def __init__(self, mode='stable_max'):
        """
        Args:
            mode: 'argmax' or 'stable_max'
                - 'argmax': Use argmax method
                - 'stable_max': Use stable max softmax method to compute reciprocal
        """
        super().__init__()
        self.mode = mode
        self.weight = nn.Parameter(torch.ones(128))
        
        if mode not in ['argmax', 'stable_max']:
            raise ValueError(f"mode must be 'argmax' or 'stable_max', but got '{mode}'")

    def _argmax(self, x):
        x0 = torch.argmax(x, dim=-1)              # (B, L)
        print('x = ',x)
        print('x0 = ',x0)
        return x0
    
    def _stable_max_method(self, logits):
        # Method 2: use max logit for numerical stability (no explicit softmax)
        m = logits.max(dim=-1).values             # (B, L)
        sub_result = logits - m.unsqueeze(-1)     # (B, L, V)
        exp_shifted = torch.exp(sub_result)       # (B, L, V)
        denom = exp_shifted.sum(dim=-1)           # (B, L)
        reciprocal_denom = 1.0 / denom            # (B, L)

        print('reciprocal_denom.shape = ', reciprocal_denom.shape)
        return reciprocal_denom

    def forward(self, input):
        x = input
        if self.mode == 'argmax':
            output = self._argmax(x)
        elif self.mode == 'stable_max':
            output = self._stable_max_method(x.float()).type_as(x)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
        return output


if __name__ == "__main__":

    # ============ Configuration ============
    # Select test mode: 'argmax' or 'stable_max'
    TEST_MODE = 'stable_max'  # Change this to switch test mode
    # ========================================
    
    vocal_size=64
    gen_length = 64
    vlen = 64
    batch_size = 4
    preload_amount=4
    hbm_data_width=64
    real_data_ratio = (8*8 + 8) / (8 * 8)
    fp_preload = [0.0, 0.0, 0.0]

    
    torch.manual_seed(   42   )
    logits = torch.randn(batch_size, gen_length, vocal_size)

    input_tensor = logits
    original_layer = TEST(mode=TEST_MODE)
    original_output = original_layer(input_tensor)

    golden_result = {
        "input_tensor": input_tensor,
        "original_output": original_output
    }
    
    print(f"==================== Test Mode: {TEST_MODE} ====================")
    
    gen_assembly_code = "; Argmax for dLLM Generation \n"

    # Set the VRAM address offsets
    output_offset_address = 0
    logtis_offset_address = (batch_size * vlen)
    
    # Set the addr offset for weight and bias
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1],
        available_registers=[1],
        addr_reg_val=[int(align_addr_to_hbm_bandwidth(batch_size*gen_length*vocal_size*real_data_ratio, hbm_data_width))]
    )

    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3]
    )
    
    # Gen Activation Preload
    gen_assembly_code += preload_act_asm_scale(
        vlen=vlen,
        preload_len=preload_amount,
        batch=batch_size,
        hidden_size=gen_length*vocal_size,
        scale = batch_size*gen_length*vocal_size,
        alive_registers=[1,2,3],  # [a_actual_register, set_stride_register, result_register]
        act_hbm_offset=0,
        act_vram_offset=logtis_offset_address,
        activation_offset_reg=0
    )

    # Reset the registers
    gen_assembly_code += reset_reg_asm(
        alive_registers=[1,2,3,4,5]
    )
    
    # Generate corresponding assembly code based on mode
    if TEST_MODE == 'argmax':
        gen_assembly_code += argmax_debug(
            alive_registers=[1,2,3,4,5],                  # [input_addr, output_addr, len_addr, max_idx_addr, max_idx_offset_addr]
            input_base_address= logtis_offset_address,    # base address of input_tensor in VRAM
            output_base_address= output_offset_address,
            vlen=vlen,
            batch_size=batch_size,
            gen_length=gen_length,
            vocal_size=vocal_size,
        )
    elif TEST_MODE == 'stable_max':
        gen_assembly_code += stable_max_softmax_method(
            alive_registers=[1,2,3,4],                    # [input_addr, output_addr, len_addr]
            input_base_address= logtis_offset_address,    # base address of input_tensor in VRAM
            output_base_address= output_offset_address,   # base address of output_tensor in VRAM
            vlen=vlen,
            batch_size=batch_size,
            gen_length=gen_length,
            vocal_size=vocal_size,
        )
    else:
        raise ValueError(f"Unknown test mode: {TEST_MODE}")


    create_sim_env(input_tensor, gen_assembly_code, golden_result, fp_preload)
    create_mem_for_sim(data_size=256, mode="behave_sim", asm="dllm", data=None, specified_data_order = ["input_tensor"])
    
    