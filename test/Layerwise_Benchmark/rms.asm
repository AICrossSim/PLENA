; Parameters:
; VLEN = 4
; Hidden_Size= 16

S_ADDI_FIX x1, x0, 0;
S_MV_FP fp3, fp0; 
S_ADDI_FIX x3, x0, 4;

S_MUL_FIX x3, x3, x3;
; x3 = 'h10


; Repeat the following sections{

H_PREFETCH_V_C x1, x1, x0;
V_MUL_VV x3, x1, x1;
; x3 = 'h10

S_MV_FIX x2, x3;

; Bug here
S_ADDI_FIX x1, x1, 4;
; x1 = 4
; 1000 001 001 011001

S_ADDI_FIX x3, x3, 4;
; x3 = 'h16
H_PREFETCH_V_C x1, x1, x0;
V_MUL_VV x3, x1, x1;
V_RED_SUM fp3, x2, x3;
S_ADDI_FIX x1, x1, 4;
S_ADDI_FIX x3, x3, 4;

;}