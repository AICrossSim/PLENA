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
; ============================================================


;<---------------- Set up Environment ---------------->
; Set Stride Register
S_LD_FIX x7, x0, 0;
C_SET_STRIDE_REG x7;
; Set Address Register




S_ADDI_FIX x1, x0, 0;
; LOOP N / Br
S_ADDI_FIX x2, x0, 0;
; LOOP N / Bc
S_ADDI_FIX x8, x0, 0;
; LOOP across buffer location             
S_ADDI_FIX x3, x0, 0;               set FIX[3] to 0, use it as an incremental pointer (loop index) across d/MLEN
; LOOP across d/MLEN
S_ADDI_FIX x4, x3, MLEN;            set FIX[4] to x3 * MLEN, use it to store start offset for different Q blocks arocss embedding dimension
S_ADDI_FIX x5, x3, MLEN;            set FIX[5] to x3 * MLEN, use it to store start offset for different K blocks arocss embedding dimension

S_ADDI_FIX x6, x0, 1;               set FIX[6] to 1, use as pointer to the beginning M_SRAM, V_SRAM location

; compute address of Q/K blocks
S_ADDI_FIX x7, x0, Br * d * h;          Br * d * h
S_MUL_FIX  x7, x1, x7;                  x7 = r * (Br * d * h)
S_ADDI_FIX x4, x4, x7;                  x4 = x4 + x7

S_ADDI_FIX x7, x0, Bc * d * h;          Bc * d * h
S_MUL_FIX  x7, x2, x7;                  x7 = c * (Bc * d * h)
S_ADDI_FIX x5, x5, x7;                  x4 = x4 + x7

; if x3 != d/MLEN - 1: Not the last loop
H_PREFETCH_V_S x6, x4, ADR[Q]
H_PREFETCH_M_S x6, x5, ADR[K]
M_MM_IC 0, x6, x6 
S_ADDI_FIX x3, x3, 1;
; if x3 == d/MLEN - 1: Not the last loop
M_MM_PS x6, x6, x8
S_ADDI_FIX x8, x0, 1;