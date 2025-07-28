
S_LUI_FIX i1, 0; 
C_SET_ADDR_REG a1, i1, i1; 
H_PREFETCH_V i1, i1, a1; 
// i1 = x
S_LUI_FIX i2, 0; 
S_LD_FP f1, i1, 0; 
// f1 = 1
V_EXP_V i2, i1, 0;
// i2 = exp(x)
V_ADD_VF i1, i2, f1;
// i1 = exp(x) + 1
V_RECI_V i1, i1, 0;
// i1 = 1 / (exp(x) + 1)
V_MUL_VV i1, i1, i2;
// i1 = exp(x) / (exp(x) + 1)
H_STORE_V_H_C i1, i2, a2; 
// HBM[1] = i1