# Attention Layer

## Formula
```
Output = softmax(Q @ K^T / sqrt(head_dim)) @ V
```

## How To Approach This Problem

Follow a **top-down decomposition**:
1. **Shapes first** - What are we working with? Write dimensions as comments.
2. **Stages** - What are the major computational steps?
3. **Substeps** - What does each stage actually require? (especially softmax)
4. **Loop structure** - How do we iterate over all queries?
5. **Verify** - Did we cover all output elements?

Do NOT start writing code until you complete steps 1-4 in your thinking.

## STEP 1: Write Down Shapes First (MANDATORY)

Before writing ANY code, compute and write these as comments:
```
Q: [batch, seq_q, num_heads, head_dim] = [?, ?, ?, ?] → total ? elements
K: [batch, seq_kv, num_kv_heads, head_dim] = [?, ?, ?, ?]
V: [batch, seq_kv, num_kv_heads, head_dim] = [?, ?, ?, ?]
Scores per query: [seq_kv] (one score per KV position)
Output: [batch, seq_q, num_heads, head_dim] → total ? elements

Total queries to process: batch × seq_q × num_heads = ?
Each query produces: head_dim output values
```

## STEP 2: Break Into 4 Stages

For EACH query vector Q[i] (there are batch × seq_q × num_heads of them):

| Stage | What | Math | Output |
|-------|------|------|--------|
| 1 | Compute scores | S[j] = dot(Q[i], K[j]) × scale | [seq_kv] scalars |
| 2 | Find max | max_s = max(S) | 1 scalar |
| 3 | Softmax | W = exp(S - max_s) / sum(exp(S - max_s)) | [seq_kv] weights |
| 4 | Weighted sum | O[i] = sum(W[j] × V[j]) | [head_dim] vector |

## STEP 3: Softmax Substeps (CRITICAL - Do Not Skip!)

Softmax is NOT just dividing by a constant. It requires ALL of these:
```
1. max_s = max(scores)              ← for numerical stability
2. shifted = scores - max_s         ← subtract max from each score
3. exp_scores = exp(shifted)        ← exponentiate each score
4. sum_exp = sum(exp_scores)        ← sum of all exponentials
5. weights = exp_scores / sum_exp   ← normalize to get probabilities
```

If you skip any step, the output will be WRONG.

## STEP 4: Loop Structure

```
for each query (batch × seq_q × num_heads iterations):

    # Stage 1: Compute ALL scores for this query
    for j in range(seq_kv):
        scores[j] = dot(Q[query_idx], K[j]) × qk_scale

    # Stage 2-3: Softmax (ALL substeps!)
    max_s = max(scores)
    shifted = scores - max_s
    exp_scores = exp(shifted)
    sum_exp = sum(exp_scores)
    weights = exp_scores / sum_exp

    # Stage 4: Weighted sum of V
    output = zeros(head_dim)
    for j in range(seq_kv):
        output += weights[j] × V[j]

    # Store output for this query
```

## STEP 5: Verify Completeness

Before submitting, answer:
- Total queries = batch × seq_q × num_heads = ?
- My outer loop runs ? times
- Do they match? If NO → code is incomplete

## Memory Layout

```
Vector SRAM:
  [0, Q_end)           : Q data (input, becomes output in-place)
  [K_start, K_end)     : K data
  [V_start, V_end)     : V data
  [scratch, ...)       : scores array [seq_kv], temp storage

FP SRAM (preloaded):
  FP_SRAM[0] = 0.0
  FP_SRAM[1] = 1/sqrt(head_dim) = qk_scale
  FP_SRAM[2] = -inf (for masking if needed)
```

## Common Mistakes

1. **Skipping softmax** - Using raw scores or dividing by constant instead of exp/sum
2. **Missing exp()** - Must exponentiate after subtracting max
3. **Missing max subtraction** - Causes numerical overflow
4. **Incomplete loops** - Not processing all batch × seq_q × num_heads queries
5. **Wrong accumulation** - Forgetting to zero-initialize output before accumulating
