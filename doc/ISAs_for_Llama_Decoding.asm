; Assume Dimension
; hidden_size = h = 4096
; num_hidden_layers = 32
; sequence_length = s_q = 1
; s_max = maximum sequence length supported = 256 ? To be confirmed.
; floating_type = FP8 = 8 bits
; fixed data_type = fixed8 = 8bits
; vocab_size = 128256
; intermediate_size: 14336
; max_position_embeddings: 131072
; 


; OFFSET:
; MEM_Region from csr_adr[0] + x0000_0000 to 0x6000_0000
; ( Weight for ith hidden layer Q, K, V, each cover hidden_size * hidden_size * 3 * FP8 = 0x3000000 )

; MEM_Region from csr_adr[1] + 0x0000_0000 to 0x0006_0000
; ( Offest for ith hidden layer Q, K, V, each cover hidden_size * 3 * 1 * FP8 = 0x3000 )

; MEM_Region from csr_adr[2] + 0x0000_0000 to 0xC_0000_0000
; ( Cached for ith hidden layer Q, K, V, each cover hidden_size * max_position_embeddings * 3 * FP8 = 0x30_0000)

; MEM_Region from csr_adr[3] + 0x0000_0000 to 0x1F50_0000
; (Embeddings, hidden_size * vocab_size * FP8 = 0x1F500000 )

; MEM_Region from csr_adr[4] + 0x1000
; (RoPE Weights, hidden_size * 1 * FP8 = 0x1000 )

; MEM_Region from csr_adr[5] + 0x0000_0000 to (SLEN)
; (MLP_Weights, each layer: hidden_size * intermediate_size * FP8 = 0x1000 )

; MEM_Region from TOKEN_ADDR
; MEM_Region from PC Start


// Single Head Case and Decoding Stage.........

// <-------------------- Embeddings ------------------------>
// Preparing the embedded data
lui x1, TOKEN_ADDR;
lw x2, x1, (ith token addr);                Load the token to be processed in decoding stage, assuming each token is in length log2(128256) appox 17 bit (TODO: Rounded to 32 bits or 4 Bytes)
slli x2, x2, 4;
mv x10, x0;                                 x5 stores the index of N hidden layers
v.fetch x5, x2, csr_adr[3];                 Fetch the corresponding embeddings according to (token_value) in the vocab library. Fetch the embedding and stored in the addr 0x00000 in SRAM as scratchpad.

LOOP_N_Layers: 

    // <--------------------RMS Norm------------------------>
    addi x1, x0, (hidden_size / MLEN);
    mv x2, x0;
    v.fmul.vf v1, x0;                       Zero mapping v1
    v.fmul.vf v3, x0;                       Zero mapping v3

    LOOP_MLEN_VEC1:
        v.lv v1, x2, 0;                     Loading vector data of MLEN stored in SRAM to vector reg v1;
        v.fmul.vv v2, v1, v1;
        v.fredsum v3, v3, v2;               v3[0] = v3[0] + sum(v2)
        addi x2, x2, MLEN;
        addi x1, x1, 0xFFF ;                counter, -1 every loop
        blt x0, x1, LOOP_MLEN_VEC1;
    
    v.fmv.f.s x3, v3;                       Storing v3[0] to x3
    lui x1, hidden_size;
    div x3, x3, x1;
    s.sqrt x3, x3;
    lui x1, epsilon;
    div x3, x1, x3;                         epsilon/rms
    
    addi x1, x0, (hidden_size / MLEN);       reset x1
    mv x2, x0;

    LOOP_MLEN_VEC2:                         // Iteratively dividing embeddings by x3
        v.lv v1, x2, 0;
        v.fdiv.vf v2, v1, x3;
        v.sv v2, x2, hidden_size;           Store back vector to the address starting from hidden_size
        addi x2, x2, MLEN; 
        addi x1, x1, 0xfff ;                counter, -1 every loop
        blt x0, x1, LOOP_MLEN_VEC2;

    

    // <-------------------- Projection ------------------------>

    lui x1, 3 * hidden_size; 
    lui x2, hidden_size;
    mul x2, x2, x10;
    mul x2, x2, x1;    Addr Offset to weights Q_i, K_i, V_i, 3 * hidden_size * hidden_size


    lui x3, max_position_embeddings;
    mul x3, x3, x10;
    mul x3, x3, x1; Addr Offset to cached Q_i, K_i, V_i, 3 * hidden_size * max_position_embeddings;
    addi x3, x3, s_index * hidden_size;

    mul x4, x10, x1; Addr Offset to offset Q_i, K_i, V_i, 3 * hidden_size

    lui x5, hidden_size;                        Address to embedded vector after RMSNorm in SRAMS
    addi x6, x5, hidden_size;                   Address to QKV offsets in SRAMS
    addi x7, x6, hidden_size;                   Address to MVM results in SRAMS

    addi x8, 0x3;                                  x8 is the index in {Q, K, V}

    LOOP_Q_K_V_PROJECT:
        slli x9, x8, hidden_size * hidden_size
        m.fetch x2, csr_adr[0];
        v.fetch x6, csr_adr[1];

        mv x11, x0;
        addi x1, x0, 3;
        LOOP_MLEN_MATRIX:
            slli, x15, x11, hidden_size; 
            addi x12, x5, x15;           Current tile addr for embedded vector
            addi x13, x6, x15;           Current tile addr for QKV offsets
            addi x14, x7, x15;           Current tile addr for MVM results
            m.mv x14, x11, x12, 0;         x11 th tiled matrix from SRAM multiplied with vector stored in x12 and store the computed results to x14.
            v.fadd.vv  x14, x14, x13; 
            addi x11, x11, 0x1;      
            blt x11, x1, LOOP_MLEN_MATRIX;
        
        v.store_to_bram x3, x7, csr_adr[2]; 

        addi x8, x8, 0xfff;
        blt x0, x8, LOOP_Q_K_V_PROJECT






    



    
