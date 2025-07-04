S_LUI_FIX x1, 0;
S_LUI_FIX x2, 0;

C_SET_ADDR_REG x1, x1, x2;

H_PREFETCH_M_C x1, x2, x1;

S_ADDI_FIX x3, x0, 8;

S_ADDI_FIX x4, x0, 4;

S_MUL_FIX x5, x3, x4;

H_PREFETCH_V_C x1, x5, x1;

M_MM_IC  x0, x1, x1; 

S_ADDI_FIX x4, x0, 2;

S_MUL_FIX x1, x3, x4;

M_MV_IC  x5, x0, x1;

M_MV_WO x4, x0, x0;

M_TMV_IC x5, x0, x1;

M_MV_IC  x5, x0, x1;

M_MV_WO x4, x0, x0;

