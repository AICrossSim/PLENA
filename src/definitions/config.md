# Accelerator's Design Space and Tuning Method
## Tuning Method

You can customise build parameters using the `make set` command:

```bash
make set CONFIG="VLEN=4 MLEN=123" MODE=ASIC
```

### Arguments

- **MODE**  
  Specifies the target environment. Available options:
  - `ASIC` : Only includes the core configurations.
  - `SIMULATION` : Includes additional configurations for simulation environments, such as fake HBM memory and other simulation-specific settings.

- **CONFIG**  
  A string of one or more key-value pairs to override default parameters. Use this to tune individual or multiple settings at once. 

### Example Usage

To set `VLEN` to 4 and `MLEN` to 123 for the ASIC mode:

```bash
make set CONFIG="VLEN=4 MLEN=123" MODE=ASIC
```

To set `ACT_MXFP_MANT_WIDTH` to 8 for the ASIC mode:
```bash
 make set PRECISION="ACT_MXFP_MANT_WIDTH=8"
```

This approach enables flexible, fine-grained control over build configurations for different deployment targets.

## Design Space Constraints

### Configuration Parameters
- `MLEN` >= `BLEN`
<!-- - `MLEN` = `VLEN` -->
- `MLEN` % `BLEN` == 0
- `MATRIX_SRAM_DEPTH` >= `2 * MLEN`
- `VECTOR_SRAM_DEPTH` >= `2* head_dim + (hidden_dim // VLEN)`
<!-- - `INT_SRAM_DEPTH`  >= 16 -->
- `INT_SRAM_DEPTH`  >= `16`
- `FP_SRAM_DEPTH`     >= `3 * MLEN + FP_CONSTANT_NUM`
<!-- - `HBM_M_Prefetch_Amount` >= `BLEN`
- `HBM_V_Prefetch_Amount` >= `BLEN` -->
- `(MLEN * ACT_ELEMENT_WIDTH + (MLEN // BLOCK_DIM) * ACT_SCALE_WIDTH) < 1510` Assuming 1GHz, 1TB/s bandwidth
- `(VLEN * ACT_ELEMENT_WIDTH + (VLEN // BLOCK_DIM) * ACT_SCALE_WIDTH) < 1510` Assuming 1GHz, 1TB/s bandwidth
- `(MLEN * ACT_ELEMENT_WIDTH + (MLEN // BLOCK_DIM) * ACT_SCALE_WIDTH) < 1510` Assuming 1GHz, 1.5TB/s bandwidth
- `(VLEN * ACT_ELEMENT_WIDTH + (VLEN // BLOCK_DIM) * ACT_SCALE_WIDTH) < 1510` Assuming 1GHz, 1.5TB/s bandwidth

### Precision Parameters