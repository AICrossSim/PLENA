# Softmax Layer

## Formula (Numerically Stable)
```
softmax(x)_i = exp(x_i - max(x)) / sum(exp(x_j - max(x)))
```

## Shapes
- X: [batch, hidden]
- Y: [batch, hidden] (values sum to 1 per batch)

## Stages
1. Find max: max(x) per batch
2. Subtract max: x - max (for stability)
3. Exponential: exp(x - max)
4. Sum: sum(exp(...))
5. Reciprocal: 1 / sum
6. Normalize: exp(...) * (1/sum)

## Output
IN-PLACE (overwrites input).
