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


