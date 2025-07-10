; on-chip address 32-bit
; HBM address 4-bit
; ============================================================
; Preliminary
; ============================================================
; Assume Br is 
; Assume Q (N, d) is stored in HBM[Q] (This case, assuming b=1 and dimension: (b,s,h,d))
; Assume K (N, d) is stored in HBM[K] (This case, assuming b=1 and dimension: (b,s,h,d))
; Assume V (N, d) is stored in HBM[V] (This case, assuming b=1 and dimension: (b,s,h,d))
; Assume O (N, d) is stored in HBM[O] (This case, assuming b=1 and dimension: (b,s,h,d))
; Assume m_curr ([1:Br+1]) is stored in FP_SRAM[m_curr:m_curr+Br]
; Assume m_last ([1:Br+1]) is stored in FP_SRAM[m_last:m_last+Br]
; Assume l ([1:Br+1]) is stored in FP_SRAM[l:l+Br]
; Assume o_scale ([1:Br+1]) is stored in FP_SRAM[o:o+Br]

; Assume Q value is directly stored in ADR[Q]
; Assume K value is directly stored in ADR[K]
; Assume V value is directly stored in ADR[V]
; Assume O value is directly stored in ADR[O]

; Available Fixed-Point Regfile: FIX[1], ..., FIX[8]
; Available Floating-Point Regfile: FP[1], ..., FP[8]
; MLEN: 128
; VLEN: 128
; BLEN: 8
; DataType : MXFP ELEMENT 8 bits and SCALE 16 bits
; Matrix SRAM: 2 * MLEN * MLEN
; Vector SRAM: 2 * Hidden_size
; VEC_LOOP_SIZE: h / V_LEN
; HALF_VEC_LOOP_SIZE: h / V_LEN / 2
; store the LOOP 2 counter x8 in FIX_SRAM[5]
; ============================================================


;<---------------- Set up Environment ---------------->
; Set Stride Register
S_LD_FIX x1, x0, 0;
C_SET_STRIDE_REG x1, 0, 0;
; Set Scale Offset
S_LD_FIX x1, x0, 1;
C_SET_SCALE_REG x1, 0, 0;

;<---------------- LOOP Tr Iteration 0 ---------------->
S_ADDI_FIX x1, x0, 0; 
;<---------------- LOOP Tc Iteration 0 ---------------->
S_ADDI_FIX x2, x0, 0;
;<---------------- LOOP Internal QKT (MLEN/BLEN) Iteration 0 ---------------->
S_ADDI_FIX x3, x0, 0; 

; Assuming prefetching a head_dim * MLEN data to MATRIX and VECTOR SRAM using the following two instructions.
H_PREFETCH_V_S x0, x0, x2; 
H_PREFETCH_M_S x0, x0, x3;

;<--------LOOP Internal QKT (head_dim // MLEN) Iteration 0 -------->      
S_LD_FIX x4, x0, MLEN;              set FIX[4] to x3 * MLEN, use it to store start offset for different Q blocks arocss embedding dimension
S_ADDI_FIX x5, x0, 0;               internal counter, looping for (head_dim // MLEN) times
S_MUL_FIX x6, x5, x4;               set FIX[6] to 1, use as pointer to the beginning M_SRAM, V_SRAM location

M_TMM_IC 0, x6, x6;

;<-------LOOP Internal QKT (head_dim // MLEN) Iteration END ------->      
S_LD_FIX x4, x0, MLEN;
S_ADDI_FIX x5, x0, 0;
S_MUL_FIX x6, x5, x4;
M_TMM_PS x3, x6, x6;

;<---------------- LOOP Internal QKT (MLEN/BLEN) Iteration END ---------------->
S_ADDI_FIX x3, x3, 1; 
S_LD_FIX x4, x0, MLEN;

S_MUL_FIX x4, x4, x3;

H_PREFETCH_V_S x0, x4, x2; 
H_PREFETCH_M_S x0, x4, x3;

;<--------LOOP Internal QKT (head_dim // MLEN) Iteration 0 -------->      
S_LD_FIX x4, x0, MLEN;
S_ADDI_FIX x5, x0, 0;
S_MUL_FIX x6, x5, x4;
M_TMM_IC 0, x6, x6;

;<-------LOOP Internal QKT (head_dim // MLEN) Iteration end ------->      
S_LD_FIX x4, x0, MLEN;
S_ADDI_FIX x5, x0, 0;
S_MUL_FIX x6, x5, x4;
M_TMM_PS x3, x6, x6;
M_MM_WO x0, 0, 0; Write to the 0 addr of the VECTOR SRAM, replacing original K Cache.
