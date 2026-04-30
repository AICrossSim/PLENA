# SimTop Correctness Test Debug — Session Summary

**Date**: 2026-03-15
**Branch**: kev/aten
**Goal**: Fix PLENA RTL SimTop correctness test to achieve ≥80% allclose for Y = X @ W (16×16 MXFP8 matrix multiply)
**Config**: MLEN=16, BLEN=8, VLEN=16, BLOCK_DIM=8, ACC_NUM=2

---

## Current Status: 0 rows captured (still failing)

---

## Fixes Applied (4 files modified)

1. **`src/frontend/rtl/decoder.sv:259`** — Set `update_m_waddr=1` for M_MM_WO opcode
   - Root cause: `writeback_buffer_controller` never enabled → `block_data_buffer` join2 never fires → 0 output rows
   - Fix: `decode_stage_op.update_m_waddr <= (decode_instr_info.opcode == M_MM_WO) ? 1'b1 : 1'b0;`

2. **`src/memory/HBM/rtl/tl_master.sv`** — total_response_counter fix (prior session)

3. **`src/memory/matrix_sram/rtl/matrix_sram_without_rounding.sv`** — data_not_ready always-update fix (prior session)

4. **`src/core/rtl/plena.sv`** — m_prefetch_en one-shot fix (prior session)

---

## What the Simulation Log Shows

The SimTop log reveals the pipeline **never starts HBM prefetch for matrix data**:

```
instr=1/1   — stuck at instruction 1 forever
hbm_m_pf=0  — HBM M-path prefetch never fires
hbm_m_req=0 — HBM never requested for M-path
m_in_prep=0 — m_load_in_process never asserts
m_not_rdy=1 — matrix data not ready (from cycle ~46 onward)
m_m_v=0     — matrix machine M-valid never asserts
```

The V-path (activation) prefetch works fine (`hbm_v_pf=1` fires around cycle 38). The M-path (weight) prefetch **never fires**. No GEMM computation ever starts → 0 output rows.

---

## Root Cause Hypothesis

The `H_PREFETCH_M` instruction is not triggering HBM M-path prefetch. Likely causes:
- The `m_prefetch_en` one-shot fix in `plena.sv` may be too aggressive (not re-arming for subsequent prefetches)
- `data_flow_control.sv` may not be enabling `m_load_in_process` correctly
- The instruction pipeline may be stalling before reaching `H_PREFETCH_M`

---

## matrix_machine_tb Result

Also fails with "MM_WO drain timeout" — but this is a **test bug**, not an RTL bug:
- `control_in_exe` never returns to `STALL_M` after MM_WO (by design — it only updates on non-STALL commands)
- The data path may actually work; the test just checks the wrong completion condition

---

## Next Steps

1. **Investigate why `hbm_m_req=0` always** — trace `H_PREFETCH_M` through:
   - `data_flow_control.sv` → `plena.sv` → `hbm_sys.sv`
2. **Check `m_prefetch_en` one-shot fix** in `plena.sv` — may not re-arm properly
3. **Check `data_flow_control.sv`** — `m_load_in_process` logic and HBM M-path prefetch enable
4. **Fix matrix_machine_tb** — change completion check from `cie==STALL_M` to monitoring `output_reset` or output valid

---

## Key Files to Read

| File | Why |
|------|-----|
| `src/core/rtl/plena.sv` | m_prefetch_en one-shot fix — likely culprit |
| `src/core/rtl/data_flow_control.sv` | m_load_in_process, hbm_m_req_prefetch_data |
| `src/memory/HBM/rtl/hbm_sys.sv` | HBM M-path prefetch FSM |
| `src/frontend/rtl/decoder.sv` | update_m_waddr fix (confirmed present) |
| `src/system/test/SimTop_correctness_tb.py` | test + generated ASM |
| `src/matrix_machine/rtl/matrix_machine_v2.sv` | wait_for_output, writeback wiring |
| `src/basic_components/systolic_gemm_mx/rtl/mx_systolic_mcu.sv` | MCU drain/empty_in_progress |
| `src/basic_components/systolic_gemm_mx/rtl/block_data_buffer.sv` | ACC_NUM trigger condition |
| `src/matrix_machine/rtl/writeback_buffer_controller.sv` | acc_waddr counter |

---

## Generated ASM

`src/system/test/build/SimTopCorrectness/generated_asm_code.asm`

Key layout: gp9=256 (output VRAM base), W at HBM byte 320 (a0=320), X scale at byte 256.

---

## Architecture Notes

- `block_data_buffer` trigger: `acc_waddr == ACC_NUM-1 && write_to_buffer_valid && wait_for_output`
- `writeback_buffer_controller` uses internal counter (0,1,0,1...) not instruction addr fields
- `wait_for_output` set to 1 when `matrix_opcode == MM_WO`, cleared when `result_out_valid`
- `control_in_exe` in MCU only updates when `control != STALL_M` — never resets to STALL_M after drain
- Scale addressing: `C_SET_SCALE_REG` sets `stored_v_scale_offset` (V/X path); `stored_m_scale_offset` stays 0 → W scales always at byte 0
