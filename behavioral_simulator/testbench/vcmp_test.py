import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import torch
from torch import Tensor, nn
from test_data_gen import get_weights_path, generate_and_save_random_weights
from compiler.asm_templates import vcmp_eq_asm, preload_act_asm, reset_reg_asm, preload_addr_reg_asm, vcmp_asm_debug
from create_sim_env import create_sim_env, create_sim_env_dllm
from sim_env_utils import build_fake_sim_env
import torch.nn.functional as F

from tools.memory_mapping.hbm_addr_map import align_addr_to_hbm_bandwidth


class TEST(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(128))

    def _vcmp_eq(self, vec, scalar):
        """Vector compare equal"""
        # Returns 1.0 where vec[i] == scalar, else 0.0
        return (vec == scalar).float()
    
    def _scatter_with_vcmp(self, dst, value, positions, idx):
        """Scatter using V_CMP + V_SELECT pattern"""
        # Generate one-hot mask
        mask = (positions == idx).float()
        # Conditional update: dst = mask ? value : dst
        result = torch.where(mask.bool(), value, dst)
        return result

    def forward(self, vec, scalar):
        return self._vcmp_eq(vec.float(), scalar).type_as(vec)


if __name__ == "__main__":
    print("=" * 80)
    print("V_CMP Instruction Test")
    print("=" * 80)
    
    # Test parameters
    vocal_size = 64
    hidden_size = 64
    vlen = 64
    batch_size = 4
    preload_amount = 4
    real_data_ratio = (8*8 + 8) / (8 * 8)
    hbm_data_width = 64
    # fp_preload: position 0-2 for standard preload, position 5 for scalar value 5.0
    fp_preload = [0.0, 1e-6, 1/hidden_size, 0.0, 0.0, 5.0]

    # ===== Test 1: V_CMP_EQ_VF =====
    print("\n" + "=" * 80)
    print("Test 1: V_CMP_EQ_VF - Vector Compare Equal with Scalar")
    print("=" * 80)
    
    torch.manual_seed(42)
    # Create test vector with some known values

    input_tensor = torch.tensor([
        [1.0, 2.0, 5.0, 3.0, 5.0, 4.0, 5.0, 2.0] + [0.0] * 56,
        [5.0, 5.0, 1.0, 5.0, 2.0, 3.0, 4.0, 5.0] + [0.0] * 56,
        [2.0, 3.0, 4.0, 5.0, 5.0, 5.0, 1.0, 2.0] + [0.0] * 56,
        [5.0, 1.0, 2.0, 3.0, 4.0, 5.0, 5.0, 5.0] + [0.0] * 56,
    ])
    print('input_tensor.shape = ', input_tensor.shape)
    scalar_value = 5.0
    
    original_layer = TEST()
    weights = original_layer.state_dict()
    original_output = original_layer(input_tensor, scalar_value)
    
    #print(f"Input vector[0, :8]: {input_tensor[0, :8].tolist()}")
    ##print(f"Scalar value: {scalar_value}")
    #print(f"Expected mask[0, :8]: {original_output[0, :8].tolist()}")
    #print(f"  (1.0 where input == {scalar_value}, 0.0 elsewhere)")
    
    golden_result = {
        "input_tensor": input_tensor,
        "weights": weights,
        "original_output": original_output
    }
    
    gen_assembly_code = "; V_CMP_EQ_VF Test \n"
    
    # Set address registers
    gen_assembly_code += preload_addr_reg_asm(
        addr_reg_to_set=[1],
        available_registers=[1],
        addr_reg_val=[int(align_addr_to_hbm_bandwidth(batch_size * vocal_size * real_data_ratio, hbm_data_width))]
    )
    
    # Reset registers
    gen_assembly_code += reset_reg_asm(alive_registers=[1,2,3])
    
    # Preload input vector
    gen_assembly_code += preload_act_asm(
        vlen=vlen,
        preload_len=preload_amount,
        batch=batch_size,
        hidden_size=vocal_size,
        alive_registers=[1,2,3],
        act_vram_offset=0,
        activation_offset_reg=0
    )
    
    # Reset registers for execution
    gen_assembly_code += vcmp_asm_debug(
        alive_registers=[1,2,3,4],
        activation_base_address = 0,                           # input1 starts at VRAM offset 0
        scratchpad_base_address = batch_size * vocal_size,    # input2 starts after input1
        vlen=vlen,
        batch_size=batch_size,
    )
    create_sim_env(input_tensor, weights, gen_assembly_code, golden_result, fp_preload)
    build_fake_sim_env(data_size=256, mode="behave_sim", asm="vcmp_eq", data=None, specified_data_order=["input_tensor"])
    

    '''
    gen_assembly_code += reset_reg_asm(alive_registers=[1,2,3,4])
    
    scratchpad_addr = alive_registers[3]
    # Load scalar value into fp register
    gen_assembly_code += f"S_ADDI_INT gp{scratchpad_addr}, gp0, {scratchpad_base_address} \n"
    gen_assembly_code += f"S_ADDI_INT gp1, gp0, 0\n"  # input at VRAM offset 0
    gen_assembly_code += f"S_ADDI_INT gp2, gp0, {batch_size * vocal_size}\n"  # output after input
    gen_assembly_code += f"; Load scalar value {scalar_value} into f1\n"
    gen_assembly_code += f"S_ADD_FP f1, f0, f0\n"  # f1 = 0
    gen_assembly_code += f"S_ADDI_INT gp3, gp0, {int(scalar_value)}\n"  # gp3 = 5
    # Convert int to float (approximate, using the scalar as-is)
    # For simplicity, we'll use a preloaded value or assume scalar is set
    
    gen_assembly_code += f"; Batch 0: Compare vector with scalar\n"
    gen_assembly_code += vcmp_eq_asm(
        gp_dst=2,  # Output goes to gp2
        gp_vec=1,  # Input from gp1
        fp_scalar=3  # Scalar in f3 (we'll need to set this properly)
    )
    gen_assembly_code += f"S_ADDI_INT gp1, gp1, {vlen}\n"
    gen_assembly_code += f"S_ADDI_INT gp2, gp2, {vlen}\n"

    create_sim_env(input_data, weights, gen_assembly_code, golden_result, fp_preload)
    build_fake_sim_env(data_size=256, mode="behave_sim", asm="vcmp_eq", data=None, specified_data_order=["input_tensor"])
    '''

    '''
    # Execute V_CMP_EQ_VF for each batch
    for b in range(batch_size):
        gen_assembly_code += f"; Batch {b}: Compare vector with scalar\n"
        gen_assembly_code += vcmp_eq_asm(
            gp_dst=2,  # Output goes to gp2
            gp_vec=1,  # Input from gp1
            fp_scalar=3  # Scalar in f3 (we'll need to set this properly)
        )
        gen_assembly_code += f"S_ADDI_INT gp1, gp1, {vlen}\n"
        gen_assembly_code += f"S_ADDI_INT gp2, gp2, {vlen}\n"
    
    print("\n" + "=" * 80)
    print("Generated Assembly Code:")
    print("=" * 80)
    print(gen_assembly_code)
    
    create_sim_env(input_data, weights, gen_assembly_code, golden_result, fp_preload)
    build_fake_sim_env(data_size=256, mode="behave_sim", asm="vcmp_eq", data=None, specified_data_order=["input_tensor"])
    '''
    
    '''
    # ===== Test 3: Scatter using V_CMP + V_SELECT =====
    print("\n" + "=" * 80)
    print("Test 3: Scatter operation using V_CMP_EQ_VF + V_SELECT_VVM")
    print("=" * 80)
    
    # Create position vector [0, 1, 2, ..., L-1]
    positions = torch.arange(vocal_size).unsqueeze(0).expand(batch_size, -1).float()
    dst = torch.zeros(batch_size, vocal_size)
    value_vec = torch.ones(batch_size, vocal_size)
    
    # Scatter to positions [2, 5, 7]
    scatter_indices = [2, 5, 7]
    for idx in scatter_indices:
        mask = (positions == idx).float()
        dst = torch.where(mask.bool(), value_vec, dst)
    
    print(f"Position to scatter: {scatter_indices}")
    print(f"Result[0, :10]: {dst[0, :10].tolist()}")
    print(f"  (1.0 at positions {scatter_indices}, 0.0 elsewhere)")
    
    print("\n" + "=" * 80)
    print("✅ All V_CMP instruction tests defined successfully!")
    print("=" * 80)
    print("\nNote: To run the simulator, you need to:")
    print("1. Compile the Rust simulator with the new V_CMP instructions")
    print("2. Run: cargo build --release")
    print("3. Execute this test with the simulator backend")
    '''
