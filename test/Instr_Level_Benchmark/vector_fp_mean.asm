
// testing for HBM[2] = HBM[1] + HBM[0]

S_LUI_FIX x1, 0; // x1 = 0 << 12
C_SET_ADDR_REG x2, x1, x1; // 
H_PREFETCH_V_C x1, x1, x2; // HBM[addr_x2 + 0] -> VSRAM[x1]

// 1/(1+exp(-x))
S_LUI_FIX x3, 0; 
V_SUB_VV x3, x3, x1;// x3 = -x
V_EXP_V x3, x3, x2; // x4 = exp(-x)
S_LD_FP x4, 1; // question, the floating point can be represented as decimal? 
V_ADD_VF x3, x3, x4;
V_REC_V x3, x3;

S_LUI_FIX x1, 1; // x1 = 0 << 12
H_STORE_V_H_C x3, x1, x2; // HBM[addr_x2 + 1] = VSRAM[x3]

