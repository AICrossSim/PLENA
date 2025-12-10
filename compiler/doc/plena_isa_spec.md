# PLENA Instruction Set Architecture (ISA) Specification

## Register Types

The PLENA architecture supports four types of registers:

- **gp_reg** (`gp0` to `gp15`): General-purpose integer registers
- **fp_reg** (`f0` to `f7`): Floating-point registers
- **hbm_addr_reg** (`a0` to `a7`): HBM address registers

## Assembly Syntax

Instructions are written with the opcode followed by a space, then comma-separated operands:

```
OPCODE operand1, operand2, operand3, ...
```

**Register naming conventions:**
- General-purpose registers: `gp0`, `gp1`, ..., `gp15`
- Floating-point registers: `f0`, `f1`, ..., `f7`
- HBM address registers: `a0`, `a1`, ..., `a7`

**Example:**
```asm
S_ADDI_INT gp1, gp0, 128    ; gp1 = gp0 + 128
M_MM 0, gp2, gp4            ; Matrix multiply using Vector[gp2] and Matrix[gp4]
```

## Instruction Format

Instructions follow one of the following encoding formats:

| Format | Operands | Used By |
|--------|----------|---------|
| `OPCODE rd, rs1, rs2, rstride, precision` | 5 operands | H_PREFETCH_M, H_PREFETCH_V, H_STORE_V |
| `OPCODE rd, rs1, rs2, rmask` | 4 operands | V_ADD_VV, V_MUL_VV, etc. |
| `OPCODE rd, rs1, rmask` | 3 operands | V_EXP_V, V_RECI_V |
| `OPCODE 0, rs1, rs2` | 3 operands | M_MM, M_TMM, M_MV, M_TMV |
| `OPCODE rd, rs1, rs2` | 3 operands | S_ADD_INT, C_SET_ADDR_REG |
| `OPCODE rd, rs1, imm` | 3 operands | S_ADDI_INT, M_MM_WO |
| `OPCODE rd, imm` | 2 operands | S_LUI_INT, M_BMM_WO, M_MV_WO |
| `OPCODE rd` | 1 operand | C_SET_SCALE_REG, C_SET_STRIDE_REG |

## Parameters

Refer to `plena_settings.toml` for the detailed parameters.

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| **MLEN** | Tile size used in matrix machine | 64 |
| **BLEN** | Tile size used in systolic array | 4 |
| **HLEN** | Tile size used in partitioned systolic array | 16 |
| **VLEN** | Tile size used in vector machine | 64 |
| **HBM_M_Prefetch_Amount** | Number of MLEN rows fetched from HBM | 64 |
| **HBM_V_Prefetch_Amount** | Number of VLEN rows fetched from HBM | 4 |


## Matrix (M-Type) Instructions

### Notation

| Notation | Description |
|----------|-------------|
| **Matrix[i]** | i-th entry of the Matrix SRAM |
| **Vector[i]** | i-th entry of the Vector SRAM |

**Addressing Constraints:**
- **Matrix SRAM:** Read Addresses `gp_reg<rs2> % MLEN` must be multiples of `BLEN`.
- **Matrix SRAM:** Write Addresses `gp_reg<rd> % MLEN` must be multiples of `BLEN`.
- **Vector SRAM:** Addresses must be multiples of `VLEN`.

### M_MM

**Format:** `M_MM 0, rs1, rs2`

**Operation:** `Systolic Array += Vector_SRAM[gp_reg<rs1>] @ Matrix_SRAM[gp_reg<rs2>]`

**Description:**

Fetch an (BLEN, MLEN) vector from the Vector SRAM using the address provided by `rs1` and an (MLEN, BLEN) matrix from the Matrix SRAM using the address provided by `rs2`. Then, perform an array of dot products. The result matrix (BLEN, BLEN) is internally accumulated in every PE of the systolic array. 0 is a placeholder here, it does not have the write access to the Vector SRAM.

**Example:**
```asm
S_ADDI_INT gp2, gp0, 0      ; Vector SRAM address = 0
S_ADDI_INT gp4, gp0, 0      ; Matrix SRAM address = 0
M_MM 0, gp2, gp4            ; Accumulate Vector[0] @ Matrix[0] into systolic array
```

