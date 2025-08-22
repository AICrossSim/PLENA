S_LUI_INT gp1, 256; 
C_SET_SCALE_REG gp1; 
C_SET_ADDR_REG a1, gp0, gp0; 
H_PREFETCH_V gp0, gp0, a1, 0, 0;
S_LUI_INT gp2, 0; 
S_LD_FP f1, gp2, 0;
//V_ADD_VF gp1, gp2, f1; 
//V_PS_V gp1, gp2, gp0;
V_SHFT_V gp1, gp1, 2;