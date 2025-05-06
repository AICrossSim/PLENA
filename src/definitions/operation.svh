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
    MV          = 0,
    MV_O        = 1,
    STALL_M     = 2
} M_OP;

typedef enum logic [2:0] {
    ADD_V_ELEMENT   = 0,
    SUB_V_ELEMENT   = 1,
    MUL_V_ELEMENT   = 2,
    EXP_V_ELEMENT   = 3,
    STALL_V_ELEMENT = 4
} V_ELEMENT_OP;

typedef enum logic [2:0] {
    SUM_V_REDUCT    = 0,
    MAX_V_REDUCT    = 1,
    STALL_V_REDUCT  = 2
} V_REDUCT_OP;

typedef enum logic [3:0] {
    ADD_FP      = 0,
    SUB_FP      = 1,
    MAX_FP      = 2,
    MUL_FP      = 3,
    EXP_FP      = 4,
    RECI_FP     = 5,
    SQRT_FP     = 6,
    LD_REG_FP   = 7,
    LD_OUT_FP   = 8,
    ST_REG_FP   = 9,
    ST_IN_FP    = 10,
    STALL_S_FP  = 11
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
    M_MV            = 6'h00,
    M_MV_O          = 6'h01,
    M_TMV           = 6'h02,
    M_TMV_O         = 6'h03,

    // Vector Operation
    V_ADD_VV        = 6'h04,
    V_ADD_VF        = 6'h05,
    V_SUB_VV        = 6'h06,
    V_SUB_VF        = 6'h07,
    V_MUL_VV        = 6'h08,
    V_MUL_VF        = 6'h09,
    V_EXP_VV        = 6'h0A,
    V_RED_SUM       = 6'h0B,
    V_RED_MAX       = 6'h0C,

    // Scalar Operation (Floating-Point)
    S_ADD_FP        = 6'h0D,
    S_SUB_FP        = 6'h0E,
    S_MAX_FP        = 6'h0F,
    S_MUL_FP        = 6'h10,
    S_EXP_FP        = 6'h11,
    S_RECI_FP       = 6'h12,
    S_SQRT_FP       = 6'h13,
    S_LD_REG_FP     = 6'h14,
    // S_LD_OUT_FP     = 6'h15,
    S_ST_REG_FP     = 6'h16,

    // Scalar Operation (Fixed-Point)
    S_ADD_FIX       = 6'h17,
    S_ADDI_FIX      = 6'h18,
    S_SUB_FIX       = 6'h19,
    S_MUL_FIX       = 6'h1A,
    S_DIV_FIX       = 6'h1B,
    S_LUI_FIX       = 6'h1C,
    S_MV_FIX        = 6'h1D,
    S_LD_FIX        = 6'h1E,
    S_ST_FIX        = 6'h1F,

    // Memory Operation
    H_PREFETCH_M    = 6'h20,
    H_PREFETCH_V    = 6'h21,
    H_STORE_V       = 6'h22,

    // CSR Setting
    C_SET_ADDR_REG  = 6'h23,
    C_SET_M_OFFSET  = 6'h24,
    C_SET_LUT       = 6'h25,

    // Invalid
    INVALID_OPCODE  = 6'h26
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
