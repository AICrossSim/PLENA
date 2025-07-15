// <-------------------- FlashAttention ------------------------>
// Assuming the q is in shape [1, 1, num_attention_heads, Head_Dim]
// For locality issue, stored the q, k, v in this dimension in HBM
// Assuming the k is in shape [1, num_key_value_heads, s_kv, Head_Dim]  
// Assuming the v is in shape [1, num_key_value_heads, s_kv, Head_Dim]
// Assuming single batchsize
// x is the fixed point register


S_LUI_FIX   x1, Head_Dim;
S_LUI_FIX   x2, s_kv//MLEN;                 Tc Filled by Compiler
S_LUI_FIX   x3, MLEN;                       MLEN
S_LUI_FIX   x4, s_kv;                       Sequence Length
S_MV_FIX    x5, x0;                         Index of q_head.

LOOP_ATTENTION_Q_HEADS:
    S_DIV_FIX   x5, ; (index of in q head // num_head_groups) index of kv_head.
    (S_LUI_FIX  x5, Filled by Compiler;)

    S_MUL_FIX   x6, x4, x1;                     Head_Dim * s_kv     
    S_MUL_FIX   x6, x6, x5;                     memory offset to the ith head content in K, V in HBM
    S_LUI_FIX   x8, (MLEN * MLEN);

    LOOP_ATTENTION_PER_HEAD:
        // q @ k_j.transpose(1, 2)

        S_LUI_FIX x9, (Head_Dim // MLEN);       // Loop Counter
        S_LUI_FIX x12, ACC_OFFSET;              // Tiled Matrix-Vector Accumulator
        S_MV_FIX x16, x0;                       // Storing the max value of s_j in x16
        S_MV_FIX x20, x0;                       // Storing online row sum
        
        S_LUI_FIX x21, OUTPUT_STORE_REGION;     // Storing output

        LOOP_Bc:
            S_MUL_FIX       x10, x9, x8;                // Storing the address for matrix 
            S_MUL_FIX       x11, x9, x1;                // Storing the address for multiplicand vector
            
            // Fetching K and Q of  (MLEN,  MLEN) from HBM () to MVM SRAM

            S_ADDI_FIX      x13,  x13, 0x1;            // Prefetched address of K and Q

            H_PREFETCH_M_C    x13,  x10, csr_adr[0];    
            H_PREFETCH_V_H_C    x13,  x11, csr_adr[1]; 
            C_SET_MV_OFFSET x13;
            
            // s_j = q @ k_j.transpose(1, 2)
            M_TMV_IC           x12, x13, x13;              // Matrix-Vector Multiplication

            S_ADDI_FIX      x9, x9, 0xfff;              // - 1
            blt             x0, x9, LOOP_Bc;            // Unroll the loop in main processor, not included in this coprocess.
        
        // x14 stores the qk_scale in fp, where s_j = q @ k_j.transpose(1, 2) * qk_scale, dot product, s_j in dimension (1, MLEN)
        V_MUL_VF            x12, x12, x14;              // Multiply the result of Q @ K^T with qk_scale     
        H_STORE_VECTOR      x12, x0, csr_adr[8];        // Store the result of Q @ K^T in SRAM

        // rowmax_s_j = s_j.max().cpu().item() & m_new = max(m, rowmax_s_j)  # update global row max, store the previous m in x16

        V_RED_MAX           x17, x12, x16;

        // s_j_shifted = s_j - m_new
        V_SUB_VF            x12, x12, x16;              

        // p = torch.exp(s_j_shifted)
        V_EXP_V             x12, x12, x0;                   
 
        // m_res = m - m_new
        S_SUB_FP         x10, x16, x17;              

        // m = m_new
        S_MV_FIX    x16, x17;                       

        // l_scale = math.exp(m_res)
        S_EXP_FP         x10, x10, x0;              

        // p_row_sum = p.sum().cpu().item()
        V_RED_SUM           x11, x12, x0;              

        // l_scale * l
        S_LUI_FIX       x13, l_scale;
        S_MUL_FP        x20, x20, x13;             

        // l = l_scale * l + p_row_sum
        S_ADD_FP        x20, x20, x11;           

        // o_scale = math.exp(m_res)
        S_EXP_FP         x10, x10, x0;


        LOOP_Bc:
            // o_scale * o
            S_ADD_FP        x22, x21, x3;               // Increment addr by MLEN, storing output vector 
            V_MUL_VF        x22, x21, x10;
            
            S_MUL_FIX       x10, x9, x8;                // Storing the address for matrix 
            S_MUL_FIX       x11, x9, x1;                // Storing the address for multiplicand vector
            // p shape(MLEN) @ v_j (MLEN, Head_Dim)
            // Fetching V of  (MLEN,  MLEN) from HBM () to MVM SRAM
            S_ADDI_FIX      x13,  x13, 0x1;            // Prefetched address of V
            H_PREFETCH_M_C    x13,  x10, csr_adr[0];    

            M_MV_IC            x12, x13, x12;              // Matrix-Vector Multiplication

            V_ADD_VV        x22, x22, x12;              // o = o + p @ v_j

            S_ADDI_FIX      x9, x9, 0xfff;              // - 1
            blt             x0, x9, LOOP_Bc;            // Unroll the loop in main processor, not included in this coprocess.
