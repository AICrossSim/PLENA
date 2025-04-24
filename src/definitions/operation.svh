`ifndef OPERATION_SVH
`define OPERATION_SVH


typedef enum logic [2:0] {
    ADD = 0,
    SUB = 1,
    MUL = 2,
    EXP = 3,
    STALL = 4
} V_ELEMENT_OP;

typedef enum logic [2:0] {
    SUM = 0,
    MAX = 1,
    STALL = 2
} V_REDUCT_OP;


typedef enum logic [2:0] {
    ADD     = 0,
    SUB     = 1,
    MUL     = 2,
    ISQRT   = 3,
    LOG     = 4,
    EXP     = 5
} S_ALU_OP;


// TODO
typedef enum logic [4:0] {
    // Matrix Operation
    M_MV   = 0,
    M_TMV  = 1,

    // Vector Operation
    V_ADD_VV    = 2,
    V_ADD_VF    = 3,
    V_SUB_VV    = 4,
    V_SUB_VF    = 5,
    V_MUL_VV    = 6,
    V_MUL_VF    = 7,
    V_EXP_VV    = 8,
    V_RED_SUM   = 9,
    V_RED_MAX   = 10

} CUSTOM_ISA_OPCODE;

`endif
