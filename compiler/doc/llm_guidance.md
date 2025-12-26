# LLM Guidance for PLENA Assembly Generation

This document provides guidance for LLMs generating PLENA assembly code for the custom LLM accelerator.

---

## System Prompt Starting Point

Use this as a foundation when prompting an LLM to generate PLENA assembly:

```
You are an expert PLENA assembly code generator for a custom Large Language Model accelerator.
Your goal is to produce correct, complete, efficient PLENA assembly kernels.

Before generating code, read the following documentation in this directory:
- compiler/doc/plena_isa_spec.md - Full ISA specification with instruction formats and semantics
- compiler/doc/memory_layout.md - HBM and SRAM memory layout conventions
- compiler/doc/llm_guidance.md - Common patterns, mistakes, and debugging tips

Key hardware parameters (from src/definitions/plena_settings.toml):
- MLEN=64: Matrix tile size
- BLEN=4: Systolic array tile size
- VLEN=64: Vector length
- HBM_V_Prefetch_Amount=4: Batch size for vector prefetch

You must:
- Generate optimized kernels (linear, projection, FFN, RMSNorm, attention)
- Use only instructions defined in the ISA specification
- Follow the memory layout conventions for data placement
- Understand the M_MM/M_MM_WO accumulation pattern (critical!)

Reference existing templates in compiler/asm_templates/ for working examples:
- projection_asm.py - Linear projection layer
- ffn_asm.py - Feed-forward network with SwiGLU
- flash_attn_asm.py - Flash attention implementation
```

---

## M_MM and M_MM_WO Accumulation Pattern

**This is the most common bug. Understanding this is essential for correct code.**

### How M_MM works:
- M_MM **ACCUMULATES** into the systolic array (does NOT overwrite)
- Multiple M_MM calls ADD to the same accumulator
- The accumulator is NOT cleared between M_MM calls

### How M_MM_WO works:
- M_MM_WO writes the accumulated result to Vector SRAM
- M_MM_WO **CLEARS** the accumulator after writing
- After M_MM_WO, the accumulator is reset to zero

### Correct pattern for matrix multiply Y = X @ W with K-dimension tiling:
```asm
; For each output column block (c):
;     For each K tile (k):        ; K accumulation loop
;         M_MM ...                ; Accumulate partial product for this K tile
;     M_MM_WO ...                 ; Write AFTER all K tiles accumulated
```

### WRONG pattern (clears accumulator too early):
```asm
; For each K tile (k):
;     For each output column block (c):
;         M_MM ...
;         M_MM_WO ...             ; WRONG! Clears before next K can accumulate!
```

### Example with K=2 tiles:
```asm
; CORRECT: Both K tiles accumulate, then write
M_MM 0, gp_weight_k0, gp_act_k0    ; Accumulate K=0
M_MM 0, gp_weight_k1, gp_act_k1    ; Accumulate K=1 (adds to K=0 result)
M_MM_WO gp_output, gp0, 0          ; Write complete result

; WRONG: Writing after each K clears the accumulator
M_MM 0, gp_weight_k0, gp_act_k0    ; Accumulate K=0
M_MM_WO gp_output, gp0, 0          ; Writes K=0 only, CLEARS accumulator!
M_MM 0, gp_weight_k1, gp_act_k1    ; K=1 starts fresh (K=0 lost!)
M_MM_WO gp_output, gp0, 0          ; Overwrites with K=1 only - WRONG RESULT!
```

---

## Assembly Syntax Rules

**Register operands MUST use register names, not bare integers.**
- Use `gp0`, `gp1`, ... `gp15` for general-purpose registers
- Use `f0`, `f1`, ... `f7` for floating-point registers
- Use `a0`, `a1`, ... `a7` for HBM address registers
- Even for register 0, write `gp0` NOT `0`

```asm
; WRONG
M_MM_WO gp8, 0, 0      ; "0" is not a valid register name!

; RIGHT
M_MM_WO gp8, gp0, 0    ; gp0 is correct
```

Immediates (imm) are plain integers. Only the IMM operand position takes integers.

---

## Common Mistakes to Avoid

### Register & Setup Errors:
- `gp0` is hardwired to 0. To multiply by a constant, load it into another register first.
- Address registers (`a0-a7`) must be initialized with `C_SET_ADDR_REG` before use in `H_PREFETCH`.
- `C_SET_SCALE_REG` must be called before `H_PREFETCH_M`, or data will be corrupted.
- Use register names (`gp0`, `gp1`) not bare integers (`0`, `1`) for register operands.

### Memory & Computation Errors:
- In-place operations overwrite data. Save to scratchpad first if you need the original later.
- M_MM accumulates into the systolic array. M_MM_WO writes the result AND clears it.
- Never put M_MM_WO inside the K-accumulation loop - it clears partial results too early.
- Unimplemented instructions (`M_BMV`, `M_BTMV`, `M_BMV_WO`, `H_STORE_V`) will crash the simulator.

### Workflow Errors:
- Do not generate code one instruction at a time or build up incrementally.
- Do not write incomplete kernels that only compute partial output.

---

## Debugging Tips

### Interpreting debug_view_memory Output:

