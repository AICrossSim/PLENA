# SiLU Activation

## Formula
```
SiLU(x) = x * sigmoid(x) = x / (1 + exp(-x))
```

## Shapes
- X: [batch, hidden]
- Y: [batch, hidden] (element-wise)

## Stages
1. Negate: -x
2. Exponential: exp(-x)
3. Add one: 1 + exp(-x)
4. Reciprocal: sigmoid = 1/(1 + exp(-x))
5. Multiply: x * sigmoid

## Output
IN-PLACE (overwrites input).
