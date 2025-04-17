// File: element_op_defs.svh

`ifndef OPERATION_SVH
`define OPERATION_SVH


parameter OPERAND_WIDTH = 3; // Number of bits to represent the operation
typedef enum logic [OPERAND_WIDTH-1:0] {
    ADD = 0,
    SUB = 1,
    MUL = 2,
    EXP = 3
} ELEMENT_V_OPERAND;

`endif
