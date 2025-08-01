;<---------------- Set up Environment (QKT stride) ---------------->
; Br and Bc are both MLEN
; rstride[0] = Number of attention heads * Head Dimension * High Precision
; rstride[1] = Number of attention heads * Head Dimension * Low Precision
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
V_RESET_SRAM 0, i1, 0; # i1 + 0 : i1 + 0 + head_dim * MLEN
;<---------------- Fetch Q ---------------->
S_LD_FIX i1, i0, 13; Counter for Tr
S_LD_FIX i2, i0, 6; Q block size
S_MUL_FIX i2, i2, i1; Q block address
HPrefetchV { rd: i0, rs1: i2, rs2: a2, rstride: 0, precision: activation }; Load MLEN * Head Dimension elements of Q
S_ADDI_FIX i1, i1, 1; Increment Tr counter 
S_ST_FIX i1, i0, 13; Store Tr counter
;<--------------------------------  LOOP Tc Iteration 0 -------------------------------->
S_LD_FIX i1, i0, 14; Counter for Tc
S_LD_FIX i2, i0, 5; K block size
S_MUL_FIX i2, i2, i1; K block address
HPrefetchM { rd: i0, rs1: i2, rs2: a2, rstride: 1, precision: kv }; Load MLEN * Head Dimension elements of KT
S_ADDI_FIX i1, i1, 1; Increment Tc counter
S_ST_FIX i1, i0, 14; Store Tc counter


S_ADDI_FIX i7, i0, 0; Buffer Pointer in VSRAM 
S_ADDI_FIX i8, i0, 0; S offset (full buffer load to S (MLEN/BLEN))

;<-------------------------------- LOOP Internal Q (MLEN/BLEN) -------------------------------->
;<--- LOOP Init --->
S_ADDI_FIX i5, i0, 0; Q offset
S_ADDI_FIX i6, i0, 0; KT offset 

;<--- LOOP Init --->

;<---------------------- LOOP Internal KT (MLEN/BLEN - 1) -------------------------------->

;<---------------- LOOP Internal QKT (HEAD_DIM/MLEN - 1) ---------------->
; i1: Address for Q
; i2: Address for KT
; i3: Loop Counter
; i4: MLEN * BLEN * (Weight Precision) or MLEN * BLEN * (K Precision)          : Q block address size or KT block address size

;<--- LOOP Init --->
S_ADD_FIX i1, i0, i5; Q address
S_ADD_FIX i2, i0, i6; KT address
S_ADDI_FIX i3, i0, 0; Loop Counter
;<--- LOOP Init --->

M_TMM 0, i1, i2; (BLEN * MLEN) * (MLEN * BLEN)
S_ADDI_FIX i3, i0, 1; Increment Loop Counter

S_LD_FIX i4, i0, 0; Q block size
S_MUL_FIX i1, i3, i4; Calculate current Q block offset in the hidden dimension
S_ADDI_FIX i1, i5, i1; Update Q offset
S_LD_FIX i4, i0, 1; KT block size
S_MUL_FIX i2, i3, i4; Calculate current KT block offset in the hidden dimension
S_ADDI_FIX i2, i6, i2; Update KT offset

;<---------------- LOOP Internal QKT (HEAD_DIM/MLEN - 1) --------------->
;<---------------- LOOP Internal QKT (HEAD_DIM/MLEN    ) --------------->
M_MM_WO i7, i1, i2; Multiply Q and KT and store to S. No index needed for S. This is an append operation.

;<---------------- LOOP Internal QKT (HEAD_DIM/MLEN    ) --------------->

;<---------------------- LOOP Internal KT (MLEN/BLEN) -------------------------------->
S_LD_FIX i1, i0, 7; Load head dimension * BLEN (next internal block of KT)
S_ADDI_FIX i6, i6, i1; Update KT to the next token
S_LD_FIX i1, i0, i5; Reload Q to multiply with next KT and do nothing to KT address so it continues to increment on itself
;<---------------------- LOOP Internal KT (MLEN/BLEN - 1) -------------------------------->
S_LD_FIX i1, i0, 7; Load head dimension * BLEN (next internal block of Q)
S_ADDI_FIX i5, i5, i1; Update Q to the next token
S_ADDI_FIX i6, i0, 0; Reset KT offset
S_LD_FIX i1, i0, 18; Load MLEN * BLEN, address offset for a full row of S
S_ADDI_FIX i7, i7, i1; Update buffer pointer
;<---------------------- LOOP Internal KT (MLEN/BLEN - 1) -------------------------------->
;<-------------------------------- LOOP Internal Q (MLEN/BLEN) -------------------------------->

