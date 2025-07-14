S_ADDI_FIX x1, x0, 0;
S_ADDI_FIX x2, x0, 0;
C_SET_ADDR_REG x1, x1, x2;
H_PREFETCH_M_C x1, x2, x1;
S_ADDI_FIX x3, x0, 8;
S_ADDI_FIX x4, x0, 4;
S_MUL_FIX x5, x3, x4;
H_PREFETCH_V_H_C x1, x5, x1;
S_ADDI_FIX x1, x0, 0;
S_LD_FIX x2, x0, 2;
S_ADDI_FIX x3, x0, 0;
//////
V_RED_SUM x1, x1, 0;
S_ST_FP   x1, x3, 0;
S_ADD_FIX x1, x1, x2;
S_ADDI_FIX x3, x3, 1;
V_RED_SUM x1, x1, 0;
S_ST_FP   x1, x3, 0;
S_ADD_FIX x1, x1, x2;
S_ADDI_FIX x3, x3, 1;
V_RED_SUM x1, x1, 0;
S_ST_FP   x1, x3, 0;
S_ADD_FIX x1, x1, x2;
S_ADDI_FIX x3, x3, 1;
V_RED_SUM x1, x1, 0;
S_ST_FP   x1, x3, 0;
S_ADDI_FIX x3, x0, 0;
S_MAP_V_FP x0, x0, 0;
V_RESET_SRAM x0, x0, 0;


//////
