`ifndef OPERATION_SVH
`define OPERATION_SVH


typedef enum logic [2:0] {
    ADD = 0,
    SUB = 1,
    MUL = 2,
    EXP = 3,
    STALL = 4
} ELEMENT_V_OPERAND;

typedef enum logic [2:0] {
    SUM = 0,
    MAX = 1,
    STALL = 2
} RED_V_OPERAND;


// TODO
typedef enum logic [4:0] {
    V_ADD   = 0,
    V_SUB   = 1,
    V_MULT  = 2,
    V_EXP   = 3,
    V_SUM   = 4,
    V_MAX   = 5
} CUSTOM_ISA;

`endif
