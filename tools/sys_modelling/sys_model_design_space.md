# System Level Model Design Space

## Hardware Search Space

### Memory Unit Config

| Component | Options |
|-----------|---------|
| **Matrix SRAM** | On-chip SRAM / 3D Stacked / Combined |
| **Off-chip Storage** | HBM / DDR / Combined|

### Compute Unit Config

| Component | Options |
|-----------|---------|
| **PLENA Core Number** | 1 / 2 / 4 / 8 |
| **Matrix Compute** | MLEN, BLEN, HLEN |
| **Vector Compute** | VLEN |
| **ACT Precision** | FP, MXFP, MXINT |
| **KV Precision** | FP, MXFP, MXINT |
| **Weight Precision** | FP, MXFP, MXINT |

## Software Search Space

### FFN Layer

*Operations: Upsize Linear, Gate Projection, SILU Activation, Downsize Linear*

#### Search Space

| Component | Options |
|-----------|---------|
| **Execution Order** (Upsize, Gate, Downsize) | Output Stationary / Activation Stationary / Weight Stationary |
| **On-Chip Storage Priority** | Weight Priority / Activation Priority |

### Flash Attention Layer

*Operations: QKT Multiplication, Softmax, PV Computation, O Computation*

#### Search Space

| Component | Options |
|-----------|---------|
| **Execution Order** (Head Iteration) | Iterate Over Q Head / Iterate Over KV Head |
| **Soft Tiling Size** | Bc and Br | 
| **On-Chip Storage Priority** | KV Priority / Weight Priority |