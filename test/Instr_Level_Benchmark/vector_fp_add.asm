
S_LUI_FIX fx_x1, 0; 
// x1 = 0 << 12
C_SET_ADDR_REG addr_x1, fx_x1, fx_x1; 
H_PREFETCH_V_C fx_x1, fx_x1, addr_x1; 
// HBM[addr_x2 + 0] -> VSRAM[x1]

S_LD_FP fp_x1, fx_x1, 0; 
V_ADD_VF fx_x1, fx_x1, fp_x1; 
// VSRAM[x3(1)] = VSRAM[x1(0)](x) + 1
V_ADD_VV fx_x1, fx_x1, fx_x1; 
// VSRAM[x3(1)] = VSRAM[x1(0)](x) + VSRAM[x3(1)](x + 1)

S_LUI_FIX fx_x2, 1; 
// x2 = 1
H_STORE_V_H_C fx_x1, fx_x2, addr_x2; 
// HBM[addr_x2 + 1] = VSRAM[x3]