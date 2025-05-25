
S_LUI_FIX x1, 6;
S_LUI_FIX x2, 8;

C_SET_ADDR_REG x1, x1, x2;

H_PREFETCH_M x1, x2, x1;

S_ADDI_FIX x3, x0, 12;

S_ADDI_FIX x4, x0, 12;

S_MUL_FIX x5, x3, x4;

H_PREFETCH_V x1, x3, x1;

M_MV x5, x1, x1; 

C_SET_M_OFFSET x3;

M_TMV_O x5, x1, x1; 

H_STORE_V x5, x0, x1;