# Memory Layout
# ================


## HBM Memory
Currently, two types of data type (High-Precision MXFP and Low-Precision MXFP) are supported in HBM memory.
- High-Precision MXFP: Q in (B, S, H, D), the block are stored together in HBM followed by the scales.
- Low-Precision MXFP: K, V in (B, S, H, D), the block are stored together in HBM followed by the scales.

The Data Region Required
- Q: `B * S * H * D`
- K: `B * S * H * D`
- V: `B * S * H * D`