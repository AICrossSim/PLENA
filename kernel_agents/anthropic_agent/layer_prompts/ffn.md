# FFN (Feed-Forward Network) Layer

## Formula (SwiGLU)
```
Y = down(SiLU(up(X)) * gate(X))
```
Where SiLU(x) = x * sigmoid(x)

## Shapes
- X: [batch, hidden]
- W_up: [hidden, intermediate]
- W_gate: [hidden, intermediate]
- W_down: [intermediate, hidden]
- Y: [batch, hidden]

## 5 Stages
1. up_out = X @ W_up (matrix multiply)
2. gate_out = X @ W_gate (matrix multiply)
3. silu_up = SiLU(up_out) (vector ops)
4. hidden = silu_up * gate_out (element-wise)
5. Y = hidden @ W_down (matrix multiply)

## HBM Layout
3 weight matrices stored sequentially after activations.

## Output
Stored IN-PLACE at address 0.
