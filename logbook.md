# PLENA FPGA BRAM Inference Investigation

**Date**: 2026-02-04
**Configuration**: MLEN=64, VLEN=64, SRAM_DEPTH=1024, Matrix_Parallel_Rd_Dim=1

---

## 1. BRAM Utilization Summary

| Memory | RAMB18 Count | Width | Depth | Notes |
|--------|-------------|-------|-------|-------|
| matrix_sram element_storage | 64 | 14-bit | 1024 | 64 subsrams × 1 RAMB18 each |
| matrix_sram scale_storage | 64 | 8-bit | 1024 | 64 subsrams × 1 RAMB18 each |
| vector_sram (vect_storage) | 64 | 17-bit | 1024 | 64 slices × 1 RAMB18 each |
| **Total** | **192** | | | ~26% of XC7A200T (730 RAMB18) |

---

## 2. Matrix SRAM Architecture

### 2.1 Diagonal Skew for Conflict-Free Transposed Access

The matrix SRAM uses 64 independent subsrams to enable single-cycle access for both normal rows and transposed columns (rows of the transposed matrix).

**Key Insight**: Data is stored with a diagonal skew across the 64 subsrams, allowing all 64 elements to be read in parallel regardless of access orientation.

### 2.2 Data Flow

#### Write Path (wdata_transform)
```
Column c of row at address a → stored in subsram[(c + a) mod 64] at address a
```

#### Normal Read (row r)
- All 64 subsrams read address `r`
- subsram[k] returns element from column `(k - r) mod 64`
- rdata_transform unscrambles: `out[j] = in[(j + r) mod 64]`
- **Result**: Row `r` in correct column order

#### Transposed Read (column c)
- Each subsram[k] reads different address: `(k - c) mod 64`
- Address translation compensates for diagonal skew
- rdata_transform: `out[i] = in[(i + c) mod 64]`
- **Result**: Column `c` as `[a[0][c], a[1][c], ..., a[63][c]]`

### 2.3 Storage Layout Visualization

```
Write row 0: col 0→subsram[0], col 1→subsram[1], ..., col 63→subsram[63]
Write row 1: col 0→subsram[1], col 1→subsram[2], ..., col 63→subsram[0]  (rotated +1)
Write row 2: col 0→subsram[2], col 1→subsram[3], ..., col 63→subsram[1]  (rotated +2)
...
Write row r: col c → subsram[(c + r) mod 64]
```

### 2.4 Address Translation (subsram.sv)
```systemverilog
addr_offset = sram_index - raddr[5:0];
translated_raddr = transposed_read ? {raddr[9:6], addr_offset} : raddr;
```

---

## 3. BRAM Inference Verification

### 3.1 Why BRAM Infers Correctly (with or without `ram_style` attribute)

Vivado automatically infers BRAM when:
1. **Synchronous read pattern** - output registered on clock edge
2. **Sufficient depth** - 1024 depth strongly favors BRAM
3. **Standard dual-port pattern** - separate read/write ports

The coding style in subsram.sv follows Vivado's BRAM inference template:
```systemverilog
// Write port
always @(posedge clk) begin
    if (wen) mem[waddr] <= wdata;
end

// Read port (registered output = BRAM inference)
always @(posedge clk) begin
    if (req) raw_rdata <= mem[translated_raddr];
end
```

### 3.2 Protection Against BRAM Merging

**Concern**: If multiple narrow subsrams (14-bit each) were packed into the same physical BRAM, transposed reads would have port conflicts and break single-cycle access.

**Solution**: The `DONT_TOUCH` attribute prevents Vivado from merging:
```systemverilog
(* ram_style = "block", DONT_TOUCH = "TRUE" *) logic [ElementWidth-1:0] mem [SRAM_DEPTH];
```

### 3.3 Verification from Utilization Report

Each subsram instance confirmed to have exactly 1 RAMB18:
```
element_storage                    ... |     64 |   ← 64 RAMB18 total
  sub_sram_gen[0].sub_sram_init    ... |      1 |   ← 1 RAMB18
  sub_sram_gen[1].sub_sram_init    ... |      1 |   ← 1 RAMB18
  ...
  sub_sram_gen[63].sub_sram_init   ... |      1 |   ← 1 RAMB18
```

**No merging occurred** - the `DONT_TOUCH` attribute is working correctly.

---

## 4. Vector SRAM Architecture

### 4.1 Memory Structure (prim_generic_ram_2p.sv)

Uses sliced memory for per-element write masks:
```systemverilog
for (k = 0; k < MaskWidth; k++) begin : gen_mem_slice
    logic [DataBitsPerMask-1:0] mem_slice [Depth];  // 17-bit × 1024
end
```

- **MaskWidth** = VLEN = 64 slices
- **DataBitsPerMask** = V_FP_EXP_WIDTH + V_FP_MANT_WIDTH + 1 = 8 + 8 + 1 = 17 bits
- Each slice: 17-bit × 1024 depth → 1 RAMB18

### 4.2 True Dual-Port Pattern
```systemverilog
// PORT A
always @(posedge clk_i) begin
    if (a_req_i) begin
        if (effective_a_write && a_wmask[k])
            mem_slice[a_addr_i] <= a_wdata_i[...];
        a_rdata_o[...] <= mem_slice[a_addr_i];
    end
end

// PORT B (similar)
```

---

## 5. Key Files

| File | Purpose |
|------|---------|
| `src/definitions/configuration.svh` | MLEN, VLEN, SRAM_DEPTH parameters |
| `src/definitions/precision.svh` | Data widths (MXFP, FP formats) |
| `src/memory/matrix_sram/rtl/subsram.sv` | Core matrix memory with address translation |
| `src/memory/matrix_sram/rtl/biaccess_sram.sv` | Instantiates 64 subsrams |
| `src/memory/matrix_sram/rtl/wdata_transform.sv` | Write-side diagonal skew |
| `src/memory/matrix_sram/rtl/rdata_transform.sv` | Read-side unscrambling |
| `src/memory/matrix_sram/rtl/matrix_sram_with_rounding.sv` | Top-level with element + scale storage |
| `src/memory/vector_sram/rtl/prim_generic_ram_2p.sv` | True dual-port RAM for vector SRAM |

---

## 6. Conclusions

1. **BRAM count is correct**: 128 RAMB18 for matrix_sram (64 element + 64 scale), 64 RAMB18 for vector_sram

2. **No BRAM merging**: `DONT_TOUCH` attribute ensures each subsram maps to its own RAMB18

3. **Single-cycle transposed access preserved**: The 64 independent BRAMs can all read different addresses simultaneously

4. **BRAM inference works without explicit attribute**: Vivado infers BRAM automatically due to:
   - Synchronous read pattern (registered output)
   - 1024 depth (large enough for BRAM preference)
   - Standard dual-port coding style

5. **Width efficiency**:
   - Element BRAMs: 14/18 = 78% width utilized
   - Scale BRAMs: 8/18 = 44% width utilized (some waste)
   - Vector BRAMs: 17/18 = 94% width utilized

---

## 7. Verification Checklist

- [x] Each subsram has exactly 1 RAMB18 in utilization report
- [x] No RAM merging warnings in vivado.log
- [x] `DONT_TOUCH` attribute present on all memory declarations
- [ ] (Optional) Simulation test for single-cycle transposed read timing
