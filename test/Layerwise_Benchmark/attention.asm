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
; Assume Q (N, d) is stored in HBM[Q] (This case, assuming b=s=1)
; Assume K (N, d) is stored in HBM[K]
; Assume V (N, d) is stored in HBM[V]
; Assume O (N, d) is stored in HBM[O]
; Assume m_curr ([1:Br+1]) is stored in FP_SRAM[m_curr:m_curr+Br]
; Assume m_last ([1:Br+1]) is stored in FP_SRAM[m_last:m_last+Br]
; Assume l ([1:Br+1]) is stored in FP_SRAM[l:l+Br]
; Assume o_scale ([1:Br+1]) is stored in FP_SRAM[o:o+Br]

; Assume Q value is directly stored in ADR[Q]
; Assume K value is directly stored in ADR[K]
; Assume V value is directly stored in ADR[V]
; Assume O value is directly stored in ADR[O]


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

S_ADDI_FIX x1, x0, 0;           set FIX[1] to 0, use it as an incremental pointer (loop index) across N/Br
; LOOP N / Br
    S_ADDI_FIX x2, x0, 0;               set FIX[2]] to 0, use it as an incremental pointer (loop index) across N/Bc
    ; LOOP N / Bc
        S_ADDI_FIX x3, x0, 0;               set FIX[3] to 0, use it as an incremental pointer (loop index) across d/i

        S_ADDI_FIX x4, x3, 0;               set FIX[4] to 0, use it to store offset address for different Q blocks; loop index * (Q block size)
        S_ADDI_FIX x5, x3, 0;               set FIX[5] to 0, use it to store offset address for different K blocks; loop index * (K block size)
        S_ADDI_FIX x6, x0, 1;               set FIX[6] to 1, use as pointer to the beginning M_SRAM, V_SRAM location
        
        ; compute address of Q/K blocks
        S_ADDI_FIX x7, x0, Br * d;          Br * d is Br of query vector
        S_MUL_FIX  x4, x1, x7;              x4 = r * (Br * d)
        S_ADDI_FIX x8, x0, Bc * d;          Bc * d is Br of key vector
        S_MUL_FIX  x5, x2, x8;              x5 = c * (Bc * d)

        S_ADDI_FIX x7, x0, Br * i;          reset x7,x8 to block size of Q, K for indexing d/i
        S_ADDI_FIX x8, x0, Bc * i;
        ; LOOP d/i - 1; not the last loop
            H_PREFETCH_V_C x6, x4, ADR[Q];
            H_PREFETCH_M_C x6, x5, ADR[K];
            M_BMM 0, x6, x6
            S_ADDI_FIX x4, x4, x7;              x4 = x4 + x7        
            S_ADDI_FIX x5, x5, x8;              x5 = x5 + x8
        ; LOOP d/i; last loop   
            H_PREFETCH_V_C x6, x4, ADR[Q];
            H_PREFETCH_M_C x6, x5, ADR[K];
            M_BMM_O x6, x6, x6;                 store S in Q to VSRAM[1]
            S_ADDI_FIX x4, x4, x7;                      
            S_ADDI_FIX x5, x5, x8;           
        

        ; Compute the row max of all the S
        S_ADDI_FIX x7, x0, 0;               use it as loop index for Br
        S_ADDI_FIX x4, x0, x6;              set x4 to 1, use it to index VSRAM
        ; LOOP Br;
            V_RED_MAX x0, x4, x6;               perform reduce and store it in REG[1]
            S_ST_FP m_curr, x7, x6;             perform store REG[1] to FP[x7]

            S_ADDI_FIX x4, x4, Bc;              next row address in V_RAM
            S_ADDI_FIX x7, x7, 1;               next FP address
        

        ; Compute online softmax
        S_ADDI_FIX x7, x0, 0;               set FIX[7] to 0, use it as an incremental pointer (loop index) across #Br of scaler

        S_ADDI_FIX x3, x0, x6;              set x3 to 1, use it to point to the beginning of computed S in V_RAM
        S_ADDI_FIX x4, x0, x6;              set x4 to 1, use it to store m_curr
        S_ADDI_FIX x5, x4, 1;               set x5 to 2, use it to store m_last
        S_ADDI_FIX x6, x5, 1;               set x6 to 3, use it to store p_sum
        S_ADDI_FIX x8, x6, 1;               set x6 to 4, use it to store l
        ; LOOP Br;
            S_LD_FP m_curr, x7, x4;             load curr m to x4
            S_LD_FP m_last, x7, x5;             load last m to x5
            S_MAX_FP x5, x4, x4;                x4 (m_new) = max(m_curr, m_last)
            S_SUB_FP x5, x4, x5;                x5 (m_res) = max(m_last, x4)

            V_SUB_VF x4, x3, x3;                x7 (s_j_shifted) = x7 (row) - x4 (m_new)
            V_EXP_V  0, x3, x3;                 x7 (p) = torch.exp(x7 (s_j_shifted))
            V_RED_SUM x0, x3, x6;               x6 (p_sum) = x7.sum (p.sum())

            S_EXP_FP 0, x5, x5;                 x5 (l_scale/o_scale) = exp(x5 (m_res))
            S_LD_FP l, x7, x8;                  load l to x8
            S_MUL_FP x8, x5, x8;                x8 (l_inter) = l_scale (x5) * l (x8)
            S_ADD_FP x8, x6, x8;                x8 (l_new) = l_inter (x8) + p_sum (x5)

            S_ST_FP m_last, x7, x4;             store m_new to m_last
            S_ST_FP l, x7, x8;                  store l_new to l
            S_ST_FP o_scale, x7, x5;            store o_scale to o_scale

            S_ADDI_FIX x3, x3, Bc;              next vector
            S_ADDI_FIX x7, x7, 1;               next scaler
        
        ; Multiplying with V
        ; compute address of V
        S_ADDI_FIX x7, x0, Bc * Bc;
        S_MUL_FIX  x4, x2, x7;              x4 = c * (Bc * Bc) address offset V
        S_ADDI_FIX x7, x0, Bc * Br;
        S_MUL_FIX  x5, x2, x7;              x5 = c * (Bc * Br) address offset O

        S_MUL_FIX  x6, x0, 1;               set x6 pointing to p again
        S_MUL_FIX  x7, x6, Bc * Br;         set x7 pointing to O in V_RAM

        ; LOOP N/Bc;
            H_PREFETCH_M_C x6, x4, ADR[V];
            M_BMM_O x6, x6, x6;             x6 (p@v) = x6 (p V_RAM) @ x6 (v S_RAM)
            H_PREFETCH_M_C x7, x5, ADR[O];    load previous O matrix

            S_ADDI_FIX x3, x0, 0;           use this to index row
            ; LOOP Br;
                ; if x2 != N/Bc:
                S_LD_FP o_scale, x3, x8;    load curr m to x4
                V_MUL_VF x8, x7, x7;        x7 = x8 (o_scale) * x7(O)      
                V_ADD_VV x7, x6, x7;        x7 = x7 (o_scale * O) + x6 (p@v)   
                ; compute O store address ADR[O] based on x1, x2
                S_ADDI_FIX x6, x0, 1;
                S_MULI_FIX x6, x1, N/Br;
                S_ADDI_FIX x6, x6, x2;
                S_MULI_FIX x6, x6, Br * Bc;
                H_STORE_HBM ADR[O], x6, x7;

                ; if x2 == N/Bc:
                ; NOTE: TODO : Flash attention 2 line 12. Load all O back and scale all of them?
                S_LD_FP o_scale, x3, x8;    load curr m to x4
                V_MUL_VF x8, x7, x7;        x7 = x8 (o_scale) * x7(O)      
                V_ADD_VV x7, x6, x7;        x7 = x7 (o_scale * O) + x6 (p@v)   
                S_LD_FP l, x3, x4;          load l to x4
                S_REC_FP x4, x4;            
                V_MUL_VF x4, x7, x7;        x7 = x4 (1/l) * x7(O)  
                ; compute O store address ADR[O] based on x1, x2
                S_ADDI_FIX x6, x0, 1;
                S_MULI_FIX x6, x1, N/Br;
                S_ADDI_FIX x6, x6, x2;
                S_MULI_FIX x6, x6, Br * Bc;
                H_STORE_HBM ADR[O], x6, x7;


                S_ADDI_FIX x3, x3, 1;
                S_ADDI_FIX x7, x7, Bc;
                S_ADDI_FIX x6, x6, Bc;

            S_ADDI_FIX x4, x4, Bc * Bc;

    S_ADDI_FIX x2, x2, 1;
S_ADDI_FIX x1, x1, 1; 
