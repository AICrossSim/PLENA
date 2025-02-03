    addi x1, x0, (hidden_size / Tile_Size);      Storing the iteration amount required for the overall RMS Norm Computation.
    mv x3, x0;                              Storing the offset address for the section of embedded vector in HBM.
    v.fmul.vf v1, f0;                       Zero mapping v1
    v.fmul.vf v3, f0;                       Zero mapping v3

    LOOP_MLEN_VEC1:
        v.fetch x0, x3, csr_adr[8];
        v.lv v1, x0, 0;                     Loading vector data of Tile_Size stored in SRAM to vector reg v1;
        v.fmul.vv v2, v1, v1;
        v.fredsum v3, v3, v2;               v3[0] = v3[0] + sum(v2)
        addi x3, x3, Tile_Size;
        addi x1, x1, 0xFFF ;                counter, -1 every loop
        blt x0, x1, LOOP_MLEN_VEC1;
    
    v.fmv.f.s x3, v3;                       Storing v3[0] to x3
    lui x1, hidden_size;
    div x3, x3, x1;
    s.sqrt x3, x3;
    lui x1, epsilon;
    div x3, x1, x3;                         epsilon/rms
    
    addi x1, x0, (hidden_size / Tile_Size);       reset x1
    mv x3, x0; 

    LOOP_MLEN_VEC2:                         // Iteratively dividing embeddings by x3
        v.fetch x0, x3, csr_adr[8];
        v.lv v1, x0, 0;
        v.fdiv.vf v2, v1, x3;
        v.sv v2, x2, hidden_size;           Store back vector to the address starting from hidden_size
        addi x3, x3, Tile_Size; 
        addi x1, x1, 0xfff;                counter, -1 every loop
        blt x0, x1, LOOP_MLEN_VEC2;