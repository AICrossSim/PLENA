; Assume Dimension
; hidden_size = 4096
; num_hidden_layers = 32
; floating_type = 8 bits
; data_type = 8bits
; vocab_size = 128256
; intermediate_size: 14336
; max_position_embeddings: 131072
; num_attention_heads = 32
; num_key_value_heads = 8
; num_head_groups = num_attention_heads / num_key_value_heads = 4
; head_dim = h_qkv = hidden_size // num_attention_heads = 128
; attention_bias = false

; Computation
; TileSize = 64
; Num_of_Tiles_Matrix = (hidden_size / TileSize)^2 = 4096
; Num_of_Tiles_Vector = hidden_size / TileSize = 64
; Num_of_Tiles_Head = head_dim / TileSize = 2
; epsilon = 1e-6
; Bc = TileSize = 64
; Tc = seq_len / TileSize




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
    addi x1, x0, (hidden_size / TileSize);
    mv x2, x0;
    v.fmul.vf v1, f0;                       Zero mapping v1
    v.fmul.vf v3, f0;                       Zero mapping v3

    LOOP_TILE_VEC1:
        v.lv v1, x2, 0;                     Loading vector data of TileSize stored in SRAM to vector reg v1;
        v.fmul.vv v2, v1, v1;
        v.fredsum v3, v3, v2;               v3[0] = v3[0] + sum(v2)
        addi x2, x2, TileSize;
        addi x1, x1, 0xFFF ;                counter, -1 every loop
        blt x0, x1, LOOP_TILE_VEC1;
    
    v.fmv.f.s x3, v3;                       Storing v3[0] to x3
    lui x1, hidden_size;
    div x3, x3, x1;
    s.sqrt x3, x3;
    lui x1, epsilon;
    div x3, x1, x3;                         epsilon/rms
    
    addi x1, x0, (hidden_size / TileSize);       reset x1
    mv x2, x0;

    LOOP_TILE_VEC2:                         // Iteratively dividing embeddings by x3
        v.lv v1, x2, 0;
        v.fdiv.vf v2, v1, x3;
        v.sv v2, x2, hidden_size;           Store back vector to the address starting from hidden_size
        addi x2, x2, TileSize; 
        addi x1, x1, 0xfff;                counter, -1 every loop
        blt x0, x1, LOOP_TILE_VEC2;


    // <-------------------- Projection ------------------------>
    // ## 1. Q Projection:
    lui x1, hidden_size;            Storing the address for embeddings in SSRAM.
    add x3, x1, x1;                 Storing the offset q_new in SSRAM.
    m.fetch x0, csr_adr[0];         Fetch the Q weights from HBM to MVM SRAM.
    mul x2, x1, x2;                 Storing the address for Q offsets in HBM.
    v.fetch x3, x2, csr_adr[1];     Fetch the Q offsets from HBM to SSRAM.
    add x4, x3, x2;                 Storing the address for q_new in SSRAM.
    
    lui x5, Num_of_Tiles_Matrix;                  
    lui x6, hidden_size;
    lui x7, TileSize;                   TILE_SIZE
    mv x8, x1;                      Current tile addr for embedded vector in SSRAM
    mv x9, x0;                      Current tile addr for MVM results in accumulator
    lui x11, 0x0;                   ith tile in the matrix
    
    // MVM
    LOOP_TILE_MATRIX:
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
        blt x11, x5, LOOP_TILE_MATRIX;
    m.extract x4;

    // Add the bias
    lui x5, hidden_size;
    LOOP_TILE_VECTOR:
        v.lv v1, x4, 0;
        v.lv v2, x3, 0;
        v.fadd.vv v1, v1, v2;
        v.sv v1, x4, 0;
        addi x4, x4, TileSize;
        addi x3, x3, TileSize;
        addi x5, x5, 0xfff;
        blt x0, x5, LOOP_TILE_VECTOR;
    
    // RoPE Assuming qnew with shape (s_q, heads, head_dim), x3 to store the result after RoPE
    v.fetch x4, csr_addr[6];            Fetch the RoPE weights from HBM to MVM SRAM. (head_dim * 2, [cos, sin, else])
    addi x10, x4, 2* head_dim;           Storing the address for rotated_q;
    mv x11, x3;                          Storing the address for q_new in SSRAM;

    lui x5, num_attention_heads;
    LOOP_NUM_HEAD:
        // Apply RoPE to each head
        mv x6, x4;                  Current tile addr for cos RoPE weights in SSRAM 
        addi x8, x4, head_dim;      
        mv x8, x4;                  Current tile addr for sin RoPE weights in SSRAM
        lui x7, (head_dim/TileSize);    Counter for RoPE 

        // Prepare the rotated_q
        //if TileSize == head_dim: vector masking is introduced, or vslidedown.vx,
        //Storing rotated_q (1, num_attention_heads * head_dim) in x10
        
        LOOP_TILE_VECTOR_IN_HEAD:
            // assuming head_dim | TileSize
            // cos[i : i + TileSize] * q[i : i + TileSize]
            v.lv v1, x6, 0; cos
            v.lv v2, x4, 0;
            v.fmul.vv v3, v1, v2;
            // sin[i : i + TileSize] * rotated_q[i : i + TileSize]
            v.lv v1, x8, 0; sin
            v.lv v2, x10, 0; rotated_q
            v.fmul v4, v1, v2;
            v.fadd.vv v3, v3, v4;
            v.lv 
            v.sv x3, v3, 0;
            addi x6, x6, TileSize;
            addi x8, x8, TileSize;
            addi x4, x4, TileSize;
            addi x3, x3, TileSize;
            addi x7, x7, 0xfff;
            blt x0, x7, LOOP_TILE_VECTOR_IN_HEAD;


    // ## 2. K Projection (Similar to Q Projection, but the weight dimension changes to (hidden_size, (head_dim * num_key_value_heads)))
    // Storing the k_new into HBM, kv_cache
    mv x3, x11;
    mv x4, x0;
    lui x5, Num_of_Tiles_Matrix;
    LOOP_TILE_VECTOR:
        v.store_to_hbm x3, x4, csr_adr[3];
        addi x3, x3, TileSize;
        addi x4, x4, TileSize;
        addi x5, x5, 0xfff;
        blt x0, x5, LOOP_TILE_VECTOR;

    
    // ## 3. V Projection (Similar to K Projection, but without RoPE)

    mv x1, x0;                      x1 stores the index of in q head
    // <-------------------- FlashAttention ------------------------>
    lw x10, ; (s_num)
    mv x11, ;  address for q_new (1, num_attention_heads, head_dim) in SSRAM
    addi x13, x11, head_dim * num_attention_heads;  address for s (1, Bc) in SSRAM

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
            LOOP_TILE_MATRIX:
                m.mv x7, x12, x11;
                addi x7, x7, TileSize;
                addi x12, x12, 0x1;
                blt x12, x13, LOOP_TILE_MATRIX;
            m.extract x13;

            // s_j = q @ k_j.transpose(1, 2) * qk_scale
            lui x12, 0x0;                   ith tile in the matrix
            lui x13, Num_of_Tiles_Head; 
            lui f2, qk_scale;
            LOOP_TILE_VECTOR:
                v.lv v1, x13, 0;
                v.fmul.vf v2, v1, f2;
                v.fredmax v3, v3, v2;
                v.sv v2, x13, 0;
                addi x13, x13, TileSize;

            // rowmax_s_j = s_j.max().cpu().item()
            v.fmv.f.s f2, v3;             Storing the max value of s_j in x2 Note, storing results to floating type registers.
            lui x3, (memory to store previous m);
            ld f1, x3, 0;
            fmax.s f1, f1, f2;

            


            
                

            
        
        

            



        


    // <-------------------- Residual ------------------------>


    // <-------------------- LayerNorm ------------------------>


    // <-------------------- MLP ------------------------>


    // <-------------------- Residual ------------------------>


    // <--------------------CSR_Addr Settings------------------------>
    c.addi csr_addr[0], csr_addr[0], hidden_size * (head_dim * num_attention_heads + 1);
    c.addi csr_addr[1], csr_addr[1], hidden_size * (head_dim * num_key_value_heads + 1); 
    c.addi csr_addr[2], csr_addr[2], hidden_size * (head_dim * num_key_value_heads + 1);
    c.addi csr_addr[3], csr_addr[3], hidden_size * max_position_embeddings;
    c.addi csr_addr[4], csr_addr[4], hidden_size * max_position_embeddings;


    



    
