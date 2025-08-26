//A_cs = cumsum(A)

S_LUI_INT gp1, 256;
C_SET_SCALE_REG gp1;

C_SET_ADDR_REG aA, gp0, gp0;
H_PREFETCH_V gp0, gp0, aA, 0, 0;
V_PS_V gp2, gp0, gp0; //gpAcs stores PS of A //gpAcs = gp2

C_SET_ADDR_REG aL, gp0, gp0; //get address of matrix L, the diagonal elements L[i,i] should be 1 by default
							// this is how it is initialised in memory

V_SUB_VV gp3, gp2, gp2; //gpOnes is now a vector of 0s //gp3 = gpOnes
S_LUI_INT gp4, 1; //gp4 = gp_one
S_LD_FP f1, gp4, 0;
V_ADD_VF gp3, gp3, f1;

S_LUI_INT gp5, 1; //gp5 = gpK
//loop k = 1 to VLEN-1 //gp5 stores the variable we iterate i.e. k
//shifted = shift_right(A_cs, k)
V_SHFT_V gp6, gp2, gp5; //gp6 = gpShift
//diff = A_cs - shifted
V_SUB_VV gp7, gp2, gp6; //gp7 = gpDiff
//exp(diff)
V_EXP_V gp7, gp7; //gp7 = gpExp
//mask = shift_right(ones, k)
V_SHFT_V gp8, gp3, gp5; //gp8 = gpMask
//out = exp * mask
V_MUL_VV gp7, gp7, gp8; //gp7 = gp7 * gp8
//store this vector gpOut in the kth column of matrix L
// k++, continue iterating until k = VLEN