When you see `sim_nonzero: N` in row analysis:
- N = number of non-zero values per row
- Expected: VLEN (64) non-zero values per output row
- If N << VLEN (e.g., N=4): you're only writing BLEN columns per output tile

**Common cause:** Missing loop over column blocks within output tile.
- M_MM_WO writes only BLEN x BLEN (4x4) elements per call
- For VLEN=64 output columns, need VLEN/BLEN = 16 M_MM_WO calls per tile
- Pattern: `sim_nonzero=4` means you have 1 M_MM_WO where you need 16

When you see `NaN` values in certain rows:
- NaN = reading uninitialized memory or address collision
- Check: Are output addresses unique? (no two M_MM_WO to same addr)
- Check: Are Matrix SRAM prefetch addresses < total SRAM size?
- Check: Is weight HBM offset correct? Wrong offset reads garbage -> NaN after computation
- Pattern: First rows OK, later rows NaN = loop index error causing address overflow

---

## Simulator Instruction Support

**The behavioral simulator does NOT support all ISA instructions.**

### IMPLEMENTED (safe to use):
- **Matrix:** M_MM, M_TMM, M_BMM, M_BTMM, M_MM_WO, M_BMM_WO, M_MV, M_TMV, M_MV_WO
- **Vector:** V_ADD_VV, V_ADD_VF, V_SUB_VV, V_SUB_VF, V_MUL_VV, V_MUL_VF, V_EXP_V, V_RECI_V, V_RED_SUM, V_RED_MAX
- **Scalar:** S_ADD_INT, S_ADDI_INT, S_SUB_INT, S_MUL_INT, S_LUI_INT, S_LD_INT, S_ST_INT
- **Scalar FP:** S_ADD_FP, S_SUB_FP, S_MUL_FP, S_MAX_FP, S_EXP_FP, S_RECI_FP, S_SQRT_FP, S_LD_FP, S_ST_FP, S_MAP_V_FP
- **Memory:** H_PREFETCH_M, H_PREFETCH_V
- **Control:** C_SET_ADDR_REG, C_SET_SCALE_REG, C_SET_STRIDE_REG, C_SET_V_MASK_REG, C_LOOP_START, C_LOOP_END, C_BREAK

### NOT IMPLEMENTED (DO NOT USE - will crash simulator):
- M_BMV, M_BTMV, M_BMV_WO
- H_STORE_V

Since H_STORE_V is not implemented, results must remain in Vector SRAM. The simulator will check Vector SRAM contents against golden reference.

---

## Layer-Specific Computation Guides

### Linear Layer

**Formula:** `Y = X @ W`

**Shapes:**
- X: [batch, input_dim]
- W: [input_dim, output_dim]
- Y: [batch, output_dim]

**Output:** Stored AFTER activations in VRAM.

---

### FFN (Feed-Forward Network) Layer

**Formula (SwiGLU):** `Y = down(SiLU(up(X)) * gate(X))`

Where SiLU(x) = x * sigmoid(x)

**Shapes:**
- X: [batch, hidden]
- W_up: [hidden, intermediate]
- W_gate: [hidden, intermediate]
- W_down: [intermediate, hidden]
- Y: [batch, hidden]

**5 Stages:**
1. up_out = X @ W_up (matrix multiply)
2. gate_out = X @ W_gate (matrix multiply)
3. silu_up = SiLU(up_out) (vector ops)
4. hidden = silu_up * gate_out (element-wise)
5. Y = hidden @ W_down (matrix multiply)

**HBM Layout:** 3 weight matrices stored sequentially after activations.

**Output:** Stored IN-PLACE at address 0.

---

### RMS Norm Layer

**Formula:** `Y = X * rsqrt(mean(X^2) + eps)`

**Shapes:**
- X: [batch, hidden]
- Y: [batch, hidden]

**Stages:**
1. Square elements: X^2
2. Reduce sum: sum(X^2)
3. Mean: sum / hidden_size
4. Add epsilon: mean + eps
5. Reciprocal sqrt: rsqrt
6. Scale: X * rsqrt

**Output:** IN-PLACE (overwrites input).

---

### SiLU Activation

**Formula:** `SiLU(x) = x * sigmoid(x) = x / (1 + exp(-x))`

**Shapes:**
- X: [batch, hidden]
- Y: [batch, hidden] (element-wise)

**Stages:**
1. Negate: -x
2. Exponential: exp(-x)
3. Add one: 1 + exp(-x)
4. Reciprocal: sigmoid = 1/(1 + exp(-x))
5. Multiply: x * sigmoid

**Output:** IN-PLACE (overwrites input).

---

### Softmax Layer

**Formula (Numerically Stable):** `softmax(x)_i = exp(x_i - max(x)) / sum(exp(x_j - max(x)))`

**Shapes:**
- X: [batch, hidden]
- Y: [batch, hidden] (values sum to 1 per batch)

**Stages:**
1. Find max: max(x) per batch
2. Subtract max: x - max (for stability)
3. Exponential: exp(x - max)
4. Sum: sum(exp(...))
5. Reciprocal: 1 / sum
6. Normalize: exp(...) * (1/sum)

**Output:** IN-PLACE (overwrites input).
