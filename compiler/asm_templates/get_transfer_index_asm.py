import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from .preload_act import preload_act_asm_scale



def get_transfer_index_long_debug(
    alive_registers: List[int],  # Can be int or hex string, will be converted to hex
    logits_base_address: int, # input (B,L,V)
    mask_base_address: int,   # input (B,L)
    transfer_idx_base_address: int, # input (B,L)
    temp_base_address: int,   # temp ()
    x0_p_base_address: int,   # x0_p (B,L)
    k_values: List[int],
    vlen: int,
    repeat_times: int,
    batch_size: int,
    prompt_batch_size: int,
    vocal_size_single: int,
    hidden_size: int,  # L dimension (e.g., 64)
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
    temp_addr         = reg_hex(alive_registers[3])
    x0_p_addr         = reg_hex(alive_registers[4])
    k_reg             = reg_hex(alive_registers[5])
    max_idx_addr      = reg_hex(alive_registers[6])
    offset_addr       = reg_hex(alive_registers[7])  # offset register for previous idx in the continus mode of V_RED_MAX_IDX
    x_addr            = reg_hex(alive_registers[8])  # x register (int sram)
    x0_addr           = reg_hex(alive_registers[9])  # x0 register (int sram)
    
    generated_code = "; get_transfer_index for dLLM generation \n"
    generated_code += f"S_ADDI_INT gp{logits_addr}, gp0, {logits_base_address} \n"
    generated_code += f"S_ADDI_INT gp{mask_addr}, gp0, {mask_base_address} \n"
    generated_code += f"S_ADDI_INT gp{transfer_idx_addr}, gp0, {transfer_idx_base_address} \n"
    generated_code += f"S_ADDI_INT gp{temp_addr}, gp0, {temp_base_address} \n"
    generated_code += f"S_ADDI_INT gp{x0_p_addr}, gp0, {x0_p_base_address} \n"
    
    for t in range(2):  
        # Loop over batch_size rows
        for batch_idx in range(batch_size):  
            for i in range(vlen):
                # calculate the MAX in the entire V dim
                generated_code += f"S_ADD_FP f1, f0, f0 \n"  # Initialize f1 to 0 (for V_RED_MAX)
                generated_code += f"S_ADD_FP f2, f0, f0 \n"  # Initialize f2 to 0 (for V_RED_MAX_IDX)
                generated_code += f"S_ADD_INT gp{max_idx_addr}, gp0, gp0 \n"  # Initialize idx to 0
                generated_code += f"S_ADD_INT gp{offset_addr},  gp0, gp0 \n"  # Initialize offset to 0
                for j in range(repeat_times):
                    hbm_offset  = t*batch_size*hidden_size*(repeat_times*vocal_size_single) + batch_idx*hidden_size*(repeat_times*vocal_size_single)  + i * (repeat_times*vocal_size_single) + j * vocal_size_single
                    vram_offset = logits_base_address
                    generated_code += preload_act_asm_scale(
                        vlen=vlen,
                        preload_len=1,
                        batch=1,
                        hidden_size=vocal_size_single,
                        scale=2*batch_size*hidden_size*vocal_size_single*repeat_times,
                        alive_registers=[1,2,3],  # [a_actual_register, set_stride_register, result_register]
                        act_hbm_offset=hbm_offset,
                        act_vram_offset=vram_offset,
                        activation_offset_reg=0
                    )
                    
                    for k in range(vocal_size_single // vlen):
                        generated_code += f"V_RED_MAX f1, gp{logits_addr},0\n"
                        generated_code += f"V_RED_MAX_IDX gp{max_idx_addr}, gp{logits_addr}, gp{offset_addr}, f2\n"
                        # Update gp{logits_addr} and offset
                        generated_code += f"S_ADDI_INT gp{logits_addr}, gp{logits_addr}, {vlen} \n"
                        generated_code += f"S_ADDI_INT gp{offset_addr}, gp{offset_addr}, {vlen} \n"
                    generated_code += f"S_ADDI_INT gp{logits_addr}, gp0, {logits_base_address} \n"
                    
                
                # calculate the exp(logits - max_logits) in the entire V dim
                for j in range(repeat_times):
                    hbm_offset  = t*batch_size*hidden_size*(repeat_times*vocal_size_single) + batch_idx*hidden_size*(repeat_times*vocal_size_single)  + i * (repeat_times*vocal_size_single) + j * vocal_size_single
                    vram_offset = logits_base_address
                    generated_code += preload_act_asm_scale(
                        vlen=vlen,
                        preload_len=1,
                        batch=1,
                        hidden_size=vocal_size_single,
                        scale=2*batch_size*hidden_size*vocal_size_single*repeat_times,
                        alive_registers=[1,2,3],  # [a_actual_register, set_stride_register, result_register]
                        act_hbm_offset=hbm_offset,
                        act_vram_offset=vram_offset,
                        activation_offset_reg=0
                    )
                    for k in range(vocal_size_single // vlen):
                        # S' = S - max_logits
                        generated_code += f"V_SUB_VF gp{temp_addr}, gp{logits_addr}, f1, 0\n"
                        # P = exp(S')
                        generated_code += f"V_EXP_V gp{temp_addr}, gp{temp_addr}, 0 \n"
                        # update gp{logits_addr} and gp{temp_addr}
                        generated_code += f"S_ADDI_INT gp{logits_addr}, gp{logits_addr}, {vlen} \n"
                        generated_code += f"S_ADDI_INT gp{temp_addr}, gp{temp_addr}, {vlen} \n"
                    generated_code += f"S_ADDI_INT gp{logits_addr}, gp0, {logits_base_address} \n"
                    generated_code += f"S_ADDI_INT gp{temp_addr}, gp0, {temp_base_address} \n"
                
                
                # calculate the SUM in the entire V dim, no need to load the logits this time
                for j in range(repeat_times):
                    for k in range(vocal_size_single // vlen):
                        # SUM
                        generated_code += f"V_RED_SUM f1, gp{temp_addr}\n"
                        # update gp{temp_addr}
                        generated_code += f"S_ADDI_INT gp{temp_addr}, gp{temp_addr}, {vlen} \n"
                    generated_code += f"S_ADDI_INT gp{temp_addr}, gp0, {temp_base_address} \n"
                

                # Compute reciprocal
                generated_code += f"S_RECI_FP f1, f1 \n"
                # Store reciprocal value from f1 to FP_MEM: FP_MEM[fp_reg<gp0>+i] = fp_reg<f1>
                generated_code += f"S_ST_FP f1, gp0, {i} \n"

                # Store the max_idx from gp{max_idx_addr} into INT_MEM, INT_MEM[int_reg<gp0>+ (prompt_batch_size+1)*hidden_size +(batch_idx*vlen + i)] = gp{max_idx_addr}
                generated_code += f"S_ST_INT gp{max_idx_addr}, gp0, {(prompt_batch_size+1)*hidden_size + batch_idx*vlen + i} \n"
            
            # grab these accumulated vlen scalar(stored reciprocal) into SRAM to form an vector again
            # SRAM[gp<x0_p_addr>] = FP_MEM[gp0+0 : gp0+0+vlen]
            generated_code += f"S_MAP_V_FP gp{x0_p_addr}, gp0, 0 \n"
            
            # Load k value for this batch into scalar register
            k_value = k_values[t][batch_idx] if batch_idx < len(k_values) else k_values[0][0]
            generated_code += f"S_ADDI_INT gp{k_reg}, gp0, {k_value} \n"
            
            # Execute V_TOPK_MASK instruction
            # V_TOPK_MASK rd, rs1, rs2, k_scalar
            # rd: output mask (vector), rs1: confidence vector, rs2: input mask (vector), k_scalar: k value (scalar)
            generated_code += f"V_TOPK_MASK gp{transfer_idx_addr}, gp{x0_p_addr}, gp{mask_addr}, gp{k_reg}\n"

            # Setup base addresses in registers for current batch
            generated_code += f"S_ADDI_INT gp{x_addr}, gp0, {(prompt_batch_size+1)*hidden_size + batch_idx*vlen} \n"  # output base (VLEN elements)
            generated_code += f"S_ADDI_INT gp{x0_addr}, gp0, {batch_idx*vlen} \n"        # x base (VLEN elements, src2)
            # mask is in VECTOR SRAM at gp{mask_addr} (VLEN float elements, already set up earlier)
            
            # Execute S_SELECT_INT: processes all VLEN elements in one instruction
            # x0 = torch.where(mask_index, x0, x)
            generated_code += f"S_SELECT_INT gp{x_addr}, gp{x_addr}, gp{x0_addr}, gp{mask_addr} \n"
            # x[transfer_index] = x0[transfer_index]
            # equal to: x = torch.where(transfer_index, x0, x)
            generated_code += f"S_SELECT_INT gp{x0_addr}, gp{x_addr}, gp{x0_addr}, gp{transfer_idx_addr} \n"
            
            # Increment all address pointers by vlen (move to next row)
            generated_code += f"S_ADDI_INT gp{x0_p_addr}, gp{x0_p_addr}, {vlen} \n"
            generated_code += f"S_ADDI_INT gp{mask_addr}, gp{mask_addr}, {vlen} \n"
            generated_code += f"S_ADDI_INT gp{transfer_idx_addr}, gp{transfer_idx_addr}, {vlen} \n"
            
    return generated_code



def get_transfer_index_long_debug_singleT(
    alive_registers: List[int],  # Can be int or hex string, will be converted to hex
    logits_base_address: int, # input (B,L,V)
    mask_base_address: int,   # input (B,L)
    transfer_idx_base_address: int, # input (B,L)
    temp_base_address: int,   # temp ()
    x0_p_base_address: int,   # x0_p (B,L)
    k_values: List[int],
    vlen: int,
    repeat_times: int,
    batch_size: int,
    prompt_batch_size: int,
    vocal_size_single: int,
    hidden_size: int,  # L dimension (e.g., 64)
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
    temp_addr         = reg_hex(alive_registers[3])
    x0_p_addr         = reg_hex(alive_registers[4])
    k_reg             = reg_hex(alive_registers[5])
    max_idx_addr      = reg_hex(alive_registers[6])
    offset_addr       = reg_hex(alive_registers[7])  # offset register for previous idx in the continus mode of V_RED_MAX_IDX
    x_addr            = reg_hex(alive_registers[8])  # x register (int sram)
    x0_addr           = reg_hex(alive_registers[9])  # x0 register (int sram)
    
    generated_code = "; get_transfer_index for dLLM generation \n"
    generated_code += f"S_ADDI_INT gp{logits_addr}, gp0, {logits_base_address} \n"
    generated_code += f"S_ADDI_INT gp{mask_addr}, gp0, {mask_base_address} \n"
    generated_code += f"S_ADDI_INT gp{transfer_idx_addr}, gp0, {transfer_idx_base_address} \n"
    generated_code += f"S_ADDI_INT gp{temp_addr}, gp0, {temp_base_address} \n"
    generated_code += f"S_ADDI_INT gp{x0_p_addr}, gp0, {x0_p_base_address} \n"
    
    # Loop over batch_size rows
    for batch_idx in range(batch_size):  
        for i in range(vlen):
            # calculate the MAX in the entire V dim
            generated_code += f"S_ADD_FP f1, f0, f0 \n"  # Initialize f1 to 0 (for V_RED_MAX)
            generated_code += f"S_ADD_FP f2, f0, f0 \n"  # Initialize f2 to 0 (for V_RED_MAX_IDX)
            generated_code += f"S_ADD_INT gp{max_idx_addr}, gp0, gp0 \n"  # Initialize idx to 0
            generated_code += f"S_ADD_INT gp{offset_addr},  gp0, gp0 \n"  # Initialize offset to 0
            for j in range(repeat_times):
                hbm_offset  = batch_idx*hidden_size*(repeat_times*vocal_size_single)  + i * (repeat_times*vocal_size_single) + j * vocal_size_single
                vram_offset = logits_base_address
                generated_code += preload_act_asm_scale(
                    vlen=vlen,
                    preload_len=1,
                    batch=1,
                    hidden_size=vocal_size_single,
                    scale=batch_size*hidden_size*vocal_size_single*repeat_times,
                    alive_registers=[1,2,3],  # [a_actual_register, set_stride_register, result_register]
                    act_hbm_offset=hbm_offset,
                    act_vram_offset=vram_offset,
                    activation_offset_reg=0
                )
                
                for k in range(vocal_size_single // vlen):
                    generated_code += f"V_RED_MAX f1, gp{logits_addr},0\n"
                    generated_code += f"V_RED_MAX_IDX gp{max_idx_addr}, gp{logits_addr}, gp{offset_addr}, f2\n"
                    # Update gp{logits_addr} and offset
                    generated_code += f"S_ADDI_INT gp{logits_addr}, gp{logits_addr}, {vlen} \n"
                    generated_code += f"S_ADDI_INT gp{offset_addr}, gp{offset_addr}, {vlen} \n"
                generated_code += f"S_ADDI_INT gp{logits_addr}, gp0, {logits_base_address} \n"
                
            
            # calculate the exp(logits - max_logits) in the entire V dim
            for j in range(repeat_times):
                hbm_offset  = batch_idx*hidden_size*(repeat_times*vocal_size_single)  + i * (repeat_times*vocal_size_single) + j * vocal_size_single
                vram_offset = logits_base_address
                generated_code += preload_act_asm_scale(
                    vlen=vlen,
                    preload_len=1,
                    batch=1,
                    hidden_size=vocal_size_single,
                    scale=batch_size*hidden_size*vocal_size_single*repeat_times,
                    alive_registers=[1,2,3],  # [a_actual_register, set_stride_register, result_register]
                    act_hbm_offset=hbm_offset,
                    act_vram_offset=vram_offset,
                    activation_offset_reg=0
                )
                for k in range(vocal_size_single // vlen):
                    # S' = S - max_logits
                    generated_code += f"V_SUB_VF gp{temp_addr}, gp{logits_addr}, f1, 0\n"
                    # P = exp(S')
                    generated_code += f"V_EXP_V gp{temp_addr}, gp{temp_addr}, 0 \n"
                    # update gp{logits_addr} and gp{temp_addr}
                    generated_code += f"S_ADDI_INT gp{logits_addr}, gp{logits_addr}, {vlen} \n"
                    generated_code += f"S_ADDI_INT gp{temp_addr}, gp{temp_addr}, {vlen} \n"
                generated_code += f"S_ADDI_INT gp{logits_addr}, gp0, {logits_base_address} \n"
                generated_code += f"S_ADDI_INT gp{temp_addr}, gp0, {temp_base_address} \n"
            
            
            # calculate the SUM in the entire V dim, no need to load the logits this time
            for j in range(repeat_times):
                for k in range(vocal_size_single // vlen):
                    # SUM
                    generated_code += f"V_RED_SUM f1, gp{temp_addr}\n"
                    # update gp{temp_addr}
                    generated_code += f"S_ADDI_INT gp{temp_addr}, gp{temp_addr}, {vlen} \n"
                generated_code += f"S_ADDI_INT gp{temp_addr}, gp0, {temp_base_address} \n"
            

            # Compute reciprocal
            generated_code += f"S_RECI_FP f1, f1 \n"
            # Store reciprocal value from f1 to FP_MEM: FP_MEM[fp_reg<gp0>+i] = fp_reg<f1>
            generated_code += f"S_ST_FP f1, gp0, {i} \n"

            # Store the max_idx from gp{max_idx_addr} into INT_MEM, INT_MEM[int_reg<gp0>+ (prompt_batch_size+1)*hidden_size +(batch_idx*vlen + i)] = gp{max_idx_addr}
            generated_code += f"S_ST_INT gp{max_idx_addr}, gp0, {(prompt_batch_size+1)*hidden_size + batch_idx*vlen + i} \n"
        
        # grab these accumulated vlen scalar(stored reciprocal) into SRAM to form an vector again
        # SRAM[gp<x0_p_addr>] = FP_MEM[gp0+0 : gp0+0+vlen]
        generated_code += f"S_MAP_V_FP gp{x0_p_addr}, gp0, 0 \n"
        
        # Load k value for this batch into scalar register
        k_value = k_values[batch_idx] if batch_idx < len(k_values) else k_values[0]
        generated_code += f"S_ADDI_INT gp{k_reg}, gp0, {k_value} \n"
        
        # Execute V_TOPK_MASK instruction
        # V_TOPK_MASK rd, rs1, rs2, k_scalar
        # rd: output mask (vector), rs1: confidence vector, rs2: input mask (vector), k_scalar: k value (scalar)
        generated_code += f"V_TOPK_MASK gp{transfer_idx_addr}, gp{x0_p_addr}, gp{mask_addr}, gp{k_reg}\n"

        # Setup base addresses in registers for current batch
        generated_code += f"S_ADDI_INT gp{x_addr}, gp0, {(prompt_batch_size+1)*hidden_size + batch_idx*vlen} \n"  # output base (VLEN elements)
        generated_code += f"S_ADDI_INT gp{x0_addr}, gp0, {batch_idx*vlen} \n"        # x base (VLEN elements, src2)
        # mask is in VECTOR SRAM at gp{mask_addr} (VLEN float elements, already set up earlier)
        
        # Execute S_SELECT_INT: processes all VLEN elements in one instruction
        # x0 = torch.where(mask_index, x0, x)
        generated_code += f"S_SELECT_INT gp{x_addr}, gp{x_addr}, gp{x0_addr}, gp{mask_addr} \n"
        # x[transfer_index] = x0[transfer_index]
        # equal to: x = torch.where(transfer_index, x0, x)
        generated_code += f"S_SELECT_INT gp{x0_addr}, gp{x_addr}, gp{x0_addr}, gp{transfer_idx_addr} \n"
        
        # Increment all address pointers by vlen (move to next row)
        generated_code += f"S_ADDI_INT gp{x0_p_addr}, gp{x0_p_addr}, {vlen} \n"
        generated_code += f"S_ADDI_INT gp{mask_addr}, gp{mask_addr}, {vlen} \n"
        generated_code += f"S_ADDI_INT gp{transfer_idx_addr}, gp{transfer_idx_addr}, {vlen} \n"
        
    return generated_code