// <-------------------- Projection ------------------------>
// ## 1. Q Projection:                
lui x5, Num_of_Tiles_Matrix;   counter for the MVM loop               
lui x6, hidden_size;
mv x8, x0;                      Current tile addr for embedded vector in SSRAM
mv x9, x0;                      Current tile addr for MVM results in accumulator
mv x11, x0;                   size of the tile, address increment.

// MVM
LOOP_MLEN_MATRIX:
    beq x9, x6, RESET_VECTOR_ADDR;
    j   WITHOUT_RESET_VECTOR_ADDR;
    RESET_VECTOR_ADDR:
        mv x8, x0;                      Current tile addr for embedded vector in SSRAM
        mv x9, x0;                      Current tile addr for MVM results in accumulator
        j   END_VECTOR_ADDR;
    WITHOUT_RESET_VECTOR_ADDR:
        addi x8, x8, Tile_Size;           Current tile addr for embedded vector in SSRAM
        addi x9, x9, Tile_Size;           Current tile addr for MVM results in accumulator
    END_VECTOR_ADDR:
        m.fetch x11, csr_adr[0];    Fetch the weight for ith hidden layer Q from HBM to MVM SRAM
        v.fetch x0, x8, csr_adr[8];    Fetch the embedded vector from HBM to MVM SRAM
        m.mv x9, x0;  
    addi x11, x11, Tile_Size * Tile_Size;            Storing the address for the next tile in MVM SRAM
    addi x5, x5, 0xfff;                              Counter for MVM
    blt x0, x5, LOOP_MLEN_MATRIX;
v.store_acc_to_hbm x0, x6, csr_adr[0];            Store the MVM results in accumulator back to HBM.

// RoPE Assuming qnew with shape (s_q, heads, Head_Dim), x3 to store the result after RoPE
lui x1, (Head_Dim/Tile_Size);                          Counter for loading RoPE weights from HBM to MVM SRAM
lui x2, NUM_Tiles_Per_Head_Dim;
mv x4, x0;                          Storing the address for RoPE Sin weights in SSRAM;
lui x5, Head_Dim;                          Storing the address for RoPE Cos weights in SSRAM;
// Loading RoPE weights from HBM to MVM SRAM
LOOP_TILE_VECTOR_IN_HEAD:
        v.fetch x4, csr_addr[6];            Fetch the RoPE weights from HBM to MVM SRAM. (Head_Dim * 2, [cos, sin, else])
        v.fetch x5, csr_addr[6];            Fetch the RoPE weights from HBM to MVM SRAM. (Head_Dim * 2, [cos, sin, else])
        addi x4, x4, Tile_Size;             Storing the address for the next tile in MVM SRAM
        addi x1, x1, 0xfff;                  Counter for RoPE
        blt x0, x1, LOOP_TILE_VECTOR_IN_HEAD;

addi x11, x4, 3 * Head_Dim;           Storing the address for q_projected and q_roped in SSRAM;
addi x10, x4, 3 * Head_Dim;           Storing the address for rotated_q;

mv x12, x0;                          Storing the offset address for q_projected in HBM;
mv x13, x0;                          Storing the offset address for q_roped in HBM;

LOOP_NUM_HEAD:
    // Apply RoPE to each head
    mv x6, x4;                  Current tile addr for cos RoPE weights in SSRAM 
    addi x8, x4, Head_Dim;      
    mv x8, x4;                  Current tile addr for sin RoPE weights in SSRAM
    lui x7, (Head_Dim/Tile_Size);    Counter for RoPE 

    // Prepare the rotated_q
    //if Tile_Size == Head_Dim: vector masking is introduced, or vslidedown.vx,
    //Storing rotated_q (1, num_attention_heads * Head_Dim) in x10
    // Depending on the Tile_Size, estimated to take 3-5 instructions.
    // Storing to csr_adr[9] in HBM
    
    LOOP_TILE_VECTOR_IN_HEAD:
        // assuming Head_Dim | Tile_Size
        // cos[i : i + Tile_Size] * q[i : i + Tile_Size]
        v.fetch x11, x12, csr_adr[8]; q_projected
        v.lv v1, x6, 0; cos
        v.lv v2, x11, 0; q_projected
        v.fmul.vv v3, v1, v2;
        // sin[i : i + Tile_Size] * rotated_q[i : i + Tile_Size]
        v.fetch x10, x13, csr_adr[9]; q_roped
        v.lv v1, x8, 0; sin
        v.lv v2, x10, 0; rotated_q
        v.fmul v4, v1, v2;
        v.fadd.vv v3, v3, v4;
        v.sv x12, v3, csr_adr[8];
        addi x6, x6, Tile_Size;
        addi x8, x8, Tile_Size;
        addi x12, x12, Tile_Size;
        addi x13, x13, Tile_Size;
        //
        addi x7, x7, 0xfff;
        blt x0, x7, LOOP_MLEN_VECTOR_IN_HEAD;

