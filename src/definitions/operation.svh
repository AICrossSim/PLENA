// File: element_op_defs.svh

`ifndef OPERATION_SVH
`define OPERATION_SVH


typedef enum logic [2:0] {
    ADD = 0,
    SUB = 1,
    MUL = 2,
    EXP = 3
} ELEMENT_V_OPERAND;

typedef enum logic [2:0] {
    SUM = 0,
    MAX = 1
} RED_V_OPERAND;


`endif
