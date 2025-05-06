`ifndef OPERATION_SVH
`define OPERATION_SVH



parameter FIXED_OPERAND_WIDTH = 3;
parameter FP_OPERAND_WIDTH = 3;
parameter OPERAND_WIDTH = max(FIXED_OPERAND_WIDTH, FP_OPERAND_WIDTH);
parameter OPCODE_WIDTH = 6;
parameter IMM_WIDTH = 32;
parameter INSTRUCTION_LENGTH = 16;


package instruction_pkg;
    parameter FIXED_OPERAND_WIDTH = 3;
    parameter FP_OPERAND_WIDTH = 3;
    parameter OPERAND_WIDTH = max(FIXED_OPERAND_WIDTH, FP_OPERAND_WIDTH);
    parameter OPCODE_WIDTH = 6;
    parameter IMM_WIDTH = 32;
    parameter INSTRUCTION_LENGTH = 16;
endpackage

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
    ADD_FP    = 0,
    SUB_FP    = 1,
    MUL_FP    = 2,
    EXP_FP    = 3,
    RECI_FP   = 4,
    SQRT_FP   = 5,
    LD_REG_FP   = 6,
    LD_OUT_FP   = 7,
    ST_REG_FP  = 8,
    ST_IN_FP  = 9,
    STALL_S_FP = 10,
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
    STORE_V = 2,
    STALL_H = 3
} H_OP;

function automatic int max(input int a, input int b);
    return (a > b) ? a : b;
endfunction


typedef enum logic [OPCODE_WIDTH - 1:0] {
    // Matrix Operation
    M_MV        = 0x0,
    M_MV_O      = 0x1,
    M_TMV       = 2,
    M_TMV_O     = 3,

    // Vector Operation
    V_ADD_VV    = 0x4,
    V_ADD_VF    = 0x5,
    V_SUB_VV    = 0x6,
    V_SUB_VF    = 0x7,
    V_MUL_VV    = 0x8,
    V_MUL_VF    = 0x9,
    V_EXP_VV    = 0xa,
    V_RED_SUM   = 0xb,
    V_RED_MAX   = 0xc,

    // Scalar Operation
    S_ADD_FP    = 0xd,
    S_SUB_FP    = 0xe,
    S_MAX_FP    = 0xf,
    S_MUL_FP    = 0x10,
    S_EXP_FP    = 0x11,
    S_ISQRT_FP  = 0x12,
    S_LOG_FP    = 0x13,
    S_LOAD_FP   = 0x14,
    S_STORE_FP  = 0x15,
    S_ADD_FIX   = 0x16,
    S_ADDI_FIX  = 0x17,
    S_SUB_FIX   = 0x18,
    S_MUL_FIX   = 0x19,
    S_DIV_FIX   = 0x1a,
    S_LUI_FIX   = 0x1b,
    S_MV_FIX    = 0x1c,
    S_LD_FIX    = 0x1d,
    S_ST_FIX    = 0x1e,

    // Memory Operation
    H_PREFETCH_M    = 0x1f,
    H_PREFETCH_V    = 0x20,
    H_STORE_V       = 0x21,

    // CSR Setting
    C_SET_ADDR_REG  = 0x22,
    C_SET_M_OFFSET  = 0x23,
    C_SET_LUT       = 0x24,  // Left for Cano's work.

    INVALID_OPCODE  = 0x25
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
