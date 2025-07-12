
// testing for HBM[2] = HBM[1] + HBM[0]

S_LUI_FIX x1, 0; // x1 = 0 << 12
S_LUI_FIX x2, 1; // x2 = 1 << 12
C_SET_ADDR_REG x1, x1, x2; // {x1, x1} -> addr_x2
H_PREFETCH_V_C x2, x1, x2; // HBM[x1+addr_x2] -> VSRAM[x2]
V_ADD_VV x1, x1, x2; // VSRAM[x1] + VSRAM[x2] -> VSRAM[x3]
S_LUI_FIX x3, 1; // x3 = 1 << 12

H_STORE_V_H_C x1, x2, x2; // VSRAM [FIX_REG[x3]]= VSRAM[x1]

H_PREFETCH_V_C