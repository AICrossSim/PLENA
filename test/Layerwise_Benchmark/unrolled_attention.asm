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


;<---------------- Set up Environment (QKT stride) ---------------->
; Set Stride Register
S_LD_FIX i1, i0, 11;
C_SET_STRIDE_REG i1, 0, 0;
S_LD_FIX i1, i0, 12;
C_SET_STRIDE_REG i1, 0, 1;

;<------------------------------------------------ LOOP Tr Iteration 0 ------------------------------------------------>
;<---------------- Set up Environment (m) ---------------->
S_LD_FP f1, i0, 0;
S_ADDI_FIX i1, i0, 1;
; Loop MLEN Times, set a region of m to be negative infinity (negative max)
;<--- LOOP MLEN Times --->
S_ST_FP f1, i1, 0;
S_ADDI_FIX i1, i1, 1;
;<--- LOOP MLEN Times --->
;<---------------- Set up Environment (O) ---------------->
S_LD_FIX i1, i0, 15;
V_RESET_SRAM 0, i1, 0;
;<---------------- Fetch Q ---------------->
S_LD_FIX i1, i0, 13;
S_LD_FIX i2, i0, 6;
S_MUL_FIX i2, i2, i1;
H_PREFETCH_V_H_S i0, i2, a2; 
S_ADDI_FIX i1, i1, 1;
S_ST_FIX i1, i0, 13;
;<--------------------------------  LOOP Tc Iteration 0 -------------------------------->
S_LD_FIX i1, i0, 14;
S_LD_FIX i2, i0, 5;
S_MUL_FIX i2, i2, i1;
H_PREFETCH_M_L_S i0, i2, a2; 
S_ADDI_FIX i1, i1, 1;
S_ST_FIX i1, i0, 14;


;<-------------------------------- LOOP Internal Q (MLEN/BLEN) -------------------------------->
;<--- LOOP Init --->
S_ADDI_FIX i5, i0, 0; Q offset
S_ADDI_FIX i8, i0, 0; S offset (full buffer load to S (MLEN/BLEN))
S_ADDI_FIX i6, i0, 0; KT offset
S_ADDI_FIX i7, i0, 0; Buffer Pointer

;<--- LOOP Init --->

;<---------------------- LOOP Internal KT (MLEN/BLEN) -------------------------------->

;<---------------- LOOP Internal QKT (HEAD_DIM/MLEN - 1) ---------------->
; i1: Address for Q
; i2: Address for K
; i3: Loop Counter
; i4: MLEN * BLEN * (Weight Precision) or MLEN * BLEN * (K Precision)          : Q block address size or KT block address size

;<--- LOOP Init --->
S_ADD_FIX i1, i0, i5;
S_ADD_FIX i2, i0, i6;
S_ADDI_FIX i3, i0, 0;
;<--- LOOP Init --->

M_TMM_IC 0, i1, i2;
S_ADDI_FIX i3, i0, 1;

S_LD_FIX i4, i0, 0;
S_MUL_FIX i1, i3, i4;
S_LD_FIX i4, i0, 1;
S_MUL_FIX i2, i3, i4;

;<---------------- LOOP Internal QKT (HEAD_DIM/MLEN - 1) --------------->
;<---------------- LOOP Internal QKT (HEAD_DIM/MLEN    ) --------------->
M_TMM_PS i7, i1, i2;
S_ADDI_FIX i7, i7, 1;
;<---------------- LOOP Internal QKT (HEAD_DIM/MLEN    ) --------------->
S_LD_FIX i4, i0, 4; K_SIZE_FOR_ONE_FULL_BUFFER_ITR offset
S_ADD_FIX i6, i6, i4; Next KT block address

;<---------------------- LOOP Internal KT (MLEN/BLEN) -------------------------------->
; Buffer is full
S_LD_FIX i1, i0, 2;
S_ADD_FIX i1, i8, i1; S base address

M_MM_WO i1, 0, 0;

S_LD_FIX i1, i0, 3;
S_ADD_FIX i8, i8, i1; Update S offset
S_ADD_FIX i5, i5, i1; Update Q offset
;<-------------------------------- LOOP Internal Q (MLEN/BLEN) -------------------------------->



; Jeffrey: I'm here!
;<----------------LOOP Internal QKT (MLEN/BLEN) Iteration END---------------->
S_ADDI_FIX x3, x3, 1; 
S_LD_FIX x4, x0, 2;
S_MUL_FIX x4, x4, x3;
H_PREFETCH_V_H_S x0, x4, x2; 
H_PREFETCH_M_S x0, x4, x3;

