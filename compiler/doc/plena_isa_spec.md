# PLENA Instruction Set Architecture (ISA) Specification

## Register Types

The PLENA architecture supports four types of registers:

- **gp_reg** (`gp0` to `gp15`): General-purpose integer registers
- **fp_reg** (`f0` to `f7`): Floating-point registers
- **hbm_addr_reg** (`a0` to `a7`): HBM address registers

## Instruction Format

Instructions follow one of the following formats:

- `opcode, rd, rs1, rs2, rstride, precision`
- `opcode, rd, rs1, rs2, rmask` (V two sources instructions)
- `opcode, rd, rs1, rmask` (V one source instructions)
- `opcode, 0, rs1, rs2` (M_MM, M_TMM, M_MV, M_TMV)
- `opcode, rd, rs1, rs2`
- `opcode, rd, imm` (M_BMM_WO, M_MV_WO)
- `opcode, rd, rs1, imm`

## Parameters
Refer to `plena_settings.toml` for the detailed parameters.
- **MLEN**: Tile size used in matrix machine
- **BLEN**: Tile size used in systolic array
- **HLEN**: Tile size used in partitioned systolic array
- **VLEN**: Tile size used in vector machine
- **HBM_M_Prefetch_Amount**: Number of MLEN rows fetched from HBM
- **HBM_V_Prefetch_Amount**: Number of VLEN rows fetched from HBM


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

**Format:** `opcode, 0, rs1, rs2`

**Operation:** `Systolic Array = Vector_SRAM[gp_reg<rs1>] @ Matrix_SRAM[gp_reg<rs2>]`

**Description:** 

Fetch an (BLEN,MLEN) vector from the Vector SRAM using the address provided by `rs1` and an (MLEN, BLEN) matrix from the Matrix SRAM using the address provided by `rs2`. Then, perform an array of dot products. The result matrix (MLEN, BLEN) is internally accumulated in every PE of the systolic array.

### M_TMM

**Format:** `opcode, 0, rs1, rs2`

**Operation:** `Systolic Array = Vector[gp_reg<rs1>] @ Matrix[gp_reg<rs2>]^T`

**Description:** 

Similar to `M_MM`, but transposes the matrix.

### M_BMM

**Format:** `opcode, 0, rs1, rs2`

**Operation:** `Systolic Array = Per Head (Vector_SRAM[gp_reg<rs2>] @ Matrix_SRAM[gp_reg<rs1> + gp_reg<rd>])`

`[MLEN // HLEN, MLEN, HLEN] @ [HLEN, MLEN] = [MLEN // HLEN, MLEN, MLEN]`

**Description:** 

