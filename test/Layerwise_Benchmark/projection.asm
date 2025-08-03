S_LUI_FIX i1, i0, 0;
S_LUI_FIX i2, i0, 0;
C_SET_ADDR_REG i1, i1, i2;
H_PREFETCH_M_C i1, i2, i1;
S_ADDI_FIX i3, i0, 8;
S_ADDI_FIX i4, i0, 4;
S_MUL_FIX i5, i3, i4;
H_PREFETCH_V_H_C i1, i5, i1;
M_MM_IC  i0, i1, i1; 
S_ADDI_FIX i4, i0, 2;
S_MUL_FIX i1, i3, i4;
M_MM_PS  i5, i0, i1;
S_ADDI_FIX i3, i0, 8;
C_SET_STRIDE_REG i3, i0, i0;
S_MV_FIX i1, i0; 
S_MV_FIX i2, i0; 
H_PREFETCH_M_S i1, i2, i1;
S_ADDI_FIX i3, i0, 8;
S_ADDI_FIX i4, i0, 4;
S_MUL_FIX i5, i3, i4;
H_PREFETCH_V_H_S i1, i5, i1;
M_MM_IC  i0, i1, i1; 
S_ADDI_FIX i4, i0, 2;
S_MUL_FIX i1, i3, i4;
S_ADDI_FIX i2, i0, 1;
M_MM_PS  i2, i0, i1;
M_MM_WO i4, i0, i0;


