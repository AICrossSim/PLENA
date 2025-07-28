
S_LUI_INT gp1, 0; 
C_SET_ADDR_REG a1, gp1, gp1; 
H_PREFETCH_V gp1, gp1, a1, 0, 0;
S_LUI_INT gp2, 0; 
S_LD_FP f1, gp1, 0; 
V_EXP_V gp2, gp1, 0;
V_ADD_VF gp1, gp2, f1;