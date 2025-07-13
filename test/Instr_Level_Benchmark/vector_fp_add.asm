
S_LUI_FIX i1, 0; 
C_SET_ADDR_REG a1, i1, i1; 
H_PREFETCH_V_C i1, i1, a1; 

S_LD_FP f1, i1, 0; 
V_ADD_VF i1, i1, f1; 
V_ADD_VV i1, i1, i1; 

S_LUI_FIX i2, 1; 
H_STORE_V_H_C i1, i2, a2; 