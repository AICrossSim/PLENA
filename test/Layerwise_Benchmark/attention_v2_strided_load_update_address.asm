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
; Assume Q (N, d) is stored in HBM[Q] (This case, assuming b=1 and dimension: (b,s,h,d))
; Assume K (N, d) is stored in HBM[K] (This case, assuming b=1 and dimension: (b,s,h,d))
; Assume V (N, d) is stored in HBM[V] (This case, assuming b=1 and dimension: (b,s,h,d))
; Assume O (N, d) is stored in HBM[O] (This case, assuming b=1 and dimension: (b,s,h,d))
; Assume m_curr ([1:Br+1]) is stored in FP_SRAM[m_curr:m_curr+Br]
; Assume m_last ([1:Br+1]) is stored in FP_SRAM[m_last:m_last+Br]
; Assume l ([1:Br+1]) is stored in FP_SRAM[l:l+Br]
; Assume o_scale ([1:Br+1]) is stored in FP_SRAM[o:o+Br]

; Assume Q value is directly stored in ADR[Q]
; Assume K value is directly stored in ADR[K]
; Assume V value is directly stored in ADR[V]
; Assume O value is directly stored in ADR[O]
; Br = BLEN, Bc = BLEN

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

S_ADDI_FIX x7, x0, Br * d * h;
C_SET_STRIDE_REG x7;