### M_TMM

**Format:** `M_TMM 0, rs1, rs2`

**Operation:** `Systolic Array += Vector[gp_reg<rs1>] @ Matrix[gp_reg<rs2>]^T`

**Description:**

Similar to `M_MM`, but transposes the matrix.

### M_BMM

**Format:** `M_BMM 0, rs1, rs2`

**Operation:** `Systolic Array = Per Head (Vector_SRAM[gp_reg<rs2>] @ Matrix_SRAM[gp_reg<rs1> + gp_reg<rd>])`

`[MLEN // HLEN, MLEN, HLEN] @ [HLEN, MLEN] = [MLEN // HLEN, MLEN, MLEN]`

**Description:**

Only take the sliced (HLEN, MLEN) matrix from the Matrix SRAM using the address provided by `gp_reg<rs1> + gp_reg<rd>`, and the vector of shape (MLEN // HLEN, MLEN, HLEN) from the Vector SRAM using the address provided by `gp_reg<rs1>`. Then, perform an array of dot products. The result matrix [MLEN // HLEN, MLEN, MLEN] is internally accumulated in every PE of the systolic array.

### M_BTMM

**Format:** `M_BTMM 0, rs1, rs2`

**Operation:** `Systolic Array = Per Head (Vector_SRAM[gp_reg<rs2>] @ Matrix_SRAM[gp_reg<rs1> + gp_reg<rd>])^T`

**Description:**

Similar to `M_BMM`, but the matrix from Matrix SRAM is transposed before the operation.

### M_BMM_WO

**Format:** `M_BMM_WO rd, imm`

**Description:**

Store the accumulated result [MLEN // HLEN, MLEN, MLEN] to the Vector SRAM at the address specified by `gp_reg<rd> + imm` with stride `MLEN // HLEN` and precision `Weights` or `KeyValue` depending on the precision of the MXFP data.

### M_MM_WO

**Format:** `M_MM_WO rd, rs1, imm`

**Operation:** 

**Description:**

Write the accumulated (BLEN × BLEN) tile from the systolic array into Vector SRAM starting at gp_reg<rd>. The tile is laid out row by row (BLEN rows). The row stride is gp_reg<rd> * MLEN (if gp_reg<rd> == 0, use 1 * MLEN). Within each stride, write BLEN elements starting at column offset gp_reg<rd> % MLEN, and the start at row gp_reg<rd> // MLEN in Matrix SRAM.

### M_MV

**Format:** `M_MV rd, rs1, x`

**Operation:** `First Row of Sys Array = Vector[gp_reg<rs1>] @ Matrix[gp_reg<rs2>]`

**Description:**

Fetch an (MLEN, MLEN) matrix from the Matrix SRAM using the address provided by `gp_reg<rs2>`, and an (MLEN, 1) vector from the Vector SRAM using the address provided by `gp_reg<rs1>`. Then, perform a dot product and store the resulting (MLEN, 1) vector in the **First Row of Sys Array**.

### M_TMV

**Format:** `M_TMV rd, rs1, x`

**Operation:** `First Row of Sys Array = Vector[gp_reg<rs1>] @ Matrix[gp_reg<rs2>]^T`

**Description:**

This instruction is similar to `M_MV`, but transposes the Matrix when fetching from the Matrix SRAM at the address set by `rs2`.

### M_BMV (TODO: Implement)

### M_BTMV (TODO: Implement)

### M_MV_WO

**Format:** `M_MV_WO rd, imm`

**Description:**

Store the accumulated result (MLEN, 1) stored in the first row of the systolic array to the Vector SRAM at the address specified by `gp_reg<rd> + imm`

### M_BMV_WO (TODO: Implement)

---

## Vector (V-Type) Instructions

### Notation

| Notation | Description |
|----------|-------------|
| **Vector[i]** | i-th entry of the Vector SRAM |

`rmask` is a binary flag indicating whether to apply the mask to the result. The mask is set by the `C_SET_V_MASK_REG` instruction.

**Addressing Constraints:**
- **Vector SRAM:** Read Addresses `gp_reg<rs1> % VLEN` and `gp_reg<rs2> % VLEN` must be multiples of `VLEN`.
- **Vector SRAM:** Write Addresses `gp_reg<rd> % VLEN` must be multiples of `VLEN`.

### V_ADD_VV

**Format:** `V_ADD_VV rd, rs1, rs2, rmask`

**Operation:** `Vector[gp_reg<rd>] & gp_rmask = (Vector[gp_reg<rs2>] & gp_reg<rmask>) + (Vector[gp_reg<rs1>]) & gp_rmask`

**Description:**

Fetch two (MLEN, 1) vectors from the Vector SRAM using the addresses provided by `rs2` and `rs1`, and then perform element-wise addition. Store the resulting vector back to the Vector SRAM at the address provided by `rd`.

### V_ADD_VF

**Format:** `V_ADD_VF rd, rs1, rs2, rmask`

**Operation:** `Vector[gp_reg<rd>] & gp_rmask = (Vector[gp_reg<rs1>] & gp_reg<rmask>) + Broadcast(fp_reg<rs2>) & gp_reg<rmask>`

**Description:**

Fetch an (MLEN, 1) vector from the Vector SRAM using the address provided by `rs1`, then fetch a single floating-point value from the FP register file using the index provided by `rs2`. Broadcast this value by duplicating it to form an (MLEN, 1) vector, and then perform element-wise addition. Store the resulting vector back to Vector SRAM at the address provided by `rd`.

### V_SUB_VV

**Format:** `V_SUB_VV rd, rs1, rs2, rmask`

**Operation:** `Vector[gp_reg<rd>] & gp_rmask = (Vector[gp_reg<rs2>] & gp_reg<rmask>) - (Vector[gp_reg<rs1>] & gp_reg<rmask>)`

**Description:**

Similar to `V_ADD_VV`, but performs element-wise subtraction.

### V_SUB_VF

**Format:** `V_SUB_VF rd, rs1, fp2, rmask, rorder`

**Operation:**
- If `rorder = 0` (Normal): `Vector[gp_reg<rd>] & gp_rmask = (Vector[gp_reg<rs1>] & gp_reg<rmask>) - Broadcast(fp_reg<fp2>) & gp_reg<rmask>`
- If `rorder > 0` (Reverse): `Vector[gp_reg<rd>] & gp_rmask = Broadcast(fp_reg<fp2>) & gp_reg<rmask> - (Vector[gp_reg<rs1>] & gp_reg<rmask>)`

**Description:**

Similar to `V_ADD_VF`, but performs element-wise subtraction. The `rorder` parameter (decoded from `funct1`) controls the order of subtraction.

### V_MUL_VV

**Format:** `V_MUL_VV rd, rs1, rs2, rmask`

**Operation:** `Vector[gp_reg<rd>] & gp_rmask = (Vector[gp_reg<rs1>] & gp_reg<rmask>) * (Vector[gp_reg<rs2>] & gp_reg<rmask>)`

**Description:**

Similar to `V_ADD_VV`, but performs element-wise multiplication.

### V_MUL_VF

**Format:** `V_MUL_VF rd, rs1, fp2, rmask`

**Operation:** `Vector[gp_reg<rd>] & gp_rmask = (Vector[gp_reg<rs1>] & gp_reg<rmask>) * Broadcast(fp_reg<fp2>) & gp_reg<rmask>`

**Description:**

Similar to `V_ADD_VF`, but performs element-wise multiplication.

### V_EXP_V

**Format:** `V_EXP_V rd, rs1, x, rmask`

**Operation:** `Vector[gp_reg<rd>] = exp(Vector[gp_reg<rs1>])`

**Description:**

Fetch an (MLEN, 1) vector from the Vector SRAM using the address provided by `rs1`, perform element-wise exponentiation, and store the resulting vector back into the Vector SRAM at the address specified by `rd`.

### V_RECI_V

**Format:** `V_RECI_V rd, rs1, x`

**Operation:** `Vector[gp_reg<rd>] = reciprocal(Vector[gp_reg<rs1>])`

**Description:**

Fetch an (MLEN, 1) vector from the Vector SRAM using the address provided by `rs1`, perform element-wise reciprocal, and store the resulting vector back into the Vector SRAM at the address specified by `rd`.

### V_RED_SUM

**Format:** `V_RED_SUM rd, rs1, 0`

**Operation:** `fp_reg<rd> = sum(Vector[gp_reg<rs1>], fp_reg<rd>)`

**Description:**

Fetch an (MLEN, 1) vector from the Vector SRAM using the address provided by `rs1`, and a single floating-point value from the FP register file using the index specified by `rd`. Perform element-wise addition on the combined vector, and store the resulting sum back into the FP register file at the index specified by `rd`. This instruction is designed to facilitate continuous summation along a high-dimension vector.

### V_RED_MAX

**Format:** `V_RED_MAX rd, rs1, 0`

**Operation:** `fp_reg<rd> = max(Vector[gp_reg<rs1>], fp_reg<rd>)`

**Description:**

Similar to `V_RED_SUM` but performs the max value selection operation.

---

## Scalar (S-Type) Instructions

### Integer Operations

#### Notation

| Notation | Description |
|----------|-------------|
| **INT_MEM[i]** | i-th entry of the SRAM within the scalar machine specifically designed for integer operations |

#### S_ADD_INT

**Format:** `S_ADD_INT rd, rs1, rs2`

**Operation:** `gp_reg<rd> = gp_reg<rs1> + gp_reg<rs2>`

#### S_ADDI_INT

**Format:** `S_ADDI_INT rd, rs1, imm`

**Operation:** `gp_reg<rd> = gp_reg<rs1> + imm`

**Example:**
```asm
S_ADDI_INT gp1, gp0, 128    ; gp1 = 0 + 128 = 128
S_ADDI_INT gp2, gp1, 64     ; gp2 = 128 + 64 = 192
```

#### S_SUB_INT

**Format:** `S_SUB_INT rd, rs1, rs2`

**Operation:** `gp_reg<rd> = gp_reg<rs1> - gp_reg<rs2>`

#### S_MUL_INT

**Format:** `S_MUL_INT rd, rs1, rs2`

**Operation:** `gp_reg<rd> = gp_reg<rs1> * gp_reg<rs2>`

#### S_LUI_INT

**Format:** `S_LUI_INT rd, imm`

**Operation:** `gp_reg<rd> = imm << 12`

**Description:**

Load upper immediate value into the integer register.

#### S_LD_INT

**Format:** `S_LD_INT rd, rs1, imm`

**Operation:** `gp_reg<rd> = INT_MEM[gp_reg<rs1> + imm]`

#### S_ST_INT

**Format:** `S_ST_INT rd, rs1, imm`

**Operation:** `INT_MEM[gp_reg<rs1> + imm] = gp_reg<rd>`

### Floating-Point Operations

#### Notation

| Notation | Description |
|----------|-------------|
| **FP_MEM[i]** | i-th entry of the SRAM within the scalar machine specifically designed for floating-point operations |

#### S_ADD_FP

**Format:** `S_ADD_FP rd, rs1, rs2`

**Operation:** `fp_reg<rd> = fp_reg<rs1> + fp_reg<rs2>`

#### S_SUB_FP

**Format:** `S_SUB_FP rd, rs1, rs2`

**Operation:** `fp_reg<rd> = fp_reg<rs1> - fp_reg<rs2>`

#### S_MAX_FP

**Format:** `S_MAX_FP rd, rs1, rs2`

**Operation:** `fp_reg<rd> = max(fp_reg<rs1>, fp_reg<rs2>)`

#### S_MUL_FP

**Format:** `S_MUL_FP rd, rs1, rs2`

**Operation:** `fp_reg<rd> = fp_reg<rs1> * fp_reg<rs2>`

#### S_EXP_FP

**Format:** `S_EXP_FP rd, rs1, x`

**Operation:** `fp_reg<rd> = exp(fp_reg<rs1>)`

#### S_RECI_FP

**Format:** `S_RECI_FP rd, rs1, x`

**Operation:** `fp_reg<rd> = reciprocal(fp_reg<rs1>)`

#### S_SQRT_FP

**Format:** `S_SQRT_FP rd, rs1, x`

**Operation:** `fp_reg<rd> = sqrt(fp_reg<rs1>)`

#### S_LD_FP

**Format:** `S_LD_FP rd, rs1, imm`

**Operation:** `fp_reg<rd> = FP_MEM[gp_reg<rs1> + imm]`

#### S_ST_FP

**Format:** `S_ST_FP rd, rs1, imm`

**Operation:** `FP_MEM[gp_reg<rs1> + imm] = fp_reg<rd>`

#### S_MAP_V_FP

**Format:** `S_MAP_V_FP rd, rs1, imm`

**Operation:** `Vector[gp_reg<rd> :+ VLEN] = FP_MEM[gp_reg<rs1> + imm :+ VLEN]`

**Description:**

Copy a vector of length VLEN from FP_MEM to Vector SRAM.

---

## Memory (H-Type) Instructions

### Notation

| Notation | Description |
|----------|-------------|
| **Matrix[i]** | The i-th entry of the Matrix SRAM |
| **Vector[i]** | The i-th entry of the Vector SRAM |
| **HBM[i]** | The i-th entry of the HBM |

### H_PREFETCH_M

**Addressing Constraints:**
- **Matrix SRAM:** Write Addresses `gp_reg<rd>` must be multiples of `MLEN * MLEN`.
- **Vector SRAM:** Write Addresses `gp_reg<rd>` must be multiples of `VLEN`.

**Format:** `H_PREFETCH_M rd, rs1, rs2, rstride, precision`

**Operation:** `Matrix[gp_reg<rd>] = HBM[gp_reg<rs1> + hbm_addr_reg<rs2>]`

**Description:**

Prefetch a matrix of size **HBM_M_Prefetch_Amount × MLEN** from the HBM to the Matrix SRAM, with a stride width specified by **STRIDE_REG** (set via `C_SET_STRIDE_REG`).

**Operands:**
- `rd`: Register containing destination address in Matrix SRAM
- `rs1`: Register containing offset within HBM
- `rs2`: HBM address register index (`a0`-`a7`) containing base address
- `rstride`: Stride register selector (use `1` to enable stride from STRIDE_REG)
- `precision`: Data precision (`0` = Weights, `1` = KeyValue)

**Example:**
```asm
S_ADDI_INT gp1, gp0, 576           ; gp1 = 576 (HBM base address for weights)
C_SET_ADDR_REG a1, gp0, gp1        ; a1 = HBM base address

S_ADDI_INT gp4, gp0, 128           ; gp4 = 128 (stride)
C_SET_STRIDE_REG gp4               ; Set stride register

S_ADDI_INT gp2, gp0, 0             ; gp2 = 0 (Matrix SRAM destination)
S_ADDI_INT gp3, gp0, 0             ; gp3 = 0 (HBM offset)
H_PREFETCH_M gp2, gp3, a1, 1, 0    ; Prefetch weights from HBM[a1+0] to Matrix[0]
```

### H_PREFETCH_V

**Format:** `H_PREFETCH_V rd, rs1, rs2, rstride, precision`

**Operation:** `Vector[gp_reg<rd>] = HBM[gp_reg<rs1> + hbm_addr_reg<rs2>]`

**Description:**

Prefetch a matrix of size **HBM_V_Prefetch_Amount × VLEN** from the HBM to the Vector SRAM, with a stride width specified by **STRIDE_REG**.

**Operands:**
- `rd`: Register containing destination address in Vector SRAM
- `rs1`: Register containing offset within HBM
- `rs2`: HBM address register index (`a0`-`a7`) containing base address
- `rstride`: Stride register selector (`0` = no stride, `1` = use STRIDE_REG)
- `precision`: Data precision (`0` = Activation, `1` = KeyValue)

**Example:**
```asm
S_ADDI_INT gp3, gp0, 0             ; gp3 = 0 (Vector SRAM destination)
S_ADDI_INT gp2, gp0, 0             ; gp2 = 0 (HBM offset)
H_PREFETCH_V gp3, gp2, a0, 1, 0    ; Prefetch activations from HBM[a0+0] to Vector[0]
```

### H_STORE_V

**Format:** `H_STORE_V rd, rs1, rs2, rstride, precision`

**Operation:** `HBM[gp_reg<rs1> + hbm_addr_reg<rs2>] = Vector[gp_reg<rd>]`

**Description:**

Store a matrix of size **HBM_V_Writeback_Amount × VLEN** from Vector SRAM to HBM, with a stride width specified by **STRIDE_REG**.

**Operands:**
- `rd`: Register containing source address in Vector SRAM
- `rs1`: Register containing offset within HBM
- `rs2`: HBM address register index (`a0`-`a7`) containing base address
- `rstride`: Stride register selector (`0` = no stride, `1` = use STRIDE_REG)
- `precision`: Data precision (`0` = Activation, `1` = KeyValue)

---

## Control and Status Register (C-Type) Instructions

### C_SET_ADDR_REG

**Format:** `C_SET_ADDR_REG rd, rs1, rs2`

**Operation:** `hbm_addr_reg<rd> = {gp_reg<rs2>, gp_reg<rs1>}`

**Description:**

Set the value of `hbm_addr_reg[rd]` by concatenating two general-purpose registers. The HBM address register has double the bit width of a GP register. The concatenation order is `{rs2 (high bits), rs1 (low bits)}`.

**Example:**
```asm
S_ADDI_INT gp1, gp0, 576           ; gp1 = 576 (low bits of address)
C_SET_ADDR_REG a1, gp0, gp1        ; a1 = {gp1, gp0} = 576
```

### C_SET_SCALE_REG

**Format:** `C_SET_SCALE_REG rd`

**Operation:** `SCALE_OFFSET = gp_reg<rd>`

**Description:**

Set the scale offset register. This is **required before H_PREFETCH_M and H_PREFETCH_V** operations when using MXFP format data. The scale offset specifies the distance between data blocks and their scale factors in HBM.

**Typical value:** For weight matrices, set to `hidden_size * hidden_size` (total number of elements).

**Example:**
```asm
S_ADDI_INT gp4, gp0, 16384         ; gp4 = 128*128 = 16384 (weight matrix size)
C_SET_SCALE_REG gp4                ; Set scale offset
```

### C_SET_STRIDE_REG

**Format:** `C_SET_STRIDE_REG rd`

**Operation:** `STRIDE_SIZE = gp_reg<rd>`

**Description:**

Set the stride size for prefetch instructions. The value is read from the register `rd`, **not** an immediate value.

**Example:**
```asm
S_ADDI_INT gp4, gp0, 128           ; gp4 = 128 (stride value)
C_SET_STRIDE_REG gp4               ; STRIDE_SIZE = 128
```

### C_SET_V_MASK_REG

**Format:** `C_SET_V_MASK_REG rd`

**Operation:** `V_MASK = gp_reg<rd>`

**Description:**

Set the vector mask register for masked vector operations.

### C_BREAK

**Format:** `C_BREAK 0, 0, 0`

**Operation:** Breakpoint exception

**Description:**

Triggers a breakpoint exception for debugging purposes. **Note:** Programs do not require `C_BREAK` to terminate - execution completes when all instructions finish.

### C_LOOP_START

**Format:** `C_LOOP_START rd, imm`

**Operation:** Initialize loop with `imm` iterations, using `rd` as the loop counter register.

**Description:**

Start a hardware loop. The loop count is set by `imm`. The register `rd` is used internally to track the loop counter.

**Example:**
```asm
C_LOOP_START gp4, 8                ; Start loop with 8 iterations
; ... loop body ...
C_LOOP_END gp4                     ; End of loop
```

### C_LOOP_END

**Format:** `C_LOOP_END rd, 0`

**Operation:** If `gp_reg<rd> > 0`, decrement counter and jump to matching `C_LOOP_START`.

**Description:**

End of a hardware loop. If the loop counter (in register `rd`) is greater than 0, it decrements the counter and jumps back to the corresponding `C_LOOP_START`.

---

