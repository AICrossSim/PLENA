S_LUI_INT gp1, 0;                  // scale (unchanged)

// rs1 base pointer in a GP reg
S_LUI_INT gp2, 0;                  // base = 0

// Program address reg a1 from gp2 (base) and gp0 (stride=0 here)
C_SET_ADDR_REG a1, gp2, gp0;

// Prefetch with non-zero stride (use 4 if stride is in bytes)
H_PREFETCH_V gp0, gp0, a1, 1, 0;

// Optional add for visibility
S_LD_FP f1, gp1, 0;
V_ADD_VF gp1, gp1, f1;

// EXP interface: (rd, rs1, x). Use rs1 = gp2 (the base GP reg), not a1.
V_EXP_V gp1, gp2, 0;

// Optional store (use supported store mnemonic if needed)
// H_STORE_V gp1, gp2, a2;