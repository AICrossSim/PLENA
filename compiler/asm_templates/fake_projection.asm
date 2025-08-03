; Basic projection template for matrix multiplication
; Load weights and perform matrix multiplication
S_LD_FIX i1, i0, 0; Load weight offset
H_PREFETCH_V_H_S i0, i1, a0; Prefetch weights
M_TMM_IC 0, i0, i0; Initialize tensor matrix multiplication
M_TMM_PS i0, i0, i0; Perform tensor matrix multiplication 