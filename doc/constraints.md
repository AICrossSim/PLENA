# Hardware Constraints

PLENA enforces strict constraints to ensure valid hardware configurations. These constraints are automatically checked during optimization.

## Hardware Parameter Constraints

### Matrix/Vector Length Relationships

| Constraint | Description |
|------------|-------------|
| `MLEN >= BLEN` | Matrix length must be at least block length |
| `MLEN = VLEN` | Matrix and vector lengths must match |
| `MLEN % BLEN == 0` | Matrix length must be divisible by block length |

### SRAM Depth Requirements

| Constraint | Description |
|------------|-------------|
| `MATRIX_SRAM_DEPTH >= 2 * MLEN` | Matrix SRAM needs 2x matrix length |
| `VECTOR_SRAM_DEPTH >= 2 * head_dim + (hidden_dim // VLEN)` | Vector SRAM based on model dimensions |
| `INT_SRAM_DEPTH >= num_hidden_layers * REPEAT_SETTINGS + FIXED_CONSTANT_NUM` | Integer SRAM for layer constants |
| `FP_SRAM_DEPTH >= 3 * MLEN + FP_CONSTANT_NUM` | FP SRAM for floating-point operations |

### HBM Prefetch Constraints

| Constraint | Description |
|------------|-------------|
| `HBM_M_Prefetch_Amount >= BLEN` | Matrix prefetch must be at least block length |
| `HBM_V_Prefetch_Amount >= BLEN` | Vector prefetch must be at least block length |

## Precision Parameter Constraints

### Bit Width Requirements

All precision formats must have power-of-two total bit widths:

```
is_power_of_two(WT_MXFP_MANT_WIDTH + WT_MXFP_EXP_WIDTH + 1) == True
is_power_of_two(ACT_MXFP_MANT_WIDTH + ACT_MXFP_EXP_WIDTH + 1) == True
is_power_of_two(KV_MXFP_MANT_WIDTH + KV_MXFP_EXP_WIDTH + 1) == True
```

Valid total bit widths: **2, 4, 8, 16, 32**

### Example Valid Configurations

| Format | Mantissa | Exponent | Sign | Total |
|--------|----------|----------|------|-------|
| MXFP4 | 2 | 1 | 1 | 4 |
| MXFP8 | 4 | 3 | 1 | 8 |
| FP16 | 10 | 5 | 1 | 16 |

## Constraint Validation

Constraints are validated in `co_design/search/utils.py`:

```python
def check_constraints(config: dict) -> bool:
    """
    Validates hardware configuration against all constraints.

    Returns:
        True if all constraints are satisfied
        False if any constraint is violated
    """
```

!!! warning "Invalid Configurations"
    Configurations that violate constraints are automatically pruned during optimization. The optimizer will skip these configurations and sample new ones.

## Common Constraint Violations

| Error | Cause | Solution |
|-------|-------|----------|
| `MLEN < BLEN` | Block length too large | Reduce BLEN or increase MLEN |
| `MLEN % BLEN != 0` | Incompatible lengths | Choose MLEN as multiple of BLEN |
| `SRAM overflow` | Insufficient SRAM depth | Increase SRAM depth or reduce MLEN |
| `Invalid bit width` | Non-power-of-two width | Adjust mantissa/exponent widths |
