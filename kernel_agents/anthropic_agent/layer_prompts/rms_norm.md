# RMS Norm Layer

## Formula
```
Y = X * rsqrt(mean(X^2) + eps)
```

## Shapes
- X: [batch, hidden]
- Y: [batch, hidden]

## Stages
1. Square elements: X^2
2. Reduce sum: sum(X^2)
3. Mean: sum / hidden_size
4. Add epsilon: mean + eps
5. Reciprocal sqrt: rsqrt
6. Scale: X * rsqrt

## Output
IN-PLACE (overwrites input).
