S_LUI_FIX i1, 0;
S_LUI_FIX i2, 0;

C_SET_ADDR_REG a1, i1, i2;

H_PREFETCH_M_H_C i1, i2, i1;

H_PREFETCH_V_H_C i1, i2, i1;

M_MV_IC  i5, i0, i1;
S_ADDI_FIX i5, i0, 0;
M_MV_WO i4, i0, i0;

M_TMV_IC i5, i0, i1;

M_MV_IC  i5, i0, i1;

M_MV_WO i4, i0, i0;

