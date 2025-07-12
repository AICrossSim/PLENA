
// testing for HBM[2] = HBM[1] + HBM[0]

S_LUI_FIX x1, 0; // register x1 = 0 << 12
S_LUI_FIX x2, 0; // register x2 = 0 << 12
C_SET_ADDR_REG x1, x1, x2; // set address register to ADR[x2] = {x1, x1}
H_PREFETCH_V_C x2, x1, x2; // prefetch VSRAM[x3] = HBM[FIX[x1]+ADR[x2]]
V_ADD_VV x1, x1, x2; // VSRAM[x2] = VSRAM[x1] + VSRAM[x1]

H_STORE_V_H_C x1, x2, x3; // HBM[FIX[x1]+ADR[x2]] = x1

H_PREFETCH_V_C