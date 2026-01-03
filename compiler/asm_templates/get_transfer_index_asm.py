import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from .preload_act import preload_act_asm_scale

def get_transfer_index_edge(
    alive_registers: List[int],  # Can be int or hex string, will be converted to hex
    logits_base_address: int, # input (B,L,V)
    mask_base_address: int,   # input (B,L)
    transfer_idx_base_address: int, # input (B,L)
    x0_p_base_address: int,   # x0_p (B,L)
    k_values: List[int],
    vlen: int,
    preload_len: int,
    T: int, #time step for duffusion
    repeat_times: int,
    batch_size: int,
    prompt_batch_size: int,
    vocal_size_single: int,
    gen_length: int,  # L dimension (e.g., 64)
) -> str:
    """
    Generate assembly code for Argnmux.
    Note: alive_registers should contain integers, they will be formatted as hex for assembly.
    """
    # Convert register numbers to hex format (required by parser)
    def reg_hex(reg_num):
        return f"{reg_num:X}"  # Format as uppercase hex
    
    logits_addr       = reg_hex(alive_registers[0])
    mask_addr         = reg_hex(alive_registers[1])
    transfer_idx_addr = reg_hex(alive_registers[2])
    x0_p_addr         = reg_hex(alive_registers[4])
    k_reg             = reg_hex(alive_registers[5])
    max_idx_addr      = reg_hex(alive_registers[6])
    offset_addr       = reg_hex(alive_registers[7])  # offset register for previous idx in the continus mode of V_RED_MAX_IDX
    x_addr            = reg_hex(alive_registers[8])  # x register (int sram)
    x0_addr           = reg_hex(alive_registers[9])  # x0 register (int sram)
    len_reg           = reg_hex(alive_registers[10]) # length register for vector operations
    
    generated_code = "; get_transfer_index for dLLM generation \n"
    generated_code += f"S_ADDI_INT gp{logits_addr}, gp0, {logits_base_address} \n"
    generated_code += f"S_ADDI_INT gp{mask_addr}, gp0, {mask_base_address} \n"
    generated_code += f"S_ADDI_INT gp{transfer_idx_addr}, gp0, {transfer_idx_base_address} \n"
    generated_code += f"S_ADDI_INT gp{x0_p_addr}, gp0, {x0_p_base_address} \n"
    generated_code += f"S_ADDI_INT gp{len_reg}, gp0, {gen_length} \n"
    
    for t in range(T):  
        # Loop over batch_size rows
        for batch_idx in range(batch_size):  
            for i in range(gen_length):
                # calculate the MAX in the entire V dim
                generated_code += f"S_ADD_FP f1, f0, f0 \n"  # Initialize f1 to 0 (for V_RED_MAX_IDX)
                generated_code += f"S_ADD_FP f2, f0, f0 \n"  # Initialize f2 to 0 (for V_RED_SUM)
                generated_code += f"S_ADD_INT gp{max_idx_addr}, gp0, gp0 \n"  # Initialize idx to 0
                generated_code += f"S_ADD_INT gp{offset_addr},  gp0, gp0 \n"  # Initialize offset to 0
                for j in range(repeat_times):
                    hbm_offset  = t*batch_size*gen_length*(repeat_times*vocal_size_single) + batch_idx*gen_length*(repeat_times*vocal_size_single)  + i * (repeat_times*vocal_size_single) + j * vocal_size_single
                    vram_offset = logits_base_address
                    generated_code += preload_act_asm_scale(
                        vlen=vlen,
                        preload_len=preload_len,
                        batch=1,
                        hidden_size=vocal_size_single,
                        scale=T*batch_size*gen_length*vocal_size_single*repeat_times,
                        alive_registers=[1,2,3],  # [a_actual_register, set_stride_register, result_register]
                        act_hbm_offset=hbm_offset,
                        act_vram_offset=vram_offset,
                        activation_offset_reg=0
                    )
                    
                    for k in range(vocal_size_single // vlen):
                        # generated_code += f"V_RED_MAX f1, gp{logits_addr},0\n"
                        generated_code += f"V_RED_MAX_IDX gp{max_idx_addr}, gp{logits_addr}, gp{offset_addr}, f1\n"
                        # Update gp{logits_addr} and offset
                        generated_code += f"S_ADDI_INT gp{logits_addr}, gp{logits_addr}, {vlen} \n"
                        generated_code += f"S_ADDI_INT gp{offset_addr}, gp{offset_addr}, {vlen} \n"
                    generated_code += f"S_ADDI_INT gp{logits_addr}, gp0, {logits_base_address} \n"
                    
                
                # calculate the exp(logits - max_logits) in the entire V dim
                for j in range(repeat_times):
                    hbm_offset  = t*batch_size*gen_length*(repeat_times*vocal_size_single) + batch_idx*gen_length*(repeat_times*vocal_size_single)  + i * (repeat_times*vocal_size_single) + j * vocal_size_single
                    vram_offset = logits_base_address
                    generated_code += preload_act_asm_scale(
                        vlen=vlen,
                        preload_len=preload_len,
                        batch=1,
                        hidden_size=vocal_size_single,
                        scale=T*batch_size*gen_length*vocal_size_single*repeat_times,
                        alive_registers=[1,2,3],  # [a_actual_register, set_stride_register, result_register]
                        act_hbm_offset=hbm_offset,
                        act_vram_offset=vram_offset,
                        activation_offset_reg=0
                    )
                    for k in range(vocal_size_single // vlen):
                        # S' = S - max_logits
                        generated_code += f"V_SUB_VF gp{logits_addr}, gp{logits_addr}, f1, 0\n"
                        # P = exp(S')
                        generated_code += f"V_EXP_V gp{logits_addr}, gp{logits_addr}, 0 \n"
                        # SUM
                        generated_code += f"V_RED_SUM f2, gp{logits_addr}\n"
                        # update gp{logits_addr}
                        generated_code += f"S_ADDI_INT gp{logits_addr}, gp{logits_addr}, {vlen} \n"
                    generated_code += f"S_ADDI_INT gp{logits_addr}, gp0, {logits_base_address} \n"
                

                # Compute reciprocal
                generated_code += f"S_RECI_FP f2, f2 \n"
                # Store reciprocal value from f2 to FP_MEM: FP_MEM[fp_reg<gp0>+i] = fp_reg<f2>
                generated_code += f"S_ST_FP f2, gp0, {i} \n"
                # Store the max_idx from gp{max_idx_addr} into INT_MEM, INT_MEM[int_reg<gp0>+ (prompt_batch_size+1)*gen_length +(batch_idx*vlen + i)] = gp{max_idx_addr}
                generated_code += f"S_ST_INT gp{max_idx_addr}, gp0, {(prompt_batch_size+0)*gen_length + batch_idx*gen_length + i} \n"
            
            # grab these accumulated gen_length scalar(stored reciprocal) into SRAM to form an vector again
            # SRAM[gp<x0_p_addr>] = FP_MEM[gp0+0 : gp0+0+gen_length]
            generated_code += f"S_MAP_V_FP gp{x0_p_addr}, gp0, 0, gp{len_reg} \n"
            
            # Load k value for this batch into scalar register
            k_value = k_values[t][batch_idx] if batch_idx < len(k_values) else k_values[0][0]
            generated_code += f"S_ADDI_INT gp{k_reg}, gp0, {k_value} \n"
            
            # Execute V_TOPK_MASK instruction
            # V_TOPK_MASK rd, rs1, rs2, k_scalar, len
            # rd: output mask (vector), rs1: confidence vector, rs2: input mask (vector), k_scalar: k value (scalar), len: vector length
            generated_code += f"V_TOPK_MASK gp{transfer_idx_addr}, gp{x0_p_addr}, gp{mask_addr}, gp{k_reg}, gp{len_reg}\n"

            # Setup base addresses in registers for current batch
            generated_code += f"S_ADDI_INT gp{x_addr}, gp0, {(prompt_batch_size+0)*gen_length + batch_idx*gen_length} \n"  # output base (gen_length elements)
            generated_code += f"S_ADDI_INT gp{x0_addr}, gp0, {batch_idx*gen_length} \n"        # x base (gen_length elements, src2)
            # mask is in VECTOR SRAM at gp{mask_addr} (gen_length float elements, already set up earlier)
            
            # Execute S_SELECT_INT: processes gen_length elements in one instruction
            # x0 = torch.where(mask_index, x0, x)
            generated_code += f"S_SELECT_INT gp{x_addr}, gp{x_addr}, gp{x0_addr}, gp{mask_addr}, gp{len_reg} \n"
            # x[transfer_index] = x0[transfer_index]
            # equal to: x = torch.where(transfer_index, x0, x)
            generated_code += f"S_SELECT_INT gp{x0_addr}, gp{x_addr}, gp{x0_addr}, gp{transfer_idx_addr}, gp{len_reg} \n"
            
            # Increment all address pointers by vlen (move to next row)
            generated_code += f"S_ADDI_INT gp{x0_p_addr}, gp{x0_p_addr}, {vlen} \n"
            generated_code += f"S_ADDI_INT gp{mask_addr}, gp{mask_addr}, {vlen} \n"
            generated_code += f"S_ADDI_INT gp{transfer_idx_addr}, gp{transfer_idx_addr}, {vlen} \n"
            
    return generated_code



def get_transfer_index_performance(
    alive_registers: List[int],  # Can be int or hex string, will be converted to hex
    logits_base_address: int, # input (B,L,V)
    transfer_idx_base_address: int, # input (B,L)
    mask_base_address: int,   # input (B,L)
    x0_p_base_address: int,   # x0_p (B,L)
    k_values: List[int],
    vlen: int,
    preload_len: int,
    T: int, #time step for duffusion
    batch_size: int,
    prompt_batch_size: int,
    batch_R:int, 
    vocal_size: int,
    gen_length: int,  # L dimension (e.g., 64)
) -> str:
    """
    Generate assembly code for Argnmux.
    Note: alive_registers should contain integers, they will be formatted as hex for assembly.
    """
    # Convert register numbers to hex format (required by parser)
    def reg_hex(reg_num):
        return f"{reg_num:X}"  # Format as uppercase hex
    
    logits_addr       = reg_hex(alive_registers[0])
    mask_addr         = reg_hex(alive_registers[1])
    transfer_idx_addr = reg_hex(alive_registers[2])
    x0_p_addr         = reg_hex(alive_registers[4])
    k_reg             = reg_hex(alive_registers[5])
    max_idx_addr      = reg_hex(alive_registers[6])
    offset_addr       = reg_hex(alive_registers[7])  # offset register for previous idx in the continus mode of V_RED_MAX_IDX
    x_addr            = reg_hex(alive_registers[8])  # x register (int sram)
    x0_addr           = reg_hex(alive_registers[9])  # x0 register (int sram)
    len_reg           = reg_hex(alive_registers[10]) # length register for vector operations
    
    generated_code = "; get_transfer_index for dLLM generation \n"
    generated_code += f"S_ADDI_INT gp{logits_addr}, gp0, {logits_base_address} \n"
    generated_code += f"S_ADDI_INT gp{mask_addr}, gp0, {mask_base_address} \n"
    generated_code += f"S_ADDI_INT gp{transfer_idx_addr}, gp0, {transfer_idx_base_address} \n"
    generated_code += f"S_ADDI_INT gp{x0_p_addr}, gp0, {x0_p_base_address} \n"
    generated_code += f"S_ADDI_INT gp{len_reg}, gp0, {gen_length} \n"
    for t in range(T):  
        # Loop over batch_size rows
        for batch_idx in range(batch_size//batch_R):  
            # 15MB for [1, 64,126468] staoring as 16bit in vector sram
            hbm_offset  = t*batch_size*gen_length*vocal_size + batch_idx*batch_R*gen_length*vocal_size
            vram_offset = logits_base_address
            generated_code += preload_act_asm_scale(
                vlen=vlen,
                preload_len=preload_len,
                batch=1,
                hidden_size=gen_length*vocal_size*batch_R,
                scale=T*batch_size*gen_length*vocal_size,
                alive_registers=[1,2,3],  # [a_actual_register, set_stride_register, result_register]
                act_hbm_offset=hbm_offset,
                act_vram_offset=vram_offset,
                activation_offset_reg=0
            )
            for batch_R_idx in range(batch_R):
                for i in range(gen_length):
                    logits_i_address = logits_base_address + (batch_R_idx*gen_length + i) *vlen*(vocal_size // vlen)
                    if logits_i_address <= 262143:
                        generated_code += f"S_ADDI_INT gp{logits_addr}, gp0, {logits_i_address} \n"
                    else:
                        generated_code += f"S_LUI_INT gp{logits_addr}, {logits_i_address >> 12} \n"
                        generated_code += f"S_ADDI_INT gp{logits_addr}, gp{logits_addr}, {logits_i_address & 0xFFF} \n"
                    # calculate the MAX in the entire V dim
                    generated_code += f"S_ADD_FP f1, f0, f0 \n"  # Initialize f2 to 0 (for V_RED_MAX_IDX)
                    generated_code += f"S_ADD_FP f2, f0, f0 \n"
                    generated_code += f"S_ADD_INT gp{max_idx_addr}, gp0, gp0 \n"  # Initialize idx to 0
                    generated_code += f"S_ADD_INT gp{offset_addr},  gp0, gp0 \n"  # Initialize offset to 0
                    
                    for j in range(vocal_size // vlen):
                        generated_code += f"V_RED_MAX_IDX gp{max_idx_addr}, gp{logits_addr}, gp{offset_addr}, f1\n"
                        # Update gp{logits_addr} and offset
                        generated_code += f"S_ADDI_INT gp{logits_addr}, gp{logits_addr}, {vlen} \n"
                        generated_code += f"S_ADDI_INT gp{offset_addr}, gp{offset_addr}, {vlen} \n"
                    
                    if logits_i_address <= 262143:
                        generated_code += f"S_ADDI_INT gp{logits_addr}, gp0, {logits_i_address} \n"
                    else:
                        generated_code += f"S_LUI_INT gp{logits_addr}, {logits_i_address >> 12} \n"
                        generated_code += f"S_ADDI_INT gp{logits_addr}, gp{logits_addr}, {logits_i_address & 0xFFF} \n"
                    
                    
                    for j in range(vocal_size // vlen):    
                        # calculate the exp(logits - max_logits) in the entire V dim
                        # S' = S - max_logits
                        generated_code += f"V_SUB_VF gp{logits_addr}, gp{logits_addr}, f1, 0\n"
                        # P = exp(S')
                        generated_code += f"V_EXP_V gp{logits_addr}, gp{logits_addr}, 0 \n"
                        # SUM
                        generated_code += f"V_RED_SUM f2, gp{logits_addr}\n"
                        # update gp{logits_addr}
                        generated_code += f"S_ADDI_INT gp{logits_addr}, gp{logits_addr}, {vlen} \n"
                    
                    # Compute reciprocal
                    generated_code += f"S_RECI_FP f2, f2 \n"
                    # Store reciprocal value from f1 to FP_MEM: FP_MEM[fp_reg<gp0>+i] = fp_reg<f1>
                    generated_code += f"S_ST_FP f2, gp0, {i} \n"
                    # Store the max_idx from gp{max_idx_addr} into INT_MEM, INT_MEM[int_reg<gp0>+ (prompt_batch_size+1)*gen_length +(batch_idx*vlen + i)] = gp{max_idx_addr}
                    generated_code += f"S_ST_INT gp{max_idx_addr}, gp0, {(prompt_batch_size+0)*gen_length + (batch_idx*batch_R+batch_R_idx)*gen_length + i} \n"
                
                # grab these accumulated gen_length scalar(stored reciprocal) into SRAM to form an vector again
                # SRAM[gp<x0_p_addr>] = FP_MEM[gp0+0 : gp0+0+gen_length]
                generated_code += f"S_MAP_V_FP gp{x0_p_addr}, gp0, 0, gp{len_reg} \n"
            
                
                # Load k value for this batch into scalar register
                k_value = k_values[t][(batch_idx*batch_R+batch_R_idx)] if (batch_idx*batch_R+batch_R_idx) < len(k_values) else k_values[0][0]
                generated_code += f"S_ADDI_INT gp{k_reg}, gp0, {k_value} \n"
            
                # Execute V_TOPK_MASK instruction
                # V_TOPK_MASK rd, rs1, rs2, k_scalar, len
                # rd: output mask (vector), rs1: confidence vector, rs2: input mask (vector), k_scalar: k value (scalar), len: vector length
                generated_code += f"V_TOPK_MASK gp{transfer_idx_addr}, gp{x0_p_addr}, gp{mask_addr}, gp{k_reg}, gp{len_reg}\n"

                # Setup base addresses in registers for current batch
                generated_code += f"S_ADDI_INT gp{x_addr}, gp0, {(prompt_batch_size+0)*gen_length + (batch_idx*batch_R+batch_R_idx)*gen_length} \n"  # output base (gen_length elements)
                generated_code += f"S_ADDI_INT gp{x0_addr}, gp0, {(batch_idx*batch_R+batch_R_idx)*gen_length} \n"        # x base (gen_length elements, src2)
                # mask is in VECTOR SRAM at gp{mask_addr} (gen_length float elements, already set up earlier)
            
                # Execute S_SELECT_INT: processes gen_length elements in one instruction
                # x0 = torch.where(mask_index, x0, x)
                generated_code += f"S_SELECT_INT gp{x_addr}, gp{x_addr}, gp{x0_addr}, gp{mask_addr}, gp{len_reg} \n"
                # x[transfer_index] = x0[transfer_index]
                # equal to: x = torch.where(transfer_index, x0, x)
                generated_code += f"S_SELECT_INT gp{x0_addr}, gp{x_addr}, gp{x0_addr}, gp{transfer_idx_addr}, gp{len_reg} \n"
                
                # Increment all address pointers by vlen (move to next row)
                generated_code += f"S_ADDI_INT gp{x0_p_addr}, gp{x0_p_addr}, {vlen} \n"
                generated_code += f"S_ADDI_INT gp{mask_addr}, gp{mask_addr}, {vlen} \n"
                generated_code += f"S_ADDI_INT gp{transfer_idx_addr}, gp{transfer_idx_addr}, {vlen} \n"
            
    return generated_code