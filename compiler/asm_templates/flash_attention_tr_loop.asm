;<------------------------------------------------ LOOP Tr Iteration 0 ------------------------------------------------>
;<---------------- Set up Environment (m) ---------------->
S_LD_FP f1, i0, 0;
S_ADDI_FIX i1, i0, 1;
; Loop MLEN Times, set a region of m to be negative infinity (negative max)
;<--- LOOP MLEN Times --->
S_ST_FP f1, i1, 0;
S_ADDI_FIX i1, i1, 1;
;<--- LOOP MLEN Times --->
;<---------------- Set up Environment (O) ---------------->
S_LD_FIX i1, i0, 15;
V_RESET_SRAM 0, i1, 0;
;<---------------- Fetch Q ---------------->
S_LD_FIX i1, i0, 13;
S_LD_FIX i2, i0, 6;
S_MUL_FIX i2, i2, i1;
H_PREFETCH_V_H_S i0, i2, a2; 
S_ADDI_FIX i1, i1, 1;
S_ST_FIX i1, i0, 13;

;;;;; <flash_attention_tc_loop> Repeat Tc Times ;;;;;;

S_LD_FIX        x1, x0, 3;
;<----------- Loop MLEN, l^(-1)------------->
S_LD_FP         x1, x1, 0;          Load l_old to x1
S_RECI_FP       x1, x1, 0;
S_ST_FP         x1, x1, 0;
S_ADDI_FIX      x1, x1, 1;
;<----------- Loop MLEN, l^(-1) END---------->

S_LD_FIX        x1, x0, 3;          x1 = 2*MLEN, l_old 
S_MAP_V_FP      x0, x1, 0;          Store at 0 to replace m.
;<----------- Loop Hidden, diag O ------------->
S_LD_FIX        x1, x0, 2;          
S_LD_FIX        x2, x0, 12;          x1 = MLEN * MLEN + Head_DIM * MLEN; Offset for O.
V_MUL_VV        x2, x2, x0;          x4 = diag-1 * O
S_ADD_FIX       x2, x2, x1;          x4 = diag-
;<----------- STORE to HBM ---------->
