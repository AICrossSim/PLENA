
S_MV_FIX x8, x0;                          Current tile addr for embedded vector in SSRAM
S_MV_FIX x9, x0;                          Current tile addr for MVM results in accumulator

S_ADDI_FIX x8, x8, MLEN;             Current tile addr for embedded vector in SSRAM
S_ADDI_FIX x9, x9, MLEN;             Current tile addr for MVM results in accumulator

H_PREFETCH_M  x13, x11, csr_adr[0];         Fetch the weight for ith hidden layer Q from HBM to MVM SRAM
C_SET_MV_OFFSET x13;                        Set the offset addr for the MVM operation
H_PREFETCH_V  x13, x8,  csr_adr[8];         Fetch the embedded vector from HBM to MVM SRAM

M_MV x9, x13, x13;  

S_ADDI_FIX      x11, x11, MLEN * MLEN;            Storing the address for the next tile in MVM SRAM
S_ADDI_FIX      x8,  x8,  MLEN;       Storing the address for the next tile in SSRAM

