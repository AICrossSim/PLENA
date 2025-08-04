S_LUI_FIX i1, i0, 0;
S_LUI_FIX i2, i0, 0;
C_SET_ADDR_REG a1, i1, i2;
H_PREFETCH_M_H_C i1, i2, i1;
S_ADDI_FIX i3, i0, 8;
S_ADDI_FIX i4, i0, 4;
S_MUL_FIX i5, i3, i4;
H_PREFETCH_V_H_C i1, i2, i1;
M_MM_IC i0, i1, i1; 
S_ADDI_FIX i4, i0, 2;
M_MM_PS  i0, i1, i1;
S_ADDI_FIX i3, i0, 8;
M_MM_WO i4, i0, i0;


