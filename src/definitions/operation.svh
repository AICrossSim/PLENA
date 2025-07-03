`ifndef OPERATION_SVH
`define OPERATION_SVH

// TODO Remove this parameter definitions
parameter FIXED_OPERAND_WIDTH = 3;
parameter FP_OPERAND_WIDTH = 3;
parameter OPERAND_WIDTH = 3;
parameter OPCODE_WIDTH = 6;
parameter IMM_WIDTH = 7;
parameter IMM_2_WIDTH = 4;
parameter INSTRUCTION_LENGTH = 16;
parameter ON_CHIP_ADDR_WIDTH = 32;

typedef struct {
    logic w_m_sram_en;
    logic w_s_sram_port_a_en;
    logic w_s_sram_port_b_en;
    logic w_from_m;
} MEM_WEN_INFO;


typedef struct {
    logic wreq_m_sram;
    logic wreq_s_sram_port_a;
    logic wreq_s_sram_port_b;
    logic wreq_from_m;
} MEM_WREQ_INFO;

typedef enum logic [2:0] {
    MV              = 3'h1,
    MV_O            = 3'h2,
    MM_IC           = 3'h3,
    MM_PS           = 3'h4,
    MM_WO           = 3'h5,
    STALL_M         = 3'h0
} M_OP;

typedef enum logic [2:0] {
    STALL_V_ELEMENT = 3'h0,
    ADD_V_ELEMENT   = 3'h1,
    SUB_V_ELEMENT   = 3'h2,
    MUL_V_ELEMENT   = 3'h3,
    EXP_V_ELEMENT   = 3'h4,
    LD_V_ELEMENT    = 3'h5
} V_ELEMENT_OP;

typedef enum logic [2:0] {
    STALL_V_REDUCT  = 3'h0,
    SUM_V_REDUCT    = 3'h1,
    MAX_V_REDUCT    = 3'h2
} V_REDUCT_OP;

typedef enum logic [3:0] {
    STALL_S_FP  = 4'h0,
    ADD_FP      = 4'h1,
    SUB_FP      = 4'h2,
    MAX_FP      = 4'h3,
    MUL_FP      = 4'h4,
    EXP_FP      = 4'h5,
    RECI_FP     = 4'h6,
    SQRT_FP     = 4'h7,
    LD_REG_FP   = 4'h8,
    LD_OUT_FP   = 4'h9,
    ST_REG_FP   = 4'hA,
    ST_IN_FP    = 4'hB,
    MV_FP       = 4'hC
} S_FP_OP;

typedef enum logic [3:0] {
    ADD_FIX       = 4'h1,
    ADDI_FIX      = 4'h2,
    SUB_FIX       = 4'h3,
    MUL_FIX       = 4'h4,
    DIV_FIX       = 4'h5,
    LUI_FIX       = 4'h6,
    MV_FIX        = 4'h7,
    LD_FIX        = 4'h8,
    ST_FIX        = 4'h9,
    PASS_ADDR     = 4'hA,
    PASS_ADDR_2   = 4'hB, // addr_port_2: rd and addr_port_1: rs1 adress.
    COMP_ADDR     = 4'hC,
    STALL_S_FIXED = 0
} S_FIXED_OP;

typedef enum logic [1:0] {
    STALL_C         = 2'h0,
    SET_ADDR_REG    = 2'h1,
    SET_STRIDE_SIZE = 2'h2,
    SET_LUT         = 2'h3
} C_OP;

typedef enum logic [2:0] {
    STALL_H      = 3'h0,
    PREFETCH_M_C = 3'h1,
    PREFETCH_M_S = 3'h2,
    PREFETCH_V_C = 3'h3,
    PREFETCH_V_S = 3'h4,
    STORE_V_C    = 3'h5,
    STORE_V_S    = 3'h6
} H_OP;

function automatic int max(input int a, input int b);
    return (a > b) ? a : b;
endfunction


