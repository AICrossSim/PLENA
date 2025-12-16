# Linear Layer

## Formula
```
Y = X @ W
```

## Shapes
- X: [batch, input_dim]
- W: [input_dim, output_dim]
- Y: [batch, output_dim]

## Stages
1. Matrix multiply only

## Output
Stored AFTER activations in VRAM.
