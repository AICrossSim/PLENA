;<---------------- Set up Environment (QKT stride) ---------------->
; Br and Bc are both MLEN
; rstride[0] = Number of attention heads * Head Dimension * High Precision
; rstride[1] = Number of attention heads * Head Dimension * Low Precision
;<------------------------------------------------ LOOP Tr Iteration 0 ------------------------------------------------>
;<---------------- Set up Environment (m) ---------------->
S_LD_FP f1, gp0, 0;
S_ADDI_FIX gp1, gp0, 1;
; Loop MLEN Times, set a region of m to be negative infinity (negative max)
;<--- LOOP MLEN Times --->
S_ST_FP f1, gp1, 0;
S_ADDI_FIX gp1, gp1, 1;
;<--- LOOP MLEN Times --->
;<---------------- Set up Environment (O) ---------------->
S_LD_FIX gp1, gp0, 15;
V_RESET_SRAM 0, gp1, 0; # gp1 + 0 : gp1 + 0 + head_dim * MLEN
;<---------------- Fetch Q ---------------->
S_LD_FIX gp1, gp0, 13; Counter for Tr
; S_LD_FIX x2, gp0, 6; Q block size
S_ADDI_FIX gp2, gp0, 0; Q block offset
S_MUL_FIX gp2, gp2, gp1; Q block address
H_PREFETCH_V { rd: gp0, rs1: gp2, rs2: a2, rstride: 0, precision: activation }; Load MLEN * Head Dimension elements of Q
S_ADDI_FIX gp1, gp1, 1; Increment Tr counter 
S_ST_FIX gp1, gp0, 13; Store Tr counter
;<--------------------------------  LOOP Tc Iteration 0 -------------------------------->
S_LD_FIX gp1, gp0, 14; Counter for Tc
; S_LD_FIX gp2, gp0, 5; K block size
S_ADDI_FIX gp2, gp0, 0; K block offset
S_MUL_FIX gp2, gp2, gp1; K block address
H_PREFETCH_M { rd: gp0, rs1: gp2, rs2: a2, rstride: 1, precision: kv }; Load MLEN * Head Dimension elements of KT
S_ADDI_FIX gp1, gp1, 1; Increment Tc counter
S_ST_FIX gp1, gp0, 14; Store Tc counter


S_LD_FIX gp7, gp0, 2; Load S initial address in VSRAM (HEAD_DIM, MLEN)

;<-------------------------------- LOOP Internal Q (MLEN/BLEN) -------------------------------->
;<--- LOOP Init --->
S_ADDI_FIX gp5, gp0, 0; Q offset
S_ADDI_FIX gp6, gp0, 0; KT offset 

;<--- LOOP Init --->

;<---------------------- LOOP Internal KT (MLEN/BLEN - 1) -------------------------------->

;<---------------- LOOP Internal QKT (HEAD_DIM/MLEN - 1) ---------------->
; gp1: Address for Q
; gp2: Address for KT
; gp3: Loop Counter
; gp4: MLEN * BLEN * (Weight Precision) or MLEN * BLEN * (K Precision)          : Q block address size or KT block address size

;<--- LOOP Init --->
S_ADD_FIX gp1, gp0, gp5; Q address
S_ADD_FIX gp2, gp0, gp6; KT address
S_ADDI_FIX gp3, gp0, 0; Loop Counter
;<--- LOOP Init --->

M_TMM 0, gp1, gp2; (BLEN * MLEN) * (MLEN * BLEN)
S_ADDI_FIX gp3, gp0, 1; Increment Loop Counter

S_LD_FIX gp4, gp0, 0; Q block size
S_MUL_FIX gp1, gp3, gp4; Calculate current Q block offset in the hidden dimension
S_ADDI_FIX gp1, gp5, gp1; Update Q offset
S_LD_FIX gp4, gp0, 1; KT block size
S_MUL_FIX gp2, gp3, gp4; Calculate current KT block offset in the hidden dimension
S_ADDI_FIX gp2, gp6, gp2; Update KT offset

;<---------------- LOOP Internal QKT (HEAD_DIM/MLEN - 1) --------------->
;<---------------- LOOP Internal QKT (HEAD_DIM/MLEN    ) --------------->
M_MM_WO gp7, gp1, gp2; Multiply Q and KT and store to S. No index needed for S. This is an append operation.

;<---------------- LOOP Internal QKT (HEAD_DIM/MLEN    ) --------------->

;<---------------------- LOOP Internal KT (MLEN/BLEN) -------------------------------->
S_LD_FIX gp1, gp0, 7; Load head dimension * BLEN (next internal block of KT)
S_ADDI_FIX gp6, gp6, gp1; Update KT to the next token
S_LD_FIX gp1, gp0, gp5; Reload Q to multiply with next KT and do nothing to KT address so it continues to increment on itself
;<---------------------- LOOP Internal KT (MLEN/BLEN - 1) -------------------------------->
S_LD_FIX gp1, gp0, 7; Load head dimension * BLEN (next internal block of Q)
S_ADDI_FIX gp5, gp5, gp1; Update Q to the next token
S_ADDI_FIX gp6, gp0, 0; Reset KT offset
; S_LD_FIX gp1, gp0, 18; Load MLEN * BLEN, address offset for a full row of S
; S_ADDI_FIX gp7, gp7, gp1; Update buffer pointer
;<---------------------- LOOP Internal KT (MLEN/BLEN - 1) -------------------------------->
;<-------------------------------- LOOP Internal Q (MLEN/BLEN) -------------------------------->
;<<<< -------Complete QKT operation------- >>>>
S_ADDI_FIX gp4, gp0, 0;
S_LD_FIX gp5, gp0, 2;
; Load MLEN
S_ADDI_FIX gp6, gp5, 0;
; Counter for m_old
S_ADDI_FIX gp7, gp6, gp5;
; Counter for m_res
S_ADDI_FIX gp1, gp7, gp5;
; Counter for l_old

