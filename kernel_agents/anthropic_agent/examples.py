"""Assembly code examples for PLENA kernel generation."""

LINEAR_PROJECTION_EXAMPLE = """\
; Linear Test with Loop Instructions, batch size of 4, hidden size of 128
; Preload Addr Reg Generation
S_ADDI_INT gp1, gp0, 2304
C_SET_ADDR_REG a1, gp0, gp1
S_LUI_INT gp2, 1153
S_ADDI_INT gp2, gp2, 2
C_SET_ADDR_REG a2, gp0, gp2
; Reset Registers [[1, 2, 3]]
S_ADDI_INT gp1, gp0, 0
S_ADDI_INT gp2, gp0, 0
S_ADDI_INT gp3, gp0, 0
; Preload Activation Generation
S_ADDI_INT gp1, gp0, 512
C_SET_SCALE_REG gp1
S_ADDI_INT gp1, gp0, 0
S_ADDI_INT gp3, gp0, 0
S_ADDI_INT gp2, gp0, 2048
C_SET_STRIDE_REG gp2
C_LOOP_START gp4, 2
S_ADDI_INT gp2, gp1, 0
H_PREFETCH_V gp3, gp2, a0, 1, 0
S_ADDI_INT gp3, gp3, 256
S_ADDI_INT gp1, gp1, 64
C_LOOP_END gp4
; Reset Registers [[1, 2, 3, 4, 5, 6, 7]]
S_ADDI_INT gp1, gp0, 0
S_ADDI_INT gp2, gp0, 0
S_ADDI_INT gp3, gp0, 0
S_ADDI_INT gp4, gp0, 0
S_ADDI_INT gp5, gp0, 0
S_ADDI_INT gp6, gp0, 0
S_ADDI_INT gp7, gp0, 0
; Projection Generation (Loop-Optimized)
S_ADDI_INT gp4, gp0, 16384
C_SET_SCALE_REG gp4
S_ADDI_INT gp4, gp0, 128
C_SET_STRIDE_REG gp4
S_ADDI_INT gp4, gp0, 0
S_ADDI_INT gp1, gp0, 2048
S_ADDI_INT gp3, gp0, 0
; Outer loop: 2 MLEN blocks
C_LOOP_START gp5, 2
S_ADDI_INT gp2, gp0, 0
H_PREFETCH_M gp2, gp3, a1, 1, 0
S_ADDI_INT gp3, gp3, 8192
S_ADDI_INT gp2, gp2, 4096
H_PREFETCH_M gp2, gp3, a1, 1, 0
S_ADDI_INT gp7, gp0, 0
; Middle loop: 16 iterations (unroll=1)
C_LOOP_START gp6, 16
M_MM 0, gp7, gp4
S_ADDI_INT gp2, gp7, 4096
S_ADDI_INT gp4, gp4, 256
M_MM 0, gp2, gp4
M_MM_WO 1, gp0, 0
S_ADDI_INT gp1, gp1, 4
S_ADDI_INT gp7, gp7, 4
S_ADDI_INT gp4, gp0, 0
C_LOOP_END gp6
S_ADDI_INT gp1, gp1, 192
S_ADDI_INT gp7, gp0, 8128
S_SUB_INT gp3, gp3, gp7
C_LOOP_END gp5
"""
