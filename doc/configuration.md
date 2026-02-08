# Configuration Reference

PLENA uses TOML configuration files to define hardware parameters, precision settings, and optimization ranges.

## Configuration File Structure

The main configuration is located at `co_design/configs/config.toml`.

## Hardware Parameters (`CONFIG` Section)

| Parameter | Range | Description |
|-----------|-------|-------------|
| `BLEN` | 2-32 | Block length |
| `MLEN` | 2-512 | Matrix length |
| `VLEN` | 2-1024 | Vector length |
| `HBM_PREFETCH_MAT` | 2-256 | HBM prefetch amount for matrices |
| `HBM_PREFETCH_VEC` | 2-256 | HBM prefetch amount for vectors |
| `SRAM_DEPTH_MAT` | configurable | SRAM depth for matrix unit |
| `SRAM_DEPTH_VEC` | configurable | SRAM depth for vector unit |
| `SRAM_DEPTH_FP` | configurable | SRAM depth for FP unit |

### Example Hardware Configuration

```toml
[CONFIG.active]
BLEN = 16
MLEN = 128
VLEN = 256
HBM_PREFETCH_MAT = 64
HBM_PREFETCH_VEC = 32
```

## Precision Parameters (`PRECISION` Section)

| Parameter | Formats | Description |
|-----------|---------|-------------|
| `ACT_ELEMENT_WIDTH` | MXINT, MXFP | Activation element width |
| `KV_ELEMENT_WIDTH` | MXINT, MXFP | Key-Value cache element width |
| `FP_EXP_WIDTH` | 2-8 bits | Floating-point exponent width |
| `FP_MANT_WIDTH` | 2-12 bits | Floating-point mantissa width |

### Supported Precision Formats

```
MXFP4   - MX Floating Point 4-bit
MXFP6   - MX Floating Point 6-bit
MXFP8   - MX Floating Point 8-bit
MXINT4  - MX Integer 4-bit
MXINT8  - MX Integer 8-bit
FP16    - IEEE Half Precision
FP32    - IEEE Single Precision
```

### Example Precision Configuration

```toml
[PRECISION.active]
ACT_ELEMENT_WIDTH = "MXFP8"
KV_ELEMENT_WIDTH = "MXINT4"
FP_EXP_WIDTH = 5
FP_MANT_WIDTH = 10
```

## Configuration Modes

PLENA supports three configuration modes:

| Mode | Purpose |
|------|---------|
| `active` | Current working configuration |
| `SIMULATION` | Settings for simulation runs |
| `ASIC` | Settings for ASIC synthesis |

## Tunable Ranges

Define searchable parameter ranges for optimization:

```toml
[CONFIG.tunable]
BLEN = [2, 4, 8, 16, 32]
MLEN = [8, 16, 32, 64, 128, 256, 512]
VLEN = [16, 32, 64, 128, 256, 512, 1024]

[PRECISION.tunable]
ACT_ELEMENT_WIDTH = ["MXFP4", "MXFP6", "MXFP8", "MXINT4", "MXINT8"]
KV_ELEMENT_WIDTH = ["MXFP4", "MXFP6", "MXFP8", "MXINT4", "MXINT8"]
```

## Model Selection

Configure which LLaMA model to evaluate:

```toml
[MODEL]
name = "Meta-Llama/Meta-Llama-3-8B"
config_path = "doc/Model_Lib/llama-3-8b.json"
```

See [Model Library](models.md) for available models.
