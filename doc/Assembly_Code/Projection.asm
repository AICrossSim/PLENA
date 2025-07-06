// <-------------------- Projection ------------------------>
// ## 1. Q Projection:                
S_LUI_FIX x5, ((hidden_size * hiddensize) / (MLEN * MLEN));   counter for the MVM loop               
S_LUI_FIX x6, hidden_size;
S_MV_FIX x8, x0;                      Current tile addr for embedded vector in SSRAM
S_MV_FIX x9, x0;                      Current tile addr for MVM results in accumulator
S_MV_FIX x11, x0;                   size of the tile, address increment.

// MVM
LOOP_MLEN_MATRIX:
    beq x9, x6, RESET_VECTOR_ADDR;          // Controlled by the main processor, to unroll the loop.
    j   WITHOUT_RESET_VECTOR_ADDR;
    
    RESET_VECTOR_ADDR:
        S_MV_FIX x8, x0;                          Current tile addr for embedded vector in SSRAM
        S_MV_FIX x9, x0;                          Current tile addr for MVM results in accumulator
        j   END_VECTOR_ADDR;
    
    WITHOUT_RESET_VECTOR_ADDR:
        S_ADDI_FIX x8, x8, MLEN;             Current tile addr for embedded vector in SSRAM
        S_ADDI_FIX x9, x9, MLEN;             Current tile addr for MVM results in accumulator

    END_VECTOR_ADDR:
        S_ADDI_FIX      x13,  x13, 0x1;            // Prefetched address of K and Q

        H_PREFETCH_M_C  x13, x11, csr_adr[0];         Fetch the weight for ith hidden layer Q from HBM to MVM SRAM
        H_PREFETCH_V_C  x13, x8,  csr_adr[8];         Fetch the embedded vector from HBM to MVM SRAM
        C_SET_MV_OFFSET x13;                        Set the offset addr for the MVM operation

        M_MV_IC x9, x13, x13;  

    S_ADDI_FIX      x11, x11, MLEN * MLEN;            Storing the address for the next tile in MVM SRAM
    S_ADDI_FIX      x8,  x8,  MLEN;       Storing the address for the next tile in SSRAM

    S_ADDI_FIX x5, x5, 0xfff;                              Counter for MVM
    blt x0, x5, LOOP_MLEN_MATRIX;

// To facilitate the flashattn, store, k, v in this shape (  [1, num_key_value_heads, s_kv, Head_Dim]  )
LOOP_HIDDEN_STORAGE:
    // TODO
    H_STORE_HBM x0, x6, csr_adr[0];            Store the MVM results in accumulator back to HBM.



// RoPE Assuming qnew with shape (s_q, heads, Head_Dim), x3 to store the result after RoPE
S_LUI_FIX x1, (Head_Dim/MLEN);                          Counter for loading RoPE weights from HBM to MVM SRAM
S_LUI_FIX x2, NUM_Tiles_Per_Head_Dim;
S_MV_FIX x4, x0;                          Storing the address for RoPE Sin weights in SSRAM;
S_LUI_FIX x5, Head_Dim;                          Storing the address for RoPE Cos weights in SSRAM;

// Loading RoPE weights from HBM to MVM SRAM
LOOP_TILE_VECTOR_IN_HEAD:
    H_STORE_VECTOR x4, csr_addr[6];            Fetch the RoPE weights from HBM to MVM SRAM. (Head_Dim * 2, [cos, sin, else])
    H_STORE_VECTOR x5, csr_addr[6];            Fetch the RoPE weights from HBM to MVM SRAM. (Head_Dim * 2, [cos, sin, else])
    S_ADDI_FIX x4, x4, MLEN;             Storing the address for the next tile in MVM SRAM
    S_ADDI_FIX x1, x1, 0xfff;                  Counter for RoPE
    blt x0, x1, LOOP_TILE_VECTOR_IN_HEAD;

S_ADDI_FIX x11, x4, 3 * Head_Dim;           Storing the address for q_projected and q_roped in SSRAM;
S_ADDI_FIX x10, x4, 3 * Head_Dim;           Storing the address for rotated_q;

S_MV_FIX x12, x0;                          Storing the offset address for q_projected in HBM;
S_MV_FIX x13, x0;                          Storing the offset address for q_roped in HBM;

LOOP_NUM_HEAD:
    // Apply RoPE to each head
    S_MV_FIX x6, x4;                  Current tile addr for cos RoPE weights in SSRAM 
    S_ADDI_FIX x8, x4, Head_Dim;      
    S_MV_FIX x8, x4;                  Current tile addr for sin RoPE weights in SSRAM
    S_LUI_FIX x7, (Head_Dim/MLEN);    Counter for RoPE 

    // Prepare the rotated_q
    //if MLEN == Head_Dim: vector masking is introduced, or vslidedown.vx,
    //Storing rotated_q (1, num_attention_heads * Head_Dim) in x10
    // Depending on the MLEN, estimated to take 3-5 instructions.
    // Storing to csr_adr[9] in HBM
    
    LOOP_TILE_VECTOR_IN_HEAD:
        // assuming Head_Dim | MLEN
        // cos[i : i + MLEN] * q[i : i + MLEN]
        H_PREFETCH_V_C x1, x12, csr_adr[8]; q_projected
        H_PREFETCH_V_C x2, x12, csr_adr[8]; cos
        V_MUL_VV x3, x1, x2;
        
        // sin[i : i + MLEN] * rotated_q[i : i + MLEN]
        H_PREFETCH_V_C x10, x13, csr_adr[9]; q_roped
        H_PREFETCH_V_C x1, x12, csr_adr[8]; rotated_q
        H_PREFETCH_V_C x2, x12, csr_adr[8]; sin
        V_MUL_VV x4, x1, x2;
        V_ADD_VV x1, x3, x4;

        H_STORE_VECTOR x12, v3, csr_adr[8];

        S_ADDI_FIX x6, x6, MLEN;
        S_ADDI_FIX x8, x8, MLEN;
        S_ADDI_FIX x12, x12, MLEN;
        S_ADDI_FIX x13, x13, MLEN;
        //
        S_ADDI_FIX x7, x7, 0xfff;
        blt x0, x7, LOOP_MLEN_VECTOR_IN_HEAD;

