S_LUI_FIX x1, 0;
S_LUI_FIX x2, 0;

C_SET_ADDR_REG x1, x1, x2;

H_PREFETCH_M x1, x2, x1;

S_ADDI_FIX x3, x0, 8;

S_ADDI_FIX x4, x0, 8;

S_MUL_FIX x5, x3, x4;

H_PREFETCH_V x1, x5, x1;

M_TMM x0, x1, x1; 

S_ADDI_FIX x4, x0, 4;

S_MUL_FIX x1, x3, x4;

M_TMM_O x5, x1, x1; 

S_ADDI_FIX x4, x0, 0;

H_STORE_V x5, x4, x1;