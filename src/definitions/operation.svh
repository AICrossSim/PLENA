`ifndef OPERATION_SVH
`define OPERATION_SVH

parameter FIXED_OPERAND_WIDTH = 3;
parameter FP_OPERAND_WIDTH = 3;
parameter OPERAND_WIDTH = 3;
parameter OPCODE_WIDTH = 6;
parameter IMM_WIDTH = 7;
parameter IMM_2_WIDTH = 4;
parameter INSTRUCTION_LENGTH = 16;

typedef struct {
    logic w_m_sram_en;
    logic w_s_sram_port_a_en;
    logic w_s_sram_port_b_en;
} MEM_WEN_INFO;


typedef struct {
    logic wreq_m_sram;
    logic wreq_s_sram_port_a;
    logic wreq_s_sram_port_b;
} MEM_WREQ_INFO;

package instruction_pkg;
    parameter FIXED_OPERAND_WIDTH = 3;
    parameter FP_OPERAND_WIDTH = 3;
    parameter OPERAND_WIDTH = 3;
    parameter OPCODE_WIDTH = 6;
    parameter IMM_2_WIDTH = 4;
    parameter IMM_WIDTH = 7;
    parameter INSTRUCTION_LENGTH = 16;
endpackage

typedef enum logic [1:0] {
    MV          = 1,
    MV_O        = 2,
    STALL_M     = 0
} M_OP;

typedef enum logic [2:0] {
    ADD_V_ELEMENT   = 1,
    SUB_V_ELEMENT   = 2,
    MUL_V_ELEMENT   = 3,
    EXP_V_ELEMENT   = 4,
    STALL_V_ELEMENT = 0
} V_ELEMENT_OP;

typedef enum logic [2:0] {
    SUM_V_REDUCT    = 1,
    MAX_V_REDUCT    = 2,
    STALL_V_REDUCT  = 0
} V_REDUCT_OP;

typedef enum logic [3:0] {
    ADD_FP      = 1,
    SUB_FP      = 2,
    MAX_FP      = 3,
    MUL_FP      = 4,
    EXP_FP      = 5,
    RECI_FP     = 6,
    SQRT_FP     = 7,
    LD_REG_FP   = 8,
    LD_OUT_FP   = 9,
    ST_REG_FP   = 10,
    ST_IN_FP    = 11,
    STALL_S_FP  = 0
} S_FP_OP;

typedef enum logic [3:0] {
    ADD_FIX       = 1,
    ADDI_FIX      = 2,
    SUB_FIX       = 3,
    MUL_FIX       = 4,
    DIV_FIX       = 5,
    LUI_FIX       = 6,
    MV_FIX        = 7,
    LD_FIX        = 8,
    ST_FIX        = 9,
    PASS_ADDR     = 10,
    PASS_ADDR_2   = 11, // outputs rd adress.
    COMP_ADDR     = 12,
    STALL_S_FIXED = 0
} S_FIXED_OP;

typedef enum logic [1:0] {
    SET_ADDR_REG = 1,
    SET_M_OFFSET = 2,
    SET_LUT      = 3,
    STALL_C      = 0
} C_OP;

typedef enum logic [1:0] {
    STALL_H    = 0,
    PREFETCH_M = 1,
    PREFETCH_V = 2,
    STORE_V    = 3
} H_OP;


function automatic int max(input int a, input int b);
    return (a > b) ? a : b;
endfunction


typedef enum logic [OPCODE_WIDTH - 1:0] {
    // Invalid
    INVALID_OPCODE  = 6'h00,

    // Matrix Operation
    M_MV            = 6'h01,
    M_MV_O          = 6'h02,
    M_TMV           = 6'h03,
    M_TMV_O         = 6'h04,

    // Vector Operation
    V_ADD_VV        = 6'h05,
    V_ADD_VF        = 6'h06,
    V_SUB_VV        = 6'h07,
    V_SUB_VF        = 6'h08,
    V_MUL_VV        = 6'h09,
    V_MUL_VF        = 6'h0A,
    V_EXP_VV        = 6'h0B,
    V_RED_SUM       = 6'h0C,
    V_RED_MAX       = 6'h0D,

    // Scalar Operation (Floating-Point)
    S_ADD_FP        = 6'h0E,
    S_SUB_FP        = 6'h0F,
    S_MAX_FP        = 6'h10,
    S_MUL_FP        = 6'h11,
    S_EXP_FP        = 6'h12,
    S_RECI_FP       = 6'h13,
    S_SQRT_FP       = 6'h14,
    S_LD_FP         = 6'h15,
    S_ST_FP         = 6'h16,

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
    C_SET_LUT       = 6'h25
} CUSTOM_ISA_OPCODE;



typedef enum logic [2:0] { 
    M       = 0,
    V       = 1,
    S_FIX   = 2,
    S_FP    = 3,
    C       = 4,
    H       = 5,
    INVALID_TYPE = 6
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
    MEM_WEN_INFO    mem_write;
} OP_BUNDLE;

`endif
