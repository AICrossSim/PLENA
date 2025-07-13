; def rms_norm(x: torch.Tensor, w: torch.Tensor, s: int, h: int, var_eps: float):
;     """
;     Args:
;         x: (b, s, h), where b = batch size, s = sequence length, h = hidden size
;         w: (h,)
;         s: sequence length
;         h: hidden size
;         var_eps: epsilon for variance

;     Returns:
;         out: (b, s, h)
;     """

; Assembler Supported formats:
; - opcode rd, rs1, imm;
; - opcode rd, rs1, rs2;
; - opcode rd, rs1;
; - opcode rd;

; on-chip address 32-bit
; HBM address 4-bit
; ============================================================
; Preliminary
; ============================================================
; Assume x (b, s, h) is stored in HBM[ACTIVATION_OFFSET] (This case, assuming b=s=1)
; Assume w (1,h) is stored in HBM[W_OFFSET]
; Assume var_eps is stored in FP_MEM[0]
; Assume h is stored in FP_MEM[1]
; Assume W_OFFSET value is directly stored in ADR[1]
; Assume ACTIVATION_OFFSET value is directly stored in ADR[0] (Otherwise need to use C_SET_ADDR_REG to set this.)

; Available Fixed-Point Regfile: FIX[1], ..., FIX[8]
; Available Floating-Point Regfile: FP[1], ..., FP[8]
; M_LEN: 32
; V_LEN: 32
; DataType : MXFP ELEMENT 8 bits and SCALE 16 bits
; Matrix SRAM: 2 * MLEN * MLEN
; Vector SRAM: 2 * Hidden_size
; VEC_LOOP_SIZE: h / V_LEN
; HALF_VEC_LOOP_SIZE: h / V_LEN / 2
; ============================================================

; -------- square_bsh = x.pow(2) ----------------
; -------- sum_bs = x.sum(dim=2) ----------------
S_ADDI_FIX x1, x0, 0;                          Set FIX[1] to 0, use it to record address offset

; load whole x from HBM[ACTIVATION_OFFSET] to Vector SRAM
;< - Duplicate VEC_LOOP_SIZE times{
    H_PREFETCH_V_H_C x1, x1, ADR[0];                   Prefetch x from HBM to MVM SRAM 
    S_ADDI_FIX x1, x1, VLEN;                       Assume datatype is 8 bits, increment the address offset by V_LEN every iteration
;}

; compute x.pow(2)
S_MV_FP fp3, fp0;                              Set FP[3] to 0, use it to record sum  
S_ADDI_FIX x2, x0, 0;                          FIX[1] now points to x^2; Set FIX[2] to 0, use it to point to x again
; |x1| Hidden_size |x2| 0 
;< - Duplicate VEC_LOOP_SIZE times{
V_ADD_VV x2, x2, x1;
S_ADDI_FIX x1, x1, VLEN;
S_ADDI_FIX x2, x2, VLEN;
;}
; reduce all x^2
S_ADDI_FIX x3, x2, VLEN;                       FIX[2] now points to x^2[0]; Set FIX[3] to x^2[1]
; |x1| 2*Hidden_size |x2| Hidden_size |x3| Hidden_size + VLEN
;< - Duplicate HALF_VEC_LOOP_SIZE times{
V_RED_SUM fp3, x2, x3;
S_ADDI_FIX x2, x2, 2*VLEN;
S_ADDI_FIX x3, x3, 2*VLEN;
;}

; now fp3 contains the sum(x^2) and Vector SRAM contains both x and x^2.
; we don't need x^2 anymore, overwrite it with w.
; |x1| 2*Hidden_size |x2| 2*(Hidden_size - VLEN) |x3| 2*Hidden_size
S_ADDI_FIX x1, x0, 0;                       Point to beginning of x in VSRAM
S_ADDI_FIX x2, x0, Hidden_Size;             Point to beginning of x^2 in VSRAM
S_ADDI_FIX x3, x0, 0;                       Counter for looping over VLEN
; |x1| 0 |x2| Hidden_size |x3| 0
;< - Duplicate VEC_LOOP_SIZE times{
H_PREFETCH_V_H_C x2, x3, ADR[1];
S_ADDI_FIX x3, x3, VLEN;
S_ADDI_FIX x2, x2, VLEN;
;}
 
; |x1| 0 |x2| 2*Hidden_size |x3| Hidden_size

; -------- var_bs = sum_bs / h ----------------
S_LD_FP fp1, x0, 8;                          Load 1/h from FP_MEM[8] to FP[1]
S_MUL_FP fp1, fp1, fp3;
; |fp3| sum(x^2) |fp1| var_bs

; -------- sqrt_bs = torch.sqrt(var_bs + var_eps) ----------------
S_LD_FP fp2, x0, 0;                       Load var_eps from FP_MEM[0] to FP[2]
S_ADD_FP fp1, fp1, fp2;                   Add var_eps to var_bs
S_SQRT_FP fp1, fp1;                       Take the square root of var_bs + var_eps
; |fp3| sum(x^2) |fp1| sqrt_bs

; -------- rsqrt_bs = 1.0 / sqrt_bs ----------------
S_RECI_FP fp1, fp1;                           Take the reciprocal of sqrt_bs
; |fp3| sum(x^2) |fp1| rsqrt_bs

; -------- x_norm_bsh = x * rsqrt_bs----------------
; |x1| 0 |x2| 2*Hidden_size |x3| Hidden_size
;< - Duplicate VEC_LOOP_SIZE times{
V_MUL_VF x1, x1, fp1;
S_ADDI_FIX x1, x1, VLEN;
;}

; -------- out_bsh = w * x_norm_bsh----------------
S_ADDI_FIX x2, x0, 0;                          Set FIX[1] to 0, reset it to 0; use to point x_norm_bsh and the updated out_bsh
; |x1| Hidden_size |x2| 0 |x3| Hidden_size
;< - Duplicate VEC_LOOP_SIZE times{
V_MUL_VV x2, x1, x2;    
S_ADDI_FIX x1, x1, VLEN;
S_ADDI_FIX x2, x2, VLEN;

H_STORE_V_H_C x2, x2, ADR[0];                       Store the result of x_norm_bsh to HBM
;}

