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
S_LD_FIX x1, x0, 1;
C_SET_SCALE_REG x1, 0, 0;

;<------------------------------------------------ LOOP Tr Iteration 0 ------------------------------------------------>
S_ADDI_FIX x1, x0, 0; 
;<--------------------------------  LOOP Tc Iteration 0 -------------------------------->
S_ADDI_FIX x2, x0, 0;
;<---------------- LOOP Internal QKT (MLEN/BLEN) Iteration 0 ---------------->
S_ADDI_FIX x3, x0, 0; 
; Assuming prefetching a head_dim * MLEN data to MATRIX and VECTOR SRAM using the following two instructions.
H_PREFETCH_V_S x0, x0, x2; 
H_PREFETCH_M_S x0, x0, x3;

;<--------LOOP Internal QKT (head_dim // MLEN) Iteration 0 -------->      
S_LD_FIX x4, x0, 2;
S_ADDI_FIX x5, x0, 0;
S_MUL_FIX x6, x5, x4;
M_TMM_IC 0, x6, x6;

;<-------LOOP Internal QKT (head_dim // MLEN) Iteration END ------->      
S_LD_FIX x4, x0, 2;
S_ADDI_FIX x5, x0, 0;
S_MUL_FIX x6, x5, x4;
M_TMM_PS x3, x6, x6;

;<----------------LOOP Internal QKT (MLEN/BLEN) Iteration END---------------->
S_ADDI_FIX x3, x3, 1; 
S_LD_FIX x4, x0, 2;
S_MUL_FIX x4, x4, x3;
H_PREFETCH_V_S x0, x4, x2; 
H_PREFETCH_M_S x0, x4, x3;

;<--------LOOP Internal QKT (head_dim // MLEN) Iteration 0 -------->      
S_LD_FIX x4, x0, 2;
S_ADDI_FIX x5, x0, 0;
S_MUL_FIX x6, x5, x4;
M_TMM_IC 0, x6, x6;

;<-------LOOP Internal QKT (head_dim // MLEN) Iteration end ------->      
S_LD_FIX x4, x0, 2;
S_ADDI_FIX x5, x0, 0;
S_MUL_FIX x6, x5, x4;
M_TMM_PS x3, x6, x6;
M_MM_WO x0, 0, 0; 

;<<<< -------Complete QKT operation------- >>>>
S_ADDI_FIX x4, x0, 0;
S_LD_FIX x7, x0, 2;
S_LD_FIX x5, x0, 3;

;<-------Reduction LOOP MLEN times rowmax(S) ------>
V_RED_MAX x0, x5, x7;
S_ADD_FIX  x4, x0, x5;
S_ADD_FIX  x7, x0, x5;

;<-------Reduction LOOP END ------>
V_RED_MAX x0, x5, x7;
S_ST_FP   x0, x7, x4; 
S_ADD_FIX  x4, x0, x5;
S_ADD_FIX  x7, x0, x5;

; Compute online softmax
S_ADDI_FIX x7, x0, 0;
S_ADDI_FIX x3, x0, 1;
S_ADDI_FIX x4, x0, 1;
S_ADDI_FIX x5, x4, 1;
S_ADDI_FIX x6, x5, 1;
S_ADDI_FIX x8, x6, 1;

;<------- LOOP Br ------>  
S_MAX_FP x0, x0, x4;       
S_SUB_FP x5, x4, x5;        
V_SUB_VF x4, x3, x3;           
V_EXP_V  0, x3, x3;         
V_RED_SUM x0, x3, x6;
S_EXP_FP 0, x5, x5;      
S_LD_FP l, x7, x8;    
S_MUL_FP x8, x5, x8;        
S_ADD_FP x8, x6, x8; 
S_ST_FP m_last, x7, x4; 
S_ST_FP l, x7, x8;  
S_ST_FP o_scale, x7, x5;   
S_ADDI_FIX x3, x3, Bc;              
S_ADDI_FIX x7, x7, 1;     

;<------- LOOP Br END ------>
