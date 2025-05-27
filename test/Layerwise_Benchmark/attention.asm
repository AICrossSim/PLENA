// <-------------------- FlashAttention ------------------------>
// Assuming the q is stored in shape [1, 1, num_attention_heads, Head_Dim]
// For locality issue, stored the q, k, v in this dimension in HBM
// Assuming the k is stored in shape [1, s_kv, num_key_value_heads, Head_Dim]  
// Assuming the v is stored in shape [1, s_kv, num_key_value_heads,67 Head_Dim]
// Therefore, for the prefetching function, we need to reshape it.

// Assuming single batchsize
// x is the fixed point register

// Parameters
// Head_Dim = 16;
// s_kv = 4;
// MLEN = 4;
// Tc = 1;


// q @ k_j.transpose(1, 2)
S_LUI_FIX       x1, x0, 0;            
S_LUI_FIX       x2, x0, 0; 

// Fetching K and Q of  (MLEN,  MLEN) from HBM to MVM SRAM
H_PREFETCH_M    x1,  x1, x0;    
H_PREFETCH_V    x2,  x2, x1; 
S_LUI_FIX       x3, 1; 
C_SET_M_OFFSET  x3;
    
// s_j = q @ k_j.transpose(1, 2)
M_TMV_O         x3, x1, x2;           

S_ADDI_FIX      x5, x0, 8;

S_ADDI_FIX      x4, x0, 15; 

S_ADDI_FIX      x4, x4, 1;

S_MUL_FIX       x4, x4, x5;

H_PREFETCH_V    x4,  x4, x1; 

V_MUL_VF        x3, x3, x4; 