S_ADDI_FIX x1, x0, 0;           set FIX[1] to 0, use it as an incremental pointer (loop index) across N/Br
; LOOP N / Br
    S_ADDI_FIX x2, x0, 0;             set FIX[2] to 0, use it as an incremental pointer (loop index) across N/Bc
    ; LOOP N / Bc
        S_ADDI_FIX x8, x0, 0;             set FIX[8] to 0, use it as an incremental pointer (loop index) across MLEN/BLEN
        ; LOOP across buffer location             
            S_ADDI_FIX x3, x0, 0;               set FIX[3] to 0, use it as an incremental pointer (loop index) across d/MLEN
            ; LOOP across d/MLEN
                S_ADDI_FIX x4, x3, MLEN;            set FIX[4] to x3 * MLEN, use it to store start offset for different Q blocks arocss embedding dimension
                S_ADDI_FIX x5, x3, MLEN;            set FIX[5] to x3 * MLEN, use it to store start offset for different K blocks arocss embedding dimension

                S_ADDI_FIX x6, x0, 1;               set FIX[6] to 1, use as pointer to the beginning M_SRAM, V_SRAM location
                
                ; compute address of Q/K blocks
                S_ADDI_FIX x7, x0, Br * d * h;          Br * d * h
                S_MUL_FIX  x7, x1, x7;                  x7 = r * (Br * d * h)
                S_ADDI_FIX x4, x4, x7;                  x4 = x4 + x7

                S_ADDI_FIX x7, x0, Bc * d * h;          Bc * d * h
                S_MUL_FIX  x7, x2, x7;                  x7 = c * (Bc * d * h)
                S_ADDI_FIX x5, x5, x7;                  x4 = x4 + x7

                ; if x3 != d/MLEN - 1: Not the last loop
                H_PREFETCH_V_S x6, x4, ADR[Q]
                H_PREFETCH_M_S x6, x5, ADR[K]
                M_MM_IC x6, x6, 0
                S_ADDI_FIX x3, x3, 1;
                ; if x3 == d/MLEN - 1: Not the last loop
                ; H_PREFETCH_V_S x6, x4, ADR[Q]
                ; H_PREFETCH_M_S x6, x5, ADR[K]
                M_MM_PS x8, x6, x6, 
                ; - opcode rd, rs1, rs2;
            S_ADDI_FIX x8, x0, 1;
            
        M_MM_WO 0, 0, x6;
        ; x3, x8 free now

        ; Compute the row max of all the S
        S_ADDI_FIX x4, x0, 1;              set x4 to 1, use it to index register
        S_ADDI_FIX x7, x0, 1;              set x7 to 1, use it to index FP RAM
        ; LOOP Br;
            V_RED_MAX x0, x4, x6;               perform reduce and store it in REG[1]
            S_ST_FP m_curr, x7, x4;             perform store REG[1] to FP[x7]

            S_ADDI_FIX x6, x6, MLEN;            next row address in V_RAM
            S_ADDI_FIX x7, x7, 1;               next FP address
        

        ; Compute online softmax
        S_ADDI_FIX x7, x0, 0;               set FIX[7] to 0, use it as an incremental pointer (loop index) across #Br of scaler

        S_ADDI_FIX x3, x0, 1;               set x3 to 1, use it to point to the beginning of computed S in V_RAM
        S_ADDI_FIX x4, x0, 1;               set x4 to 1, use it to store m_curr
        S_ADDI_FIX x5, x4, 1;               set x5 to 2, use it to store m_last
        S_ADDI_FIX x6, x5, 1;               set x6 to 3, use it to store p_sum
        S_ADDI_FIX x8, x6, 1;               set x6 to 4, use it to store l
        ; LOOP Br;
            S_LD_FP m_curr, x7, x4;             load curr m to x4 (loc: REG[1])
            S_LD_FP m_last, x7, x5;             load last m to x5 (loc: REG[2])
            S_MAX_FP x5, x4, x4;                x4 (m_new) = max(m_curr, m_last)
            S_SUB_FP x5, x4, x5;                x5 (m_res) = max(m_last, x4)

            V_SUB_VF x4, x3, x3;                x7 (s_j_shifted) = x7 (row) - x4 (m_new)
            V_EXP_V  0, x3, x3;                 x7 (p) = torch.exp(x7 (s_j_shifted))
            V_RED_SUM x0, x3, x6;               x6 (p_sum) = x7.sum (p.sum())

            S_EXP_FP 0, x5, x5;                 x5 (l_scale/o_scale) = exp(x5 (m_res))
            S_LD_FP l, x7, x8;                  load l to x8
            S_MUL_FP x8, x5, x8;                x8 (l_inter) = x5 (l_scale) * x8 (l)
            S_ADD_FP x8, x6, x8;                x8 (l_new) =  x8 (l_inter) + x5 (p_sum)

            S_ST_FP m_last, x7, x4;             store m_new to m_last
            S_ST_FP l, x7, x8;                  store l_new to l
            S_ST_FP o_scale, x7, x5;            store o_scale to o_scale

            S_ADDI_FIX x3, x3, Bc;              next vector
            S_ADDI_FIX x7, x7, 1;               next scaler
        
        ; Multiplying with V
        ; compute sequence address of V      
        S_ADDI_FIX  x7, x0, 0;                   x7 = 0
        S_ACC_MULI_FIX Bc * d * h, x2, x7;      x7 = x2 * (Bc * d * h)


        S_ADDI_FIX x5, x0, 1;               Point to P in V_RAM and V in S_RAM
        S_ADDI_FIX x3, x0, 0;               set FIX[3] to 0, use it as an incremental pointer (loop index) across  N/ MLEN;
        ; LOOP N/ MLEN;
            S_ADDI_FIX x7, x0, 0;
            S_ACC_MULI_FIX MLNE, x3, x7;
            ; LOOP across buffer location (MLEN / BLEN)
                S_ADDI_FIX x7, x7, BLEN;            set FIX[7] to (c * (Bc * d * h)) + BLEN, use it to store start offset for different V blocks
                H_PREFETCH_M_S x5, x7, ADR[V];      (Load MLEN by BLEN V at each loop)
                ; if not the last loop
                M_MM_IC x5, x5, 0;                  x5 (p@v) = x5 (P loc:V_RAM) @ x5 (V loc:M_RAM)
                ; if the last loop
                M_MM_PS x5, x5, 0;
            
            S_ADDI_FIX x3, x3, 1;

            ; Compute address to load O from HBM
            S_ADDI_FIX x7, x0, 0;
            S_ACC_MULI_FIX BLEN * MLEN, x3, x7;     
            H_PREFETCH_S x4, x7, ADR[O];       load previous O matrix (BLEN by MLEN) (x4 loc: V_RAM)

            S_ADDI_FIX x7, x0, 0;               use this to index row
            ; LOOP Br;
                ; if x2 != N/Bc:
                S_LD_FP o_scale, x7, x8;    load o_scale to x8
                V_MUL_VF x8, x4, x4;        x4 = x8 (o_scale) * x4(O)      
                V_ADD_VV x5, x4, x5;        x5 = x4 (o_scale * O) + x5 (p@v)   
                ; compute O store address ADR[O] based on x1, x2
                S_MULI_FIX x8, x1, Br * h * d;
                S_ACC_MULI h * d, x7, x8;
                S_ACC_MULI MLEN, x6, x8;
                H_STORE_V_H_C ADR[O], x8, x5;

                ; if x2 == N/Bc:
                ; NOTE: TODO : Flash attention 2 line 12. Load all O back and scale all of them?
                S_LD_FP o_scale, x7, x8;    load o_scale to x8
                V_MUL_VF x8, x4, x4;        x4 = x8 (o_scale) * x4(O)      
                V_ADD_VV x5, x4, x5;        x5 = x4 (o_scale * O) + x5 (p@v)   

                S_LD_FP l, x7, x8;          load l to x8
                S_REC_FP x8;            
                V_MUL_VF x5, x8, x5;        x5 = x8 (1/l) * x5(O)  
                ; compute O store address ADR[O] based on x1, x2
                S_MULI_FIX x8, x1, Br * h * d;
                S_MULI_ACC_FIX x8, x7, h * d;
                S_MULI_ACC_FIX x8, x6, MLEN;
                H_STORE_V_H_C ADR[O], x8, x5;



                S_ADDI_FIX x3, x3, 1;
                S_ADDI_FIX x7, x7, Bc;
                S_ADDI_FIX x6, x6, Bc;

            S_ADDI_FIX x4, x4, Bc * Bc;

    S_ADDI_FIX x2, x2, 1;
S_ADDI_FIX x1, x1, 1; 
