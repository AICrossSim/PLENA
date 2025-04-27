`ifndef OPERATION_SVH
`define OPERATION_SVH

typedef enum logic [1:0] {
    MV = 0,
    TMV = 1,
    MV_TMV_STALL = 2
} M_OP;

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
    ADD_FP    = 0,
    SUB_FP    = 1,
    MUL_FP    = 2,
    EXP_FP    = 3,
    ISQRT_FP  = 4,
    LOG_FP    = 5,
    LOAD_FP   = 6,
    STALL     = 7
} S_FP_OP;

typedef enum logic [2:0] {
    ADD_FIX   = 0,
    ADDI_FIX   = 0,
    SUB_FIX   = 1,
    STALL     = 2
} S_FIXED_OP;


parameter FIXED_OPERAND_WIDTH = 3;
parameter FP_OPERAND_WIDTH = 3;
parameter OPERAND_WIDTH = MAX(FIXED_OPERAND_WIDTH, FP_OPERAND_WIDTH);
parameter OPCODE_WIDTH = 5;
parameter IMM_WIDTH = 32;

typedef enum logic [OPCODE_WIDTH - 1:0] {
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
    V_EXP_V    = 8,
    V_RED_SUM   = 9,
    V_RED_MAX   = 10,

    // Scalar Operation
    S_ADD_FP    = 11,
    S_SUB_FP    = 12,
    S_MAX_FP    = 13,
    S_MUL_FP    = 13,
    S_EXP_FP    = 14,
    S_ISQRT_FP  = 15,
    S_LOG_FP    = 16,
    S_ADD_FIX   = 17,
    S_ADDI_FIX  = 18,
    S_SUB_FIX   = 19,
    S_MUL_FIX   = 20,
    S_DIV_FIX   = 21,
    S_LUI_FIX   = 20,
    S_MV_FIX   = 21,


    // Memory Operation
    H_PREFETCH_M = 19,
    H_PREFETCH_V  = 20,
    H_LOAD_MATRIX = 21,
    H_LOAD_VECTOR = 22,
    H_LOAD_SCALAR = 23,
    H_STORE_VECTOR = 24,
    H_STORE_SCALAR = 25,
    H_STORE_HBM = 26,
    H_SET_HBM_OFFSET = 27,

    INVALID
} CUSTOM_ISA_OPCODE;

typedef enum logic [2:0] { 
    M = 0,
    V = 1,
    S = 2,
    H = 3
 } CUSTOM_ISA_TYPE;

parameter INSTRUCTION_LENGTH = 16;

typedef struct {
    logic [OPCODE_WIDTH - 1:0] opcode;
    logic [OPERAND_WIDTH:0] rs1;
    logic [OPERAND_WIDTH:0] rs2;
    logic [OPERAND_WIDTH:0] rd;
    logic [IMM_WIDTH - 1:0] imm;
    CUSTOM_ISA_TYPE instruction_type;
} INSTR_INFO;




`endif
