## Design Space Constraints

### HW Parameters
- `MLEN` >= `BLEN`
- `MLEN` = `VLEN`
- `MLEN` % `BLEN` == 0
- `MATRIX_SRAM_DEPTH` >= `2 * MLEN`
- `VECTOR_SRAM_DEPTH` >= `2* head_dim + (hidden_dim // VLEN)`
- `INT_SRAM_DEPTH`  >= `num_hidden_layers * REPEAT_SETTINGS + FIXED_CONSTANT_NUM`
- `FP_SRAM_DEPTH`     >= `3 * MLEN + FP_CONSTANT_NUM`
- `HBM_M_Prefetch_Amount` >= `BLEN`
- `HBM_V_Prefetch_Amount` >= `BLEN`

### Precision Parameters

- `is_power_of_two`(`WT_MXFP_MANT_WIDTH` + `WT_MXFP_EXP_WIDTH`+1) == `True`
- `is_power_of_two`(`ACT_MXFP_MANT_WIDTH` + `ACT_MXFP_EXP_WIDTH`+1) == `True`
- `is_power_of_two`(`KV_MXFP_MANT_WIDTH` + `KV_MXFP_EXP_WIDTH`+1) == `True`