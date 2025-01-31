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
; num_attention_heads = 32
; num_key_value_heads = 8
; head_dim = h_qkv = config.hidden_size // config.num_attention_heads = 128
; attention_bias = false

; Computation
; MLEN = 128
; Num_of_Tiles_Matrix = (hidden_size / MLEN)^2 = 1024
; Num_of_Tiles_Vector = hidden_size / MLEN = 32
; epsilon = 1e-6



// Decoding Stage.........

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
        addi x1, x1, 0xfff;                counter, -1 every loop
        blt x0, x1, LOOP_MLEN_VEC2;


    // <-------------------- Projection ------------------------>
    // ## Q Projection:
    lui x1, hidden_size;            Storing the address for embeddings in SSRAM.
    lui x2, head_dim * num_attention_heads
    add x3, x2, x1;                 Storing the offset q_new in SSRAM.
    m.fetch x0, csr_adr[0];         Fetch the Q weights from HBM to MVM SRAM.
    mul x2, x1, x2;                 Storing the address for Q offsets in HBM.
    v.fetch x3, x2, csr_adr[1];     Fetch the Q offsets from HBM to SSRAM.
    add x4, x3, x1;                 Storing the address for q_new in SSRAM.
    
    lui x5, Num_of_Tiles_Matrix;                  
    lui x6, hidden_size;
    lui x7, MLEN;                   TILE_SIZE
    mv x8, x1;                      Current tile addr for embedded vector in SSRAM
    mv x9, x0;                      Current tile addr for MVM results in accumulator
    lui x11, 0x0;                   ith tile in the matrix
    // MVM
    LOOP_MLEN_MATRIX:
        beq x9, x6, RESET_VECTOR_ADDR;
        j   WITHOUT_RESET_VECTOR_ADDR;
        RESET_VECTOR_ADDR:
            mv x8, x1;                      Current tile addr for embedded vector in SSRAM
            mv x9, x0;                      Current tile addr for MVM results in accumulator
            j   END_VECTOR_ADDR;
        WITHOUT_RESET_VECTOR_ADDR:
            addi x8, x8, x7;           Current tile addr for embedded vector in SSRAM
            addi x9, x9, x7;           Current tile addr for MVM results in accumulator
        END_VECTOR_ADDR:
            m.mv x9, x11, x8; 
        addi x11, x11, 0x1;      
        blt x11, x5, LOOP_MLEN_MATRIX;
    m.extract x4;
    // Add the bias
    lui x5, hidden_size;
    LOOP_MLEN_VECTOR:
        v.lv v1, x4, 0;
        v.lv v2, x3, 0;
        v.fadd.vv v1, v1, v2;
        v.sv v1, x4, 0;
        addi x4, x4, MLEN;
        addi x3, x3, MLEN;
    
    // RoPE

    




    // <-------------------- FlashAttention ------------------------>



    // <--------------------CSR_Addr Settings------------------------>
    c.addi csr_addr[0], csr_addr[0], hidden_size * (head_dim * num_attention_heads + 1);
    c.addi csr_addr[1], csr_addr[1], hidden_size * (head_dim * num_key_value_heads + 1); 
    c.addi csr_addr[2], csr_addr[2], hidden_size * (head_dim * num_key_value_heads + 1);
    c.addi csr_addr[3], csr_addr[3], hidden_size * max_position_embeddings;
    c.addi csr_addr[4], csr_addr[4], hidden_size * max_position_embeddings;


    



    