;<------- Online Softmax Loop BR ------>
; fp (x1) stores m_curr
; fp (x2) stores (exp(m_last - m_curr)) ^ -1
; fp (x3) stores sum(vect)
; fp (x4) stores l
S_LD_FP    fp1, gp6, 0; load m_last from FP[MLEN] to fp1
S_MV_FP    fp2, fp1, 0; copy m_last to fp2
V_RED_MAX  fp1, gp4, 0; m_curr = find max of (P[x4], m_last) and store at fp1
S_SUB_FP   fp2, fp2, fp1; m_res = m_last - m_curr
S_EXP_FP   fp2, fp2, 0; exp(m_res)
S_ST_FP    fp1, gp6, 0; store m_curr at FP[MLEN]
V_SUB_VF   gp4, gp4, fp1; S' = S - m_curr
V_EXP_V   gp4, gp4, 0; P = exp(S')
S_LD_FP    fp4, gp1, 0; load l_old from FP[2*MLEN] to fp4
V_RED_SUM  fp3, gp4, 0; P = sum(P)
S_MUL_FP   fp4, fp4, fp2; l_s = l_old * exp(m_res)
S_ADD_FP   fp4, fp3, fp4; l_s = l_old * exp(m_res) + sum(P)
S_ST_FP    fp2, gp7, 0; store m_res at FP[2*MLEN] so that later on we can map it to a vector and conduct line 10.
S_ST_FP    fp4, gp1, 0; store l_s at FP[3*MLEN]
S_ADD_FIX  gp4, gp4, gp5; next row of S
S_ADD_FIX  gp6, gp6, 1; next row of m_old
S_ADD_FIX  gp7, gp7, 1; next row of m_res
;<------- Online Softmax Loop MLEN END ------>
;<<<< -------Complete Online Softmax------- >>>>
; Multiplying with V
; compute sequence address of V      
S_ADDI_FIX  gp2, gp0, 0;                      gp2 = 0 Offset for V (different sequences of V)
H_PREFETCH_M { rd: gp0, rs1: gp2, rs2: a4, rstride: 1, precision: kv }; Load MLEN * Head Dimension elements of V
;<------- PV (MLEN, MLEN) @ (MLEN, head_dim) 1st LOOP  Head_dim / MLEN ------>







; THE FOLLOWING CODE IS NOT BEEN VERIFIED
; THE FOLLOWING CODE IS NOT BEEN VERIFIED
; THE FOLLOWING CODE IS NOT BEEN VERIFIED
; THE FOLLOWING CODE IS NOT BEEN VERIFIED
; THE FOLLOWING CODE IS NOT BEEN VERIFIED









;<------- PV (MLEN, MLEN) @ (MLEN, BLEN) 2nd LOOP  MLEN / BLEN --------->
; gp1: Address for P
; gp2: Address for V
; gp3: Loop Counter
; gp4: MLEN * BLEN * (Weight Precision) or MLEN * BLEN * (K Precision)          : P block address size or V block address size
; gp7: Address for PV result
;<--- LOOP Init --->
S_ADD_FIX gp5, gp0, 0; V1 address
S_ADDI_FIX gp4, gp0, 0; Loop Counter
;<--- LOOP Init --->

;<------- PV (BLEN, MLEN) @ (MLEN, BLEN) 3rd LOOP  MLEN / BLEN ------>
; gp1: Address for P
; gp2: Address for V
; gp3: Loop Counter
; gp4: MLEN * BLEN * (Weight Precision) or MLEN * BLEN * (K Precision)          : P block address size or V block address size
; gp7: Address for PV result
;<--- LOOP Init --->
S_ADD_FIX gp2, gp0, gp5; V address
S_ADDI_FIX gp3, gp0, 0; Loop Counter
;<--- LOOP Init --->

M_MM_WO gp7, gp1, gp2; (BLEN * MLEN) * (MLEN * BLEN): P * V
S_LD_FIX gp2, gp0, 18; Load MLEN * BLEN (next internal column block of V)
S_MUL_FIX gp2, gp3, gp2; Calculate current V column block offset
S_ADDI_FIX gp2, gp5, gp2; Calculate current V address

;<------- PV (BLEN, MLEN) @ (MLEN, BLEN) 3rd LOOP  MLEN / BLEN ------>

S_LD_FIX gp3, gp0, 18; Load MLEN * BLEN (next internal row block of P)
S_ADDI_FIX gp1, gp1, gp3; Update P to the next row block

;<------- PV (MLEN, MLEN) @ (MLEN, BLEN) 2nd LOOP  MLEN / BLEN --------->

;<------- PV (MLEN, MLEN) @ (MLEN, head_dim) 1st LOOP  Head_dim / MLEN ------>
