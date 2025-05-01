`ifndef OPERATION_SVH
`define OPERATION_SVH

typedef enum logic [1:0] {
    MV      = 0,
    MV_O    = 1,
    STALL_M   = 2
} M_OP;

typedef enum logic [2:0] {
    ADD_V_ELEMENT = 0,
    SUB_V_ELEMENT = 1,
    MUL_V_ELEMENT = 2,
    EXP_V_ELEMENT = 3,
    STALL_V_ELEMENT = 4
} V_ELEMENT_OP;

typedef enum logic [2:0] {
    SUM_V_REDUCT = 0,
    MAX_V_REDUCT = 1,
    STALL_V_REDUCT = 2
} V_REDUCT_OP;

typedef enum logic [3:0] {
    ADD_FP      = 0,
    SUB_FP      = 1,
    MUL_FP      = 2,
    EXP_FP      = 3,
    ISQRT_FP    = 4,
    LOG_FP      = 5,
    LD_REG_FP   = 6,
    LD_OUT_FP   = 7,
    ST_REG_FP   = 8,
    ST_IN_FP    = 9,
    STALL_S_FP  = 10
} S_FP_OP;

typedef enum logic [3:0] {
    ADD_FIX   = 0,
    ADDI_FIX  = 1,
    SUB_FIX   = 2,
    MUL_FIX   = 3,
    DIV_FIX   = 4,
    LUI_FIX   = 5,
    MV_FIX    = 6,
    LD_FIX    = 7,
    ST_FIX    = 8,
    COMP_ADDR = 9,
    CONCAT    = 10,
    STALL_S_FIXED = 11
} S_FIXED_OP;


typedef enum logic [1:0] {
    SET_ADDR_REG = 0,
    SET_M_OFFSET = 1,
    SET_LUT = 2,
    STALL_C = 3
} C_OP;

typedef enum logic [1:0] {
    PREFETCH_M = 0,
    PREFETCH_V = 1,
    STORE_V_HBM = 2,
    STALL_H = 3
} H_OP;

function automatic int max(input int a, input int b);
    return (a > b) ? a : b;
endfunction

package instruction_pkg;
    parameter FIXED_OPERAND_WIDTH = 3;
    parameter FP_OPERAND_WIDTH = 3;
    parameter OPERAND_WIDTH = max(FIXED_OPERAND_WIDTH, FP_OPERAND_WIDTH);
    parameter OPCODE_WIDTH = 6;
    parameter IMM_WIDTH = 32;
    parameter INSTRUCTION_LENGTH = 16;
endpackage


typedef enum logic [OPCODE_WIDTH - 1:0] {
    // Matrix Operation
    M_MV        = 0,
    M_MV_O      = 1,
    M_TMV       = 2,
    M_TMV_O     = 3,

    // Vector Operation
    V_ADD_VV    = 4,
    V_ADD_VF    = 5,
    V_SUB_VV    = 6,
    V_SUB_VF    = 7,
    V_MUL_VV    = 8,
    V_MUL_VF    = 9,
    V_EXP_VV    = 10,
    V_RED_SUM   = 11,
    V_RED_MAX   = 12,

    // Scalar Operation
    S_ADD_FP    = 13,
    S_SUB_FP    = 14,
    S_MAX_FP    = 15,
    S_MUL_FP    = 16,
    S_EXP_FP    = 17,
    S_ISQRT_FP  = 18,
    S_LOG_FP    = 19,
    S_LOAD_FP   = 20,
    S_STORE_FP  = 21,
    S_ADD_FIX   = 22,
    S_ADDI_FIX  = 23,
    S_SUB_FIX   = 24,
    S_MUL_FIX   = 25,
    S_DIV_FIX   = 26,
    S_LUI_FIX   = 27,
    S_MV_FIX    = 28,
    S_LD_FIX    = 29,
    S_ST_FIX    = 30,

    // Memory Operation
    H_PREFETCH_M    = 31,
    H_PREFETCH_V    = 32,
    H_STORE_V_HBM   = 33,

    // CSR Setting
    C_SET_ADDR_REG = 34,
    C_SET_M_OFFSET  = 35,
    C_SET_LUT        = 36,  // Left for Cano's work.

    INVALID_OPCODE   = 37
} CUSTOM_ISA_OPCODE;

typedef enum logic [2:0] { 
    M = 0,
    V = 1,
    S = 2,
    C = 3,
    H = 4,
    INVALID_TYPE = 5
 } CUSTOM_ISA_TYPE;

typedef struct {
    logic [OPCODE_WIDTH - 1:0]  opcode;
    logic [OPERAND_WIDTH:0]     rs1;
    logic [OPERAND_WIDTH:0]     rs2;
    logic [OPERAND_WIDTH:0]     rd;
    logic [IMM_WIDTH - 1:0]     imm;
    CUSTOM_ISA_TYPE instruction_type;
} INSTR_INFO;

typedef struct {
    M_OP            m_op;
    V_ELEMENT_OP    v_ele_op;
    V_REDUCT_OP     v_reduct_op;
    S_FP_OP         s_fp_op;
    S_FIXED_OP      s_fixed_op;
    C_OP            c_op;
    H_OP            h_op;
    logic           m_transposed_read;
    logic           v_broadcast_en;
    logic           stall_for_memory;
} OP_BUNDLE;


`endif
