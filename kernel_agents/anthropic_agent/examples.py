"""Assembly code examples for PLENA kernel generation."""

# Linear projection: Y = X @ W
# X: [batch=4, hidden=128], W: [128, 128], Y: [4, 128]
# Tiling: MLEN=64, BLEN=4, VLEN=64
# K tiles: 128/64 = 2, Output tiles: 128/64 = 2, Column blocks per tile: 64/4 = 16
LINEAR_PROJECTION_EXAMPLE = """\
; =============================================================================
; Linear Projection: Y = X @ W
; X: [4, 128], W: [128, 128], Y: [4, 128]
; MLEN=64, BLEN=4, VLEN=64
; =============================================================================

; --- HBM Address Setup ---
; a0 = 0 (activations base, implicit)
; a1 = weight base = batch * hidden * 1.125 = 4 * 128 * 1.125 = 576
;      But this example uses precomputed value 2304 for different config
S_ADDI_INT gp1, gp0, 2304
C_SET_ADDR_REG a1, gp0, gp1
S_LUI_INT gp2, 1153
S_ADDI_INT gp2, gp2, 2
C_SET_ADDR_REG a2, gp0, gp2

; --- Reset working registers ---
S_ADDI_INT gp1, gp0, 0
S_ADDI_INT gp2, gp0, 0
S_ADDI_INT gp3, gp0, 0

; --- Preload Activations from HBM to Vector SRAM ---
; Scale = batch * hidden = 4 * 128 = 512 (for MXFP scale lookup)
S_ADDI_INT gp1, gp0, 512
C_SET_SCALE_REG gp1
S_ADDI_INT gp1, gp0, 0           ; HBM offset counter
S_ADDI_INT gp3, gp0, 0           ; VRAM destination
S_ADDI_INT gp2, gp0, 2048
C_SET_STRIDE_REG gp2
; Loop to prefetch activation tiles (2 tiles for hidden=128, VLEN=64)
C_LOOP_START gp4, 2
S_ADDI_INT gp2, gp1, 0
H_PREFETCH_V gp3, gp2, a0, 1, 0  ; VRAM[gp3] = HBM[a0 + gp2]
S_ADDI_INT gp3, gp3, 256         ; Next VRAM destination (+batch*VLEN = 4*64)
S_ADDI_INT gp1, gp1, 64          ; Next HBM offset (+VLEN)
C_LOOP_END gp4

; --- Reset registers for projection ---
S_ADDI_INT gp1, gp0, 0
S_ADDI_INT gp2, gp0, 0
S_ADDI_INT gp3, gp0, 0
S_ADDI_INT gp4, gp0, 0
S_ADDI_INT gp5, gp0, 0
S_ADDI_INT gp6, gp0, 0
S_ADDI_INT gp7, gp0, 0

; =============================================================================
; PROJECTION COMPUTE (Loop-Optimized)
; =============================================================================
; Scale = hidden * hidden = 128 * 128 = 16384 (for weight MXFP)
S_ADDI_INT gp4, gp0, 16384
C_SET_SCALE_REG gp4
; Stride = hidden = 128 (weight matrix stride)
S_ADDI_INT gp4, gp0, 128
C_SET_STRIDE_REG gp4
S_ADDI_INT gp4, gp0, 0           ; gp4 = activation VRAM pointer (starts at 0)
S_ADDI_INT gp1, gp0, 2048        ; gp1 = output VRAM base (after activations)
S_ADDI_INT gp3, gp0, 0           ; gp3 = weight HBM offset

; -----------------------------------------------------------------------------
; OUTER LOOP: Output column tiles (j = 0 to 1, since 128/64 = 2 MLEN blocks)
; -----------------------------------------------------------------------------
C_LOOP_START gp5, 2

; --- Prefetch ALL K tiles for this output tile BEFORE compute ---
; This loads weights for K=0 and K=1 into Matrix SRAM
; K=0 tile goes to MSRAM[0], K=1 tile goes to MSRAM[4096]
S_ADDI_INT gp2, gp0, 0           ; MSRAM dest for K=0
H_PREFETCH_M gp2, gp3, a1, 1, 0  ; Load weight tile K=0
S_ADDI_INT gp3, gp3, 8192        ; HBM offset += MLEN * stride = 64 * 128
S_ADDI_INT gp2, gp2, 4096        ; MSRAM dest for K=1 (+ MLEN^2)
H_PREFETCH_M gp2, gp3, a1, 1, 0  ; Load weight tile K=1
S_ADDI_INT gp7, gp0, 0           ; gp7 = weight MSRAM offset within tile

; -----------------------------------------------------------------------------
; MIDDLE LOOP: Column blocks within MLEN tile (c = 0 to 15, since 64/4 = 16)
; Each iteration produces BLEN=4 output columns
; -----------------------------------------------------------------------------
C_LOOP_START gp6, 16

; *** CRITICAL PATTERN: Accumulate ALL K tiles, THEN write ***
; M_MM accumulates into systolic array (does NOT clear)
; M_MM_WO writes result AND clears accumulator
; So: M_MM(K=0) → M_MM(K=1) → M_MM_WO (after all K accumulated)

; K=0 accumulation: systolic += Act[gp4] @ Weight[gp7]
M_MM 0, gp7, gp4
; K=1 accumulation: systolic += Act[gp4+256] @ Weight[gp7+4096]
S_ADDI_INT gp2, gp7, 4096        ; K=1 weight offset
S_ADDI_INT gp4, gp4, 256         ; K=1 activation offset (+ batch*VLEN)
M_MM 0, gp2, gp4

; NOW write result after ALL K tiles accumulated
M_MM_WO gp1, gp0, 0              ; Output[gp1] = systolic result, clears accumulator

; Advance pointers for next column block
S_ADDI_INT gp1, gp1, 4           ; Output += BLEN
S_ADDI_INT gp7, gp7, 4           ; Weight offset += BLEN (next column block)
S_ADDI_INT gp4, gp0, 0           ; Reset activation to base (reuse for next c)

C_LOOP_END gp6

; Advance for next output tile
S_ADDI_INT gp1, gp1, 192         ; Skip to next output tile region
S_ADDI_INT gp7, gp0, 8128
S_SUB_INT gp3, gp3, gp7          ; Adjust HBM offset for next tile

C_LOOP_END gp5
"""
