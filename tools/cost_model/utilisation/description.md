# Resource Utilisation Cost Model

## Components to Consider:
- Matrix Machine
- Matrix SRAM
- Vector Machine
- Vector SRAM
- Scalar Machine
- INT SRAM
- FP SRAM
- HBM System
- Control (Including Pipeline Control and Dataflow Control, which are fixed)

## Matrix Machine
Related Parameters:
- `MLEN` and `BLEN`, these two parameters determine the size of the systolic mcu. The resource utilisation for systolic mcu should be proportional to `MLEN * BLEN`.