;<--------LOOP Internal QKT (head_dim // MLEN) Iteration 0 -------->      
S_LD_FIX x4, x0, 2;
; Load MLEN
S_ADDI_FIX x5, x0, 0;
S_MUL_FIX x6, x5, x4;
M_TMM_IC 0, x6, x6;

;<-------LOOP Internal QKT (head_dim // MLEN) Iteration end ------->      
S_LD_FIX x4, x0, 2;
S_ADDI_FIX x5, x0, 0;
S_MUL_FIX x6, x5, x4;
M_TMM_PS x3, x6, x6;
M_MM_WO x0, 0, 0; 

;<----------------LOOP Internal QKT (MLEN/BLEN) Iteration END---------------->

;<<<< -------Complete QKT operation------- >>>>
S_ADDI_FIX x4, x0, 0;
S_LD_FIX x5, x0, 2;
; Load MLEN
S_LD_FIX x1, x0, 3;
; Load 2 * MLEN
S_ADDI_FIX x6, x0, 0;
; Counter for m_old
S_ADDI_FIX x7, x5, 0;
; Counter for m_res

;<------- Online Softmax Loop BR ------>
; fp (x1) stores m_curr
; fp (x2) stores (exp(m_last - m_curr)) ^ -1
; fp (x3) stores sum(vect)
; fp (x4) stores l
S_LD_FP    x1, x6, 0;
S_MV_FP    x2, x1, 0; 
V_RED_MAX  x1, x4, 0;
S_SUB_FP   x2, x2, x1;
S_EXP_FP   x2, x2, 0;
S_ST_FP    x1, x6, 0;
V_SUB_VF   x4, x4, x1;
S_ADD_FIX  x4, x4, x5;
S_ADD_FIX x6, x6, 1;
S_ADD_FIX x7, x7, 1;
V_EXP_V   x4, x4, 0;
S_LD_FP    x4, x1, 0;
V_RED_SUM  x3, x4, 0;
S_MUL_FP   x4, x4, x2;
S_ADD_FP   x4, x3, x4;
S_RECI_FP  x2, x2, 0;
S_ST_FP    x2, x7, 1;
S_ST_FP    x4, x1, 0;
; Store L

;<------- Online Softmax Loop MLEN END ------>
;<<<< -------Complete Online Softmax------- >>>>

; Multiplying with V
; compute sequence address of V      
S_ADDI_FIX  x2, x0, 0;                      x2 = 0
S_ADDI_FIX  x3, x0, 0;                      x3 = 0 Address pointer to P in VECTOR SRAM
S_ADDI_FIX  x4, x0, 0;                      x4 = 0 Accumulate pointer in matrix unit.
S_ADDI_FIX  x6, x0, 0;                      x6 = 0 Address pointer to V in MATRIX SRAM
S_LD_FIX    x5, x0, 11;                     x5 = BLEN * MLEN
S_LD_FIX    x1, x0, 10;                     x1 = MLEN * MLEN; PV result offset in Vector SRAM, address pointer to the result.
H_PREFETCH_M_S x0, x7, x4;
;<------- PV (MLEN, MLEN) @ (MLEN, head_dim) Outer LOOP  Head_dim / BLEN ------>

;<------- PV (MLEN, MLEN) @ (MLEN, BLEN) Inner LOOP  MLEN / BLEN ------>
M_MM_PS     x4, x6, x3;
S_ADDI_FIX  x4, x4, 1;
S_ADD_FIX   x3, x3, x5;

;<------- PV (MLEN, MLEN) @ (MLEN, BLEN) End of Inner LOOP  MLEN / BLEN ------>
M_MM_WO         x1, 0, 0;
S_ADD_FIX       x1, x1, x5;
S_ADDI_FIX      x3, x0, 0;             ; Reset x3 to 0, use it as an incremental pointer across MLEN/BLEN;
S_ADDI_FIX      x4, x0, 0;             ; Reset x4 to 0, use it as an accumulated pointer across MLEN/BLEN;
S_ADD_FIX       x6, x6, x5;

;<------- PV (MLEN, MLEN) @ (MLEN, head_dim) End of Outer LOOP  Head_dim / BLEN ------>

;<<<< -------Complete PV------- >>>>
S_LD_FIX        x3, x0, 2; 
S_MAP_V_FP      x0, x3, 0;        Store at 0 to replace P.
S_LD_FIX        x1, x0, 12;       x1 = MLEN * MLEN + Head_DIM * MLEN; Offset for O.      
S_LD_FIX        x2, x0, 10;       x1 = MLEN * MLEN; PV result offset in Vector SRAM, address pointer to the result.

;<------- O = diag() + PV LOOP over hidden------>
V_MUL_VV        x1, x1, x0;        x4 = diag-1 * O
V_ADD_VV        x1, x1, x2;        x4 = diag-1 * O + PV

S_ADD_FIX       x1, x1, x3;
S_ADD_FIX       x2, x2, x3;       

;<------- O = diag() + PV LOOP over hidden END ------>
;<--------------------------------  End of LOOP Tc Iteration 0 -------------------------------->

S_LD_FIX        x1, x0, 3;
;<----------- Loop MLEN, l^(-1)------------->
S_LD_FP         x1, x1, 0;          Load l_old to x1
S_RECI_FP       x1, x1, 0;
S_ST_FP         x1, x1, 0;
S_ADDI_FIX      x1, x1, 1;
;<----------- Loop MLEN, l^(-1) END---------->

S_LD_FIX        x1, x0, 3;          x1 = 2*MLEN, l_old 
S_MAP_V_FP      x0, x1, 0;          Store at 0 to replace m.
;<----------- Loop Hidden, diag O ------------->
S_LD_FIX        x1, x0, 2;          
S_LD_FIX        x2, x0, 12;          x1 = MLEN * MLEN + Head_DIM * MLEN; Offset for O.
V_MUL_VV        x2, x2, x0;          x4 = diag-1 * O
S_ADD_FIX       x2, x2, x1;          x4 = diag-
;<----------- STORE to HBM ---------->


