# Flash Attention Layer

## Formula (Memory-Efficient)
```
O = softmax(Q @ K^T / sqrt(d)) @ V
```
Computed block-wise WITHOUT materializing full [seq, seq] attention matrix.

## Key Difference from Standard Attention
- Standard: O(seq^2) memory - materializes full attention matrix
- Flash: O(seq) memory - uses online softmax with block-wise computation

## Algorithm (per KV head)
```
Initialize: m = -inf, l = 0, O = 0
For each KV block j in [0, Tc):
    Load K_j, V_j from HBM to SRAM
    For each Q block i in [0, Tr):
        Load Q_i from HBM
        S_ij = Q_i @ K_j^T * scale        # [Br, Bc]
        m_new = max(m_old, rowmax(S_ij))  # running max
        P_ij = exp(S_ij - m_new)          # stable softmax numerator
        l_new = l_old * exp(m_old - m_new) + rowsum(P_ij)  # running sum
        O_new = O_old * exp(m_old - m_new) + P_ij @ V_j    # accumulate
        m_old = m_new, l_old = l_new
Final: O = O / l  # normalize
```

## Shapes
- Q: [batch, seq_q, num_heads, head_dim]
- K: [batch, seq_kv, num_kv_heads, head_dim]
- V: [batch, seq_kv, num_kv_heads, head_dim]
- Block sizes: Br (query block), Bc (key block) - typically MLEN=64

## Tiling Parameters
- Tr = ceil(seq_q / Br) - number of query blocks
- Tc = ceil(seq_kv / Bc) - number of KV blocks
- GQA: num_heads / num_kv_heads Q heads share each KV head

## Online Softmax State (per row)
- m: running maximum (init: -inf)
- l: running sum of exp (init: 0)
- O: running output accumulator (init: 0)

## FP SRAM Layout
- FP_SRAM[0] = 0.0 (zero constant)
- FP_SRAM[1] = 1/sqrt(head_dim) (qk_scale)
- FP_SRAM[2] = -inf (for m initialization)
- FP_SRAM[3+] = per-row m_old, m_res, l_old values

## Vector SRAM Layout
- Q block: [Br, head_dim]
- S/P block: [Br, Bc] - reused for scores and probabilities
- PV accumulator: [Br, head_dim]
- O_old: [Br, head_dim] - running output

## HBM Layout
- Q stored sequentially: [batch, seq_q, num_heads * head_dim]
- K stored after Q: [batch, seq_kv, num_kv_heads * head_dim]
- V stored after K: [batch, seq_kv, num_kv_heads * head_dim]

## Stages per Block
1. Prefetch K_j block from HBM to Matrix SRAM
2. Compute S = Q @ K^T (using M_BTMM for broadcast transpose matmul)
3. Scale: S = S * qk_scale
4. Online softmax update:
   - m_new = max(m_old, rowmax(S))
   - m_res = exp(m_old - m_new)
   - P = exp(S - m_new)
   - l_new = l_old * m_res + rowsum(P)
5. Prefetch V_j block from HBM
6. Compute PV = P @ V
7. Update O = O_old * m_res + PV
8. Update m_old = m_new, l_old = l_new

## Final Normalization
After all KV blocks: O = O / l (row-wise division)

## Output
Stored IN-PLACE at Q location (address 0).