Only take the sliced (HLEN, MLEN) matrix from the Matrix SRAM using the address provided by `gp_reg<rs1> + gp_reg<rd>`, and the vector of shape (MLEN // HLEN, MLEN, HLEN) from the Vector SRAM using the address provided by `gp_reg<rs1>`. Then, perform an array of dot products. The result matrix [MLEN // HLEN, MLEN, MLEN] is internally accumulated in every PE of the systolic array.

### M_BTMM

**Format:** `opcode, 0, rs1, rs2`

**Operation:** `Systolic Array = Per Head (Vector_SRAM[gp_reg<rs2>] @ Matrix_SRAM[gp_reg<rs1> + gp_reg<rd>])^T`

**Description:** 

Similar to `M_BMM`, but the matrix from Matrix SRAM is transposed before the operation.

### M_BMM_WO

**Format:** `opcode, rd, imm`

**Description:** 

Store the accumulated result [MLEN // HLEN, MLEN, MLEN] to the Vector SRAM at the address specified by `gp_reg<rd> + imm` with stride `MLEN // HLEN` and precision `Weights` or `KeyValue` depending on the precision of the MXFP data.

### M_MM_WO

**Format:** `opcode, rd, rstride, imm`

**Description:** 

Output the accumulated result (BLEN, BLEN) stored in the first row of the systolic array to the Vector SRAM at the address specified by `gp_reg<rd>` with stride `rstride`.

### M_MV

**Format:** `opcode, rd, rs1, x`

**Operation:** `First Row of Sys Array = Vector[gp_reg<rs1>] @ Matrix[gp_reg<rs2>]`
**Description:** 

Fetch an (MLEN, MLEN) matrix from the Matrix SRAM using the address provided by `gp_reg<rs2>`, and an (MLEN, 1) vector from the Vector SRAM using the address provided by `gp_reg<rs1>`. Then, perform a dot product and store the resulting (MLEN, 1) vector in the **First Row of Sys Array**.

### M_TMV 

**Format:** `opcode, rd, rs1, x`

**Operation:** `First Row of Sys Array = Vector[gp_reg<rs1>] @ Matrix[gp_reg<rs2>]^T`

**Description:** 

This instruction is similar to `M_MV`, but transposes the Matrix when fetching from the Matrix SRAM at the address set by `rs2`.

### M_BMV (TODO: Implement)

### M_BTMV (TODO: Implement)

### M_MV_WO 

**Format:** `opcode, rd, imm`

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

**Format:** `opcode, rd, rs1, rs2, rmask`

**Operation:** `Vector[gp_reg<rd>] & gp_rmask = (Vector[gp_reg<rs2>] & gp_reg<rmask>) + (Vector[gp_reg<rs1>]) & gp_rmask`

**Description:** 

Fetch two (MLEN, 1) vectors from the Vector SRAM using the addresses provided by `rs2` and `rs1`, and then perform element-wise addition. Store the resulting vector back to the Vector SRAM at the address provided by `rd`.

### V_ADD_VF 

**Format:** `opcode, rd, rs1, rs2, rmask`

**Operation:** `Vector[gp_reg<rd>] & gp_rmask = (Vector[gp_reg<rs1>] & gp_reg<rmask>) + Broadcast(fp_reg<rs2>) & gp_reg<rmask>`

**Description:** 

Fetch an (MLEN, 1) vector from the Vector SRAM using the address provided by `rs1`, then fetch a single floating-point value from the FP register file using the index provided by `rs2`. Broadcast this value by duplicating it to form an (MLEN, 1) vector, and then perform element-wise addition. Store the resulting vector back to Vector SRAM at the address provided by `rd`.

### V_SUB_VV 

**Format:** `opcode, rd, rs1, rs2, rmask`

**Operation:** `Vector[gp_reg<rd>] & gp_rmask = (Vector[gp_reg<rs2>] & gp_reg<rmask>) - (Vector[gp_reg<rs1>] & gp_reg<rmask>)`

**Description:** 

Similar to `V_ADD_VV`, but performs element-wise subtraction.

### V_SUB_VF 

**Format:** `opcode, rd, rs1, fp2, rmask, rorder`

**Operation:** 
- If `rorder = Normal`: `Vector[gp_reg<rd>] & gp_rmask = (Vector[gp_reg<rs1>] & gp_reg<rmask>) - Broadcast(fp_reg<fp2>) & gp_reg<rmask>`
- If `rorder = Reverse`: `Vector[gp_reg<rd>] & gp_rmask = Broadcast(fp_reg<fp2>) & gp_reg<rmask> - (Vector[gp_reg<rs1>] & gp_reg<rmask>)`

**Description:** 

Similar to `V_ADD_VF`, but performs element-wise subtraction. The `rorder` parameter (decoded from `funct1`) controls the order of subtraction:
- `0` (Normal): vector - scalar
- `>0` (Reverse): scalar - vector

### V_MUL_VV 

**Format:** `opcode, rd, rs1, rs2, rmask`

**Operation:** `Vector[gp_reg<rd>] & gp_rmask = (Vector[gp_reg<rs1>] & gp_reg<rmask>) * (Vector[gp_reg<rs2>] & gp_reg<rmask>)`

**Description:** 

Similar to `V_ADD_VV`, but performs element-wise multiplication.

### V_MUL_VF 

**Format:** `opcode, rd, rs1, fp2, rmask`

**Operation:** `Vector[gp_reg<rd>] & gp_rmask = (Vector[gp_reg<rs1>] & gp_reg<rmask>) * Broadcast(fp_reg<fp2>) & gp_reg<rmask>`

**Description:** 

Similar to `V_ADD_VF`, but performs element-wise multiplication.

### V_EXP_V 

**Format:** `opcode, rd, rs1, x, rmask`

**Operation:** `Vector[gp_reg<rd>] = exp(Vector[gp_reg<rs1>])`

**Description:** 

Fetch an (MLEN, 1) vector from the Vector SRAM using the address provided by `rs1`, perform element-wise exponentiation, and store the resulting vector back into the Vector SRAM at the address specified by `rd`.

### V_RECI_V 

**Format:** `opcode, rd, rs1, x`

**Operation:** `Vector[gp_reg<rd>] = reciprocal(Vector[gp_reg<rs1>])`

**Description:** 

Fetch an (MLEN, 1) vector from the Vector SRAM using the address provided by `rs1`, perform element-wise reciprocal, and store the resulting vector back into the Vector SRAM at the address specified by `rd`.

### V_RED_SUM 

**Format:** `opcode, rd, rs1, 0`

**Operation:** `fp_reg<rd> = sum(Vector[gp_reg<rs1>], fp_reg<rd>)`

**Description:** 

Fetch an (MLEN, 1) vector from the Vector SRAM using the address provided by `rs1`, and a single floating-point value from the FP register file using the index specified by `rd`. Perform element-wise addition on the combined vector, and store the resulting sum back into the FP register file at the index specified by `rd`. This instruction is designed to facilitate continuous summation along a high-dimension vector.

### V_RED_MAX 

**Format:** `opcode, rd, rs1, 0`

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

**Format:** `opcode, rd, rs1, rs2`

**Operation:** `gp_reg<rd> = gp_reg<rs1> + gp_reg<rs2>`

#### S_ADDI_INT 

**Format:** `opcode, rd, rs1, imm2`

**Operation:** `gp_reg<rd> = gp_reg<rs1> + imm2`

#### S_SUB_INT 

**Format:** `opcode, rd, rs1, rs2`

**Operation:** `gp_reg<rd> = gp_reg<rs1> - gp_reg<rs2>`

#### S_MUL_INT 

**Format:** `opcode, rd, rs1, rs2`

**Operation:** `gp_reg<rd> = gp_reg<rs1> * gp_reg<rs2>`

#### S_LUI_INT 

**Format:** `opcode, rd, imm`

**Operation:** `gp_reg<rd> = imm << 12`

**Description:** 

Load upper immediate value into the integer register.

#### S_LD_INT 

**Format:** `opcode, rd, rs1, imm2`

**Operation:** `gp_reg<rd> = INT_MEM[gp_reg<rs1> + imm2]`

#### S_ST_INT 

**Format:** `opcode, rd, rs1, imm2`

**Operation:** `INT_MEM[gp_reg<rs1> + imm2] = gp_reg<rd>`

### Floating-Point Operations

#### Notation

| Notation | Description |
|----------|-------------|
| **FP_MEM[i]** | i-th entry of the SRAM within the scalar machine specifically designed for floating-point operations |

#### S_ADD_FP 

**Format:** `opcode, rd, rs1, rs2`

**Operation:** `fp_reg<rd> = fp_reg<rs1> + fp_reg<rs2>`

#### S_SUB_FP 

**Format:** `opcode, rd, rs1, rs2`

**Operation:** `fp_reg<rd> = fp_reg<rs1> - fp_reg<rs2>`

#### S_MAX_FP 

**Format:** `opcode, rd, rs1, rs2`

**Operation:** `fp_reg<rd> = max(fp_reg<rs1>, fp_reg<rs2>)`

#### S_MUL_FP 

**Format:** `opcode, rd, rs1, rs2`

**Operation:** `fp_reg<rd> = fp_reg<rs1> * fp_reg<rs2>`

#### S_EXP_FP 

**Format:** `opcode, rd, rs1, x`

**Operation:** `fp_reg<rd> = exp(fp_reg<rs1>)`

#### S_RECI_FP

**Format:** `opcode, rd, rs1, x`

**Operation:** `fp_reg<rd> = reciprocal(fp_reg<rs1>)`

#### S_SQRT_FP 

**Format:** `opcode, rd, rs1, x`

**Operation:** `fp_reg<rd> = sqrt(fp_reg<rs1>)`

#### S_LD_FP 

**Format:** `opcode, rd, rs1, imm2`

**Operation:** `fp_reg<rd> = FP_MEM[gp_reg<rs1> + imm2]`

#### S_ST_FP 

**Format:** `opcode, rd, rs1, imm2`

**Operation:** `FP_MEM[gp_reg<rs1> + imm2] = fp_reg<rd>`

#### S_MAP_V_FP 

**Format:** `opcode, rd, rs1, imm2`

**Operation:** `Vector[gp_reg<rd> :+ VLEN] = FP_MEM[gp_reg<rs1> + imm2 :+ VLEN]`

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

**Format:** `opcode, rd, rs1, rs2, rstride, precision`

**Operation:** `Matrix[gp_reg<rd>] = HBM[gp_reg<rs1> + hbm_addr_reg_<rs2>]`

**Description:** 

Prefetch a matrix of size **HBM_M_Prefetch_Amount × MLEN** from the HBM to the Matrix SRAM, with a stride width specified by **hbm_stride_reg[rstride]**.

The `precision` field (decoded from `funct1`) determines the data precision:
- `0` (Weights): High precision weights
- `>0` (KeyValue): Lower precision key-value data

### H_PREFETCH_V 

**Format:** `opcode, rd, rs1, rs2, rstride, precision`

**Operation:** `Vector[gp_reg<rd>] = HBM[gp_reg<rs1> + hbm_addr_reg_<rs2>]`

**Description:** 

Prefetch a matrix of size **HBM_V_Prefetch_Amount × VLEN** from the HBM to the Vector SRAM, with a stride width specified by **hbm_stride_reg[rstride]**.

The `precision` field (decoded from `funct1`) determines the data precision:
- `0` (Activation): High precision activation data
- `>0` (KeyValue): Lower precision key-value data

### H_STORE_V 

**Format:** `opcode, rd, rs1, rs2, rstride, precision`

**Operation:** `HBM[gp_reg<rs1> + hbm_addr_reg_<rs2>] = Vector[gp_reg<rd>]`

**Description:** 

Store a matrix of size **HBM_V_Writeback_Amount × VLEN** from Vector SRAM to HBM, with a stride width specified by **hbm_stride_reg[rstride]**.

The `precision` field (decoded from `funct1`) determines the data precision:
- `0` (Activation): High precision activation data
- `>0` (KeyValue): Lower precision key-value data

---

## Control and Status Register (C-Type) Instructions

### C_SET_ADDR_REG 

**Format:** `opcode, rd, rs1, rs2`

**Operation:** `hbm_addr_reg_<rd> = {gp_reg<rs2>, gp_reg<rs1>}`

**Description:** 

This instruction is used to set the value of `hbm_addr_reg[rd]`, assuming it has double the bit width of `fix_reg`, by concatenating two `fix_reg` entries and storing the result in `hbm_addr_reg[rd]`. The concatenation order is `{rs2, rs1}`.

### C_SET_SCALE_REG 

**Format:** `opcode, rd`

**Operation:** `SCALE_OFFSET = rd`

**Description:** 

This instruction is used to set the scale offset. The blocks and scales of the MXFP data are stored separately in HBM for memory alignment purposes. Their distance is set by the scale offset. This value differs depending on the precision of the MXFP and the data size. For example, for Q(B, S, H, D), the scales are stored after the blocks, and the offset is `B × S × H × D × (EXP_WIDTH + MANT_WIDTH + 1) / 8`.

### C_SET_STRIDE_REG 

**Format:** `opcode, rd`

**Operation:** `STRIDE_SIZE = rd`

**Description:** 

This instruction is used to set the stride size for the prefetch instructions.

### C_SET_V_MASK_REG 

**Format:** `opcode, rd`

**Operation:** `V_MASK = rd`

**Description:** 

This instruction is used to set the vector mask register for masked vector operations.

### C_BREAK

**Format:** `opcode, 0, 0, 0`

**Operation:** Breakpoint exception

**Description:** 

Triggers a breakpoint exception, typically used for debugging purposes.

### C_LOOP_START

**Format:** `opcode, rd, imm`

**Description:** 

This instruction is used to start a loop. The loop count is set by the `imm` field.

### C_LOOP_END

**Format:** `opcode, rd, 0`

**Description:** 

Jump to the start of the loop where the C_LOOP_START is called if the rd value is greater than 0 and reduce the rd value by 1.

---

## Instruction Encoding Summary

### Opcode Map

| Opcode | Instruction | Type |
|--------|-------------|------|
| 0x00 | Invalid | - |
| 0x01 | M_MM | M-Type |
| 0x02 | M_TMM | M-Type |
| 0x03 | M_BMM | M-Type |
| 0x04 | M_BTMM | M-Type |
| 0x05 | M_BMM_WO | M-Type |
| 0x06 | M_MM_WO | M-Type |
| 0x07 | M_MV | M-Type |
| 0x08 | M_TMV | M-Type |
| 0x09 | M_BMV | M-Type |
| 0x0A | M_BTMV | M-Type |
| 0x0B | M_MV_WO | M-Type |
| 0x0C | M_BMV_WO | M-Type |
| 0x0D | V_ADD_VV | V-Type |
| 0x0E | V_ADD_VF | V-Type |
| 0x0F | V_SUB_VV | V-Type |
| 0x10 | V_SUB_VF | V-Type |
| 0x11 | V_MUL_VV | V-Type |
| 0x12 | V_MUL_VF | V-Type |
| 0x13 | V_EXP_V | V-Type |
| 0x14 | V_RECI_V | V-Type |
| 0x15 | V_RED_SUM | V-Type |
| 0x16 | V_RED_MAX | V-Type |
| 0x17 | S_ADD_FP | S-Type |
| 0x18 | S_SUB_FP | S-Type |
| 0x19 | S_MAX_FP | S-Type |
| 0x1A | S_MUL_FP | S-Type |
| 0x1B | S_EXP_FP | S-Type |
| 0x1C | S_RECI_FP | S-Type |
| 0x1D | S_SQRT_FP | S-Type |
| 0x1E | S_LD_FP | S-Type |
| 0x1F | S_ST_FP | S-Type |
| 0x20 | S_MAP_V_FP | S-Type |
| 0x21 | S_ADD_INT | S-Type |
| 0x22 | S_ADDI_INT | S-Type |
| 0x23 | S_SUB_INT | S-Type |
| 0x24 | S_MUL_INT | S-Type |
| 0x25 | S_LUI_INT | S-Type |
| 0x26 | S_LD_INT | S-Type |
| 0x27 | S_ST_INT | S-Type |
| 0x28 | H_PREFETCH_M | H-Type |
| 0x29 | H_PREFETCH_V | H-Type |
| 0x2A | H_STORE_V | H-Type |
| 0x2B | C_SET_ADDR_REG | C-Type |
| 0x2C | C_SET_SCALE_REG | C-Type |
| 0x2D | C_SET_STRIDE_REG | C-Type |
| 0x2E | C_SET_V_MASK_REG | C-Type |
| 0x2F | C_BREAK | C-Type |