; FFN Test Generation 
; Preload Addr Reg Generation 
S_ADDI_INT gp1, gp0, 1152 
C_SET_ADDR_REG a1, gp0, gp1 
S_ADDI_INT gp2, gp0, 38016 
C_SET_ADDR_REG a2, gp0, gp2 
S_ADDI_INT gp3, gp0, 74880 
C_SET_ADDR_REG a3, gp0, gp3 
; Reset Registers [[1, 2, 3]] 
S_ADDI_INT gp1, gp0, 0 
S_ADDI_INT gp2, gp0, 0 
S_ADDI_INT gp3, gp0, 0 
; Preload Activation Generation 
S_ADDI_INT gp1, gp0, 1024 
C_SET_SCALE_REG gp1 
S_ADDI_INT gp1, gp0, 0 
S_ADDI_INT gp3, gp0, 0 
S_ADDI_INT gp2, gp0, 128 
C_SET_STRIDE_REG gp2 
C_LOOP_START gp4, 2 
C_LOOP_START gp5, 2 
S_ADDI_INT gp2, gp1, 0 
H_PREFETCH_V gp3, gp2, a0, 1, 0 
S_ADDI_INT gp3, gp3, 256 
S_ADDI_INT gp2, gp2, 512 
C_LOOP_END gp5 
S_ADDI_INT gp1, gp1, 64 
C_LOOP_END gp4 
; FFN Generation (Loop-Optimized)
S_ADDI_INT gp1, gp0, 32768
C_SET_SCALE_REG gp1
S_ADDI_INT gp1, gp0, 256
C_SET_STRIDE_REG gp1
S_ADDI_INT gp1, gp0, 0
S_ADDI_INT gp4, gp0, 1024
S_ADDI_INT gp6, gp4, 2048
; FFN Upsize Linear Generation (Loop)
S_ADDI_INT gp7, gp0, 0
; Outer loop: 4 MLEN blocks
C_LOOP_START gp8, 4
S_ADDI_INT gp1, gp0, 0
S_ADDI_INT gp3, gp7, 0
H_PREFETCH_M gp1, gp3, a1, 1, 0
S_ADDI_INT gp1, gp1, 4096
S_ADDI_INT gp3, gp3, 16384
H_PREFETCH_M gp1, gp3, a1, 1, 0
S_ADDI_INT gp1, gp1, 4096
S_ADDI_INT gp3, gp3, 16384
S_ADDI_INT gp1, gp0, 0
S_ADDI_INT gp5, gp4, 0
; Middle loop: 16 tiles per MLEN block
C_LOOP_START gp9, 16
S_ADDI_INT gp3, gp0, 0
; Inner loop: 2 activation columns
C_LOOP_START gpa, 2
S_ADDI_INT gp2, gp1, 0
S_ADDI_INT gp6, gp3, 0
M_MM 0, gp2, gp3
S_ADDI_INT gp2, gp2, 4096
S_ADDI_INT gp3, gp3, 512
M_MM 0, gp2, gp3
S_ADDI_INT gp2, gp2, 4096
M_MM_WO gp5, gp0, 0
S_ADDI_INT gp5, gp5, 256
S_ADDI_INT gp3, gp6, 256
C_LOOP_END gpa
S_ADDI_INT gp1, gp1, 4
S_ADDI_INT gp5, gp4, 0
S_ADD_INT gp5, gp5, gp1
C_LOOP_END gp9
S_ADDI_INT gp7, gp7, 64
S_ADDI_INT gp4, gp4, 512
C_LOOP_END gp8
; FFN Gate Projection Generation (Loop)
S_ADDI_INT gp4, gp0, 1024
S_ADDI_INT gp6, gp4, 2048
S_ADDI_INT gp7, gp0, 0
; Outer loop: 4 MLEN blocks
C_LOOP_START gp8, 4
S_ADDI_INT gp1, gp0, 0
S_ADDI_INT gp3, gp7, 0
H_PREFETCH_M gp1, gp3, a2, 1, 0
S_ADDI_INT gp1, gp1, 4096
S_ADDI_INT gp3, gp3, 16384
H_PREFETCH_M gp1, gp3, a2, 1, 0
S_ADDI_INT gp1, gp1, 4096
S_ADDI_INT gp3, gp3, 16384
S_ADDI_INT gp1, gp0, 0
S_ADDI_INT gp5, gp6, 0
; Middle loop: 16 tiles per MLEN block
C_LOOP_START gp9, 16
S_ADDI_INT gp3, gp0, 0
; Inner loop: 2 activation columns
C_LOOP_START gpa, 2
S_ADDI_INT gp2, gp1, 0
S_ADDI_INT gp4, gp3, 0
M_MM 0, gp2, gp3
S_ADDI_INT gp2, gp2, 4096
S_ADDI_INT gp3, gp3, 512
M_MM 0, gp2, gp3
S_ADDI_INT gp2, gp2, 4096
M_MM_WO gp5, gp0, 0
S_ADDI_INT gp5, gp5, 256
S_ADDI_INT gp3, gp4, 256
C_LOOP_END gpa
S_ADDI_INT gp1, gp1, 4
S_ADDI_INT gp5, gp6, 0
S_ADD_INT gp5, gp5, gp1
C_LOOP_END gp9
S_ADDI_INT gp7, gp7, 64
S_ADDI_INT gp6, gp6, 512
C_LOOP_END gp8
; SILU Generation (Loop)
S_LD_FP f1, gp0, 1
S_ADDI_INT gp4, gp0, 1024
S_ADDI_INT gp6, gp4, 2048
S_ADDI_INT gp5, gp0, 0
; SILU loop: 32 iterations
C_LOOP_START gp8, 32
V_SUB_VF gp5, gp4, f0, 0, 1
V_EXP_V  gp5, gp5, 0
V_ADD_VF gp5, gp5, f1, 0
V_RECI_V  gp5, gp5, 0
V_MUL_VV gp5, gp5, gp4, 0
V_MUL_VV gp4, gp5, gp6, 0
S_ADDI_INT gp6, gp6, 64
S_ADDI_INT gp4, gp4, 64
C_LOOP_END gp8
; FFN Downsize Linear Generation (Loop)
S_ADDI_INT gp1, gp0, 32768
C_SET_SCALE_REG gp1
S_ADDI_INT gp1, gp0, 128
C_SET_STRIDE_REG gp1
S_ADDI_INT gp1, gp0, 0
S_ADDI_INT gp6, gp0, 0
S_ADDI_INT gp4, gp0, 1024
S_ADDI_INT gp7, gp0, 0
; Outer loop: 2 MLEN blocks
C_LOOP_START gp8, 2
S_ADDI_INT gp1, gp0, 0
S_ADDI_INT gp3, gp7, 0
H_PREFETCH_M gp1, gp3, a3, 1, 0
S_ADDI_INT gp1, gp1, 4096
S_ADDI_INT gp3, gp3, 8192
H_PREFETCH_M gp1, gp3, a3, 1, 0
S_ADDI_INT gp1, gp1, 4096
S_ADDI_INT gp3, gp3, 8192
H_PREFETCH_M gp1, gp3, a3, 1, 0
S_ADDI_INT gp1, gp1, 4096
S_ADDI_INT gp3, gp3, 8192
H_PREFETCH_M gp1, gp3, a3, 1, 0
S_ADDI_INT gp1, gp1, 4096
S_ADDI_INT gp3, gp3, 8192
S_ADDI_INT gp1, gp0, 0
S_ADDI_INT gp5, gp6, 0
; Middle loop: 16 tiles per MLEN block
C_LOOP_START gp9, 16
S_ADDI_INT gp4, gp0, 1024
S_ADDI_INT gp3, gp4, 0
; Inner loop: 2 activation columns
C_LOOP_START gpa, 2
S_ADDI_INT gp2, gp1, 0
S_ADDI_INT gp4, gp3, 0
M_MM 0, gp2, gp3
S_ADDI_INT gp2, gp2, 4096
S_ADDI_INT gp3, gp3, 512
M_MM 0, gp2, gp3
S_ADDI_INT gp2, gp2, 4096
S_ADDI_INT gp3, gp3, 512
M_MM 0, gp2, gp3
S_ADDI_INT gp2, gp2, 4096
S_ADDI_INT gp3, gp3, 512
M_MM 0, gp2, gp3
S_ADDI_INT gp2, gp2, 4096
M_MM_WO gp5, gp0, 0
S_ADDI_INT gp5, gp5, 256
S_ADDI_INT gp3, gp4, 256
C_LOOP_END gpa
S_ADDI_INT gp1, gp1, 4
S_ADDI_INT gp5, gp6, 0
S_ADD_INT gp5, gp5, gp1
C_LOOP_END gp9
S_ADDI_INT gp7, gp7, 64
S_ADDI_INT gp6, gp6, 512
C_LOOP_END gp8
