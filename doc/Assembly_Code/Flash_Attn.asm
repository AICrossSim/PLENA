// <-------------------- FlashAttention ------------------------>
    LOOP_ATTENTION_Q_HEADS:
        lui x2, ; (index of in q head // num_head_groups)
        lui x3, head_dim;
        mul x4, x2, x3;                memory offset to csr_adr[3].
        lui x5, Tc;
        lui x6, Bc;
        LOOP_ATTENTION_PER_HEAD:
            mv x7, x0;                      x7 stores the address in MVM SRAM
            mv x8, x0;                      x8 stores the address for sequence_index in HBM
            mv x9, x0;                      x9 stores the address offset in HBM
            lui x12, 0x0;                   ith tile in the matrix
            // Fetching K of ((Bc), specified_idx, head_dim) from HBM () to MVM SRAM
            LOOP_Bc:
                mv          x9, x8;
                addi        x9, x9, x4;
                m.fetch     x7, x9, csr_adr[3];
                addi        x8, x8, head_dim * num_key_value_heads;
                addi        x7, x7, head_dim;
                addi        x12, x12, 0x1;
                blt         x12, x6, LOOP_Bc;

            // Fetching Q from SSRAM (1, head_dim) and Q @ K^T (Bc, head_dim)
            mv x7, x0;                      x7 stores the address in MVM SRAM
            lui x12, 0x0;                   ith tile in the matrix
            lui x13, Num_of_Tiles_Head; 
            LOOP_MLEN_MATRIX:
                m.mv x7, x12, x11;
                addi x7, x7, MLEN;
                addi x12, x12, 0x1;
                blt x12, x13, LOOP_MLEN_MATRIX;
            m.extract x13;

            // s_j = q @ k_j.transpose(1, 2) * qk_scale
            lui x12, 0x0;                   ith tile in the matrix
            lui x13, Num_of_Tiles_Head; 
            lui f2, qk_scale;
            LOOP_MLEN_VECTOR:
                v.lv v1, x13, 0;
                v.fmul.vf v2, v1, f2;
                v.fredmax v3, v3, v2;
                v.sv v2, x13, 0;
                addi x13, x13, MLEN;

            // rowmax_s_j = s_j.max().cpu().item()
            v.fmv.f.s f2, v3;             Storing the max value of s_j in x2 Note, storing results to floating type registers.
            lui x3, (memory to store previous m);
            ld f1, x3, 0;
            fmax.s f1, f1, f2;