typedef enum logic [OPCODE_WIDTH - 1:0] {
    // Invalid
    INVALID_OPCODE      = 6'h00,

    // Matrix Operations
    M_MM_IC             = 6'h01,
    M_MM_PS             = 6'h02,
    M_MM_WO             = 6'h03,
    M_TMM_IC            = 6'h04,
    M_TMM_PS            = 6'h05,
    M_TMM_WO            = 6'h06,
    M_MV                = 6'h07,
    M_MV_O              = 6'h08,
    M_TMV               = 6'h09,
    M_TMV_O             = 6'h0A,

    // Vector Operations
    V_ADD_VV            = 6'h0B,
    V_ADD_VF            = 6'h0C,
    V_SUB_VV            = 6'h0D,
    V_SUB_VF            = 6'h0E,
    V_MUL_VV            = 6'h0F,
    V_MUL_VF            = 6'h10,
    V_EXP_VV            = 6'h11,
    V_LD_F              = 6'h12,
    V_RED_SUM           = 6'h13,
    V_RED_MAX           = 6'h14,

    // Scalar Operations (Floating-Point)
    S_ADD_FP            = 6'h15,
    S_SUB_FP            = 6'h16,
    S_MAX_FP            = 6'h17,
    S_MUL_FP            = 6'h18,
    S_EXP_FP            = 6'h19,
    S_RECI_FP           = 6'h1A,
    S_SQRT_FP           = 6'h1B,
    S_MV_FP             = 6'h1C,
    S_LD_FP             = 6'h1D,
    S_ST_FP             = 6'h1E,

    // Scalar Operations (Fixed-Point)
    S_ADD_FIX           = 6'h1F,
    S_ADDI_FIX          = 6'h20,
    S_SUB_FIX           = 6'h21,
    S_MUL_FIX           = 6'h22,
    S_DIV_FIX           = 6'h23,
    S_LUI_FIX           = 6'h24,
    S_MV_FIX            = 6'h25,
    S_LD_FIX            = 6'h26,
    S_ST_FIX            = 6'h27,

    // Memory Operations
    H_PREFETCH_M_C      = 6'h28,
    H_PREFETCH_M_S      = 6'h29,
    H_PREFETCH_V_C      = 6'h2A,
    H_PREFETCH_V_S      = 6'h2B,
    H_STORE_V_C         = 6'h2C,
    H_STORE_V_S         = 6'h2D,

    // CSR Setting
    C_SET_ADDR_REG      = 6'h2E,
    C_SET_LUT           = 6'h2F,
    C_SET_STRIDE_REG    = 6'h30
} CUSTOM_ISA_OPCODE;

typedef enum logic [2:0] {
    INVALID_TYPE = 3'h0,
    M            = 3'h1,
    V            = 3'h2,
    S_FIX        = 3'h3,
    S_FP         = 3'h4,
    C            = 3'h5,
    H            = 3'h6
} CUSTOM_ISA_TYPE;

typedef struct {
    logic [OPCODE_WIDTH - 1:0]  opcode;
    logic [OPERAND_WIDTH:0]     rs1;
    logic [OPERAND_WIDTH:0]     rs2;
    logic [OPERAND_WIDTH:0]     rd;
    logic [IMM_WIDTH - 1:0]     imm;
    CUSTOM_ISA_TYPE instruction_type;
} INSTR_INFO;

// TODO: The definition is not very efficient, might need to be optimized later.
typedef struct {
    M_OP            m_op;
    V_ELEMENT_OP    v_ele_op;
    V_REDUCT_OP     v_reduct_op;
    S_FP_OP         s_fp_op;
    C_OP            c_op;
    H_OP            h_op;
    logic           m_transposed_read;
    logic           v_broadcast_en;
    logic [FP_OPERAND_WIDTH - 1:0]      fps1;
    logic [FP_OPERAND_WIDTH - 1:0]      fps2;
    logic [FP_OPERAND_WIDTH - 1:0]      fpd;
    logic [FIXED_OPERAND_WIDTH - 1:0]   fixed_rs1;
    logic [FIXED_OPERAND_WIDTH - 1:0]   fixed_rs2;
    logic [FIXED_OPERAND_WIDTH - 1:0]   fixed_rd;
    logic [ON_CHIP_ADDR_WIDTH - 1:0]    addr_1;
    logic [ON_CHIP_ADDR_WIDTH - 1:0]    addr_2;
    logic update_m_waddr;
    logic update_v_waddr;
} OP_BUNDLE;

`endif
