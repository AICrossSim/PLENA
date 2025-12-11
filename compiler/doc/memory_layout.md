# On-chip Vector SRAM Memory Layout Convention

By default, the memory layout follows this format:

Given an input tensor with shape `[b, s, h]` where:
- `b` = batch size
- `s` = sequence length
- `h` = hidden size

The data stored in Vector SRAM is reshaped to `[h // VLEN, b, s, VLEN]`.

**Rationale:** The hidden dimension is split along the `VLEN` boundary to enable efficient multi-batch GEMM operations. This layout allows parallel processing across batches while maintaining vector-length alignment requirements.

**Note:** Addresses are specified in units of data elements (not bytes).

### Example: Activation Tensor

For an activation tensor with shape `[batch=4, hidden=128]` and `VLEN=64`:

- Reshaped to: `[128//64, 4, 64]` = `[2, 4, 64]`
- Vector SRAM layout:
  - Address 0: First 64 elements of hidden dim for all batches
  - Address 256: Second 64 elements of hidden dim for all batches

# On-chip Matrix SRAM Memory Layout Convention

For a high-dimensional matrix stored in HBM, `(MLEN, MLEN)` tiles are extracted and stored in the On-chip Matrix SRAM using a **row-major tile layout**.

**Note:** Addresses are specified in units of data elements (not bytes).

## Tile Addressing

Each `(MLEN, MLEN)` tile is stored contiguously in row-major order. Tiles are addressed sequentially:

- **Address 0:** Tile (0, 0) - rows `[0..MLEN-1]`, columns `[0..MLEN-1]`
- **Address MLEN²:** Tile (0, 1) - rows `[0..MLEN-1]`, columns `[MLEN..2*MLEN-1]`
- **Address 2×MLEN²:** Tile (0, 2) - rows `[0..MLEN-1]`, columns `[2*MLEN..3*MLEN-1]`
- **Address (num_col_tiles)×MLEN²:** Tile (1, 0) - rows `[MLEN..2*MLEN-1]`, columns `[0..MLEN-1]`
- And so on...

**Rationale:** The matrix is tiled and stored in the On-chip Matrix SRAM to enable efficient matrix multiplication operations. This row-major tile layout allows parallel processing across tiles while maintaining matrix-length alignment requirements.

### Example: Weight Matrix

For a weight matrix with shape `[128, 128]` and `MLEN=64`:

- Tiled into `[2, 2]` blocks of `[64, 64]` each
- Matrix SRAM addresses (in element units):
  - Tile (0,0): Address 0 (rows 0-63, columns 0-63)
  - Tile (0,1): Address 4096 = 64×64 (rows 0-63, columns 64-127)
  - Tile (1,0): Address 8192 = 2×64×64 (rows 64-127, columns 0-63)
  - Tile (1,1): Address 12288 = 3×64×64 (rows 64-127, columns 64-127)

---


# Off-chip HBM Memory Convention
The data is assumed to be preloaded in the HBM with MX data type. For a data, such as the weight, the blocks of elements in (hidden, hidden) are stored together in HBM followed by the scales.
The data stored in HBM convention is as follows:
- activation tensor: (hidden, sequence_length, batch)
- weight matrix: (hidden, hidden)

To make the prefetch process aware of that data layout, we need the C_SET_SCALE_REG to set the scale offset for the prefetch instructions, so that the prefetch process can know the distance between the data blocks and their scale factors in HBM. 

To address MX-formatted weights in memory, compute the base plus the scale-block offset. For instance, when accessing the weight matrix, the address should be the address of the first element of the weight matrix plus the scales offset. That is hidden * sequence_length * batch_size * (data_size // 8) + ((hidden * sequence_length * batch_size) // block_dim) * (scale_width // 8)

After that, the accelerator will automatically convert them into the correct FP data layout in the On-chip Matrix SRAM. Also, during the prefetch process, the C_SET_STRIDE_REG will be used to set the stride size for the prefetch instructions.