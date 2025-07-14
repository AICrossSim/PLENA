; ============================================================
; Preliminary
; ============================================================
; Flash Attention simple version
; Assume Tr = Tc = 1
; Three MXFP Data Types:
; 1. Weight
; 2. KV Cache
; 3. Activation
; MLEN = 4, 

; ============================================================

;<---------------- Set up Environment ---------------->
; Set Stride Register


;<------------------------------------------------ LOOP Tr Iteration 0 ------------------------------------------------>

; Set Up Variables
S_LD_FP f1, i0, 0;
S_ADDI_FIX i1, i0, 1;
; Loop MLEN Times, set a region of m to be negative infinity (negative max)
S_ST_FP f1, i1, 0;
S_ADDI_FIX i1, i1, 1;
S_ST_FP f1, i1, 0;
S_ADDI_FIX i1, i1, 1;
S_ST_FP f1, i1, 0;
S_LD_FIX i1, i0, 15;
V_RESET_SRAM 0, i1, 0;

;<--------------------------------  LOOP Tc Iteration 0 -------------------------------->

S_LD_FIX i1, i0, 0;
C_SET_STRIDE_REG i1, 0;
H_PREFETCH_V_H_S i0, i0, i0;    
S_LD_FIX i1, i0, 1;
C_SET_STRIDE_REG i1, 0, 0;
H_PREFETCH_M_L_S i0, i0, i0;      
; Load K

;<--------LOOP Internal QKT (head_dim // MLEN) Iteration 0 -------->    
; i1: Address for Q
; i2: Address for K
; i3: Loop Counter
; i4: MLEN * BLEN * (Weight Precision)
; i5: MLEN * BLEN * (K Precision)
; i6: Counter for head_dim // MLEN iteration
S_LD_FIX i6, i0, 0;
S_LD_FIX i4, i0, 10;
S_LD_FIX i5, i0, 11;

;<---------------- LOOP Internal QKT (MLEN/BLEN) Iteration 0 ---------------->
S_ADDI_FIX i1, i0, 0;
S_ADDI_FIX i2, i0, 0;
S_ADDI_FIX i3, i0, 0;
M_TMM_IC 0, i1, i2;
S_ADDI_FIX i3, i0, 1;
S_MUL_FIX i1, i3, i4;
S_MUL_FIX i2, i3, i5;
M_TMM_PS i6, i1, i2;
S_ADDI_FIX i6, i0, 1;

;<--------LOOP Internal QKT (head_dim // MLEN) Iteration 1 -------->   
S_ADDI_FIX i1, i0, 0;
S_ADDI_FIX i2, i0, 0;
S_ADDI_FIX i3, i0, 0;
M_TMM_IC 0, i1, i2;
S_ADDI_FIX i3, i0, 1;
S_MUL_FIX i1, i3, i4;
S_MUL_FIX i2, i3, i5;
M_TMM_PS i6, i1, i2;
S_ADDI_FIX i6, i0, 1;

