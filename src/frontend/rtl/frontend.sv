`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Frontend
Timing      : Sequential
Description : This module serves as the frontend of this coprocessor, it includes decoder, pipeline scheduler, and address mapper.
              The decoder decodes the instruction and generates control signals for the rest of the system.
              The pipeline scheduler schedules the instructions
              The address mapper maps the addresses for the data and instructions for HBM
*/

module frontend #(
    parameter INSTRUCTION_LENGTH    = 16,
    parameter OPERAND_WIDTH         = 5,
    parameter FIXED_OPERAND_WIDTH   = 5,
    parameter FP_OPERAND_WIDTH      = 3,
    parameter OPCODE_WIDTH          = 4,
    parameter IMM_WIDTH             = 32,
    parameter INST_BUFF_DEPTH       = 8
    // parameter LOOKAHEAD_EN          = 1
)(
    input   logic clk,
    input   logic rst,

    // Instruction
    input   logic [INSTRUCTION_LENGTH - 1 : 0] instruction,
    input   logic instruction_valid,
    output  logic instruction_ready

    // Control HBM Data Prefetch
    input   logic hbm_m_prefetch_complete,
    output  logic hbm_m_prefetch_en,
    input   logic hbm_v_prefetch_complete,
    output  logic hbm_v_prefetch_en,

    output  logic hbm_v_write_en,

    // Control Memory Data Retrieval 
    output  logic read_from_m_sram_en,
    output  logic transposed_read_from_m_sram_en,
    output  logic read_from_s_sram_en,

    // Control Matrix Computation
    output  M_OP          matrix_opcode,
    // input   logic last_matrix_complete,

    // Control Vector Computation
    output  V_ELEMENT_OP      element_opcode,
    output  V_REDUCT_OP       reduce_opcode,
    input   logic broadcast_fp2
    // input   logic last_vector_complete,

    // Control Scalar Computation

    output S_FIXED_OP        fixed_opcode,
    output logic [IMM_WIDTH -1 : 0]                 imm,
    output logic [FIXED_OPERAND_WIDTH - 1 : 0]      rs1,
    output logic [FIXED_OPERAND_WIDTH - 1 : 0]      rs2,
    output logic [FIXED_OPERAND_WIDTH - 1 : 0]      rd,

    output S_FP_OP           fp_opcode,
    output logic [FP_OPERAND_WIDTH - 1 : 0]        fps1,
    output logic [FP_OPERAND_WIDTH - 1 : 0]        fps2,
    output logic [FP_OPERAND_WIDTH - 1 : 0]        fpd
);


// Pipeline Control
logic stall;

// Machine Control
INSTR_INFO current_instr_info, next_instr_info;
logic read_next_instr, decode_instr_valid;

always_comb begin
    if (decode_instr_valid) begin
        case(current_instr_info.opcode)
            M: begin
                matrix_opcode = (current_instr_info.opcode == M_MV) ? M_MV : M_TMV;
                element_opcode = STALL;
                reduce_opcode  = STALL;
                fp_opcode      = STALL;
                fixed_opcode   = LOAD_FOR_ADDR;
                fp_rs1 = {FP_OPERAND_WIDTH{1'0}};
                fp_rs2 = {FP_OPERAND_WIDTH{1'0}};
                fp_rd  = {FP_OPERAND_WIDTH{1'0}};
                rs1 = current_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                rs2 = current_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                rd  = current_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
                imm = '0;
            end

            V: begin
                matrix_opcode = STALL;
                element_opcode = (current_instr_info.opcode == V_ADD_VV || current_instr_info.opcode == V_ADD_VF) ? ADD :
                                 (current_instr_info.opcode == V_SUB_VV || current_instr_info.opcode == V_SUB_VF) ? SUB :
                                 (current_instr_info.opcode == V_MUL_VV || current_instr_info.opcode == V_MUL_VF) ? MUL :
                                 (current_instr_info.opcode == V_EXP_VV)    ? EXP : STALL;

                reduce_opcode  = (current_instr_info.opcode == V_RED_SUM)   ? SUM :
                                 (current_instr_info.opcode == V_RED_MAX)   ? MAX : STALL;
                
                fixed_opcode   = LOAD_FOR_ADDR;

                if (current_instr_info.opcode == V_ADD_VF || current_instr_info.opcode == V_SUB_VF || current_instr_info.opcode == V_MUL_VF) begin
                    fp_opcode       = LOAD_FP;
                    rs1             = current_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                    rs2             = {FIXED_OPERAND_WIDTH{1'0}};
                    rd              = current_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
                    fp_rs1          = {FP_OPERAND_WIDTH{1'0}};
                    fp_rs2          = current_instr_info.rs2[FP_OPERAND_WIDTH - 1 : 0];
                    fp_rd           = {FP_OPERAND_WIDTH{1'0}};
                    imm             = {IMM_WIDTH{1'0}};
                end else begin
                    fp_opcode       = STALL;
                    rs1             = current_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                    rs2             = current_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                    rd              = current_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
                    imm             = {IMM_WIDTH{1'0}};
                end
            end

            S: begin
                matrix_opcode = STALL;
                element_opcode = STALL;
                reduce_opcode  = STALL;
                fp_opcode      = (current_instr_info.opcode == S_ADD_FP )   ? ADD_FP    :
                                 (current_instr_info.opcode == S_SUB_FP )   ? SUB_FP    :
                                 (current_instr_info.opcode == S_MUL_FP )   ? MUL_FP    :
                                 (current_instr_info.opcode == S_EXP_FP )   ? EXP_FP    :
                                 (current_instr_info.opcode == S_ISQRT_FP)  ? ISQRT_FP  :
                                 (current_instr_info.opcode == S_LOG_FP  )  ? LOG_FP    : STALL;
                
                fixed_opcode   = (current_instr_info.opcode == S_ADD_FIX)   ? ADD_FIX   :
                                 (current_instr_info.opcode == S_ADDI_FIX)  ? ADDI_FIX  :
                                 (current_instr_info.opcode == S_SUB_FIX)   ? SUB_FIX   : 
                                 (current_instr_info.opcode == S_MUL_FIX)   ? MUL_FIX   : 
                                 (current_instr_info.opcode == S_DIV_FIX)   ? DIV_FIX   :
                                 (current_instr_info.opcode == S_LUI_FIX)   ? LUI_FIX   :
                                 (current_instr_info.opcode == S_MV_FIX)    ? MV_FIX    : STALL;
                
                if (current_instr_info.opcode == S_ADD_FP || current_instr_info.opcode == S_SUB_FP || current_instr_info.opcode == S_MUL_FP) begin
                    rs1             = {FIXED_OPERAND_WIDTH{1'0}};
                    rs2             = {FIXED_OPERAND_WIDTH{1'0}};
                    rd              = {FIXED_OPERAND_WIDTH{1'0}};
                    fp_rs1          = current_instr_info.rs1[FP_OPERAND_WIDTH - 1 : 0];
                    fp_rs2          = current_instr_info.rs2[FP_OPERAND_WIDTH - 1 : 0];
                    fp_rd           = current_instr_info.rd[FP_OPERAND_WIDTH - 1 : 0];
                    imm             = {IMM_WIDTH{1'0}};
                end else if (current_instr_info.opcode == S_EXP_FP || current_instr_info.opcode == S_ISQRT_FP || current_instr_info.opcode == S_LOG_FP) begin
                    rs1             = {FIXED_OPERAND_WIDTH{1'0}};
                    rs2             = {FIXED_OPERAND_WIDTH{1'0}};
                    rd              = {FIXED_OPERAND_WIDTH{1'0}};
                    fp_rs1          = current_instr_info.rs1[FP_OPERAND_WIDTH - 1 : 0];
                    fp_rs2          = {FP_OPERAND_WIDTH{1'0}};
                    fp_rd           = current_instr_info.rd[FP_OPERAND_WIDTH - 1 : 0];
                    imm             = {IMM_WIDTH{1'0}};
                end else if ( current_instr_info.opcode == S_ADDI_FIX) begin
                    rs1             = current_instr_info.rs1;
                    rs2             = {FIXED_OPERAND_WIDTH{1'0}};;
                    rd              = current_instr_info.rd;
                    fp_rs1 = {FP_OPERAND_WIDTH{1'0}};
                    fp_rs2 = {FP_OPERAND_WIDTH{1'0}};
                    fp_rd  = {FP_OPERAND_WIDTH{1'0}};
                    imm             = {{(IMM_WIDTH - FIXED_OPERAND_WIDTH){1'0}}, current_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0]};
                end else begin
                    rs1             = current_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                    rs2             = current_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                    rd              = current_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
                    fp_rs1 = {FP_OPERAND_WIDTH{1'0}};
                    fp_rs2 = {FP_OPERAND_WIDTH{1'0}};
                    fp_rd  = {FP_OPERAND_WIDTH{1'0}};
                    imm             = {IMM_WIDTH{1'0}};
                end
            end

            H : begin
                matrix_opcode = STALL;
                element_opcode = STALL;
                reduce_opcode  = STALL;
                fp_opcode      = STALL;
                fixed_opcode   = LOAD_FOR_ADDR;

                rs1             = current_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                rs2             = current_instr_info.rs2{FIXED_OPERAND_WIDTH{1'0}};
                rd              = current_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
                fp_rs1 = {FP_OPERAND_WIDTH{1'0}};
                fp_rs2 = {FP_OPERAND_WIDTH{1'0}};
                fp_rd  = {FP_OPERAND_WIDTH{1'0}};
                imm             = {IMM_WIDTH{1'0}};
            end

            C : begin
                matrix_opcode   = STALL;
                element_opcode  = STALL;
                reduce_opcode   = STALL;
                fp_opcode       = STALL;
                fixed_opcode    = CONCAT;
                rs1             = current_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                rs2             = current_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                rd              = {FIXED_OPERAND_WIDTH{1'0}};
                fp_rs1 = {FP_OPERAND_WIDTH{1'0}};
                fp_rs2 = {FP_OPERAND_WIDTH{1'0}};
                fp_rd  = {FP_OPERAND_WIDTH{1'0}};
                imm             = {IMM_WIDTH{1'0}};
            end

            default: begin
                matrix_opcode = STALL;
                element_opcode = STALL;
                reduce_opcode  = STALL;
                fp_opcode      = STALL;
                fixed_opcode   = STALL;
                rs1             = {FIXED_OPERAND_WIDTH{1'0}};
                rs2             = {FIXED_OPERAND_WIDTH{1'0}};
                rd              = {FIXED_OPERAND_WIDTH{1'0}};
                fp_rs1 = {FP_OPERAND_WIDTH{1'0}};
                fp_rs2 = {FP_OPERAND_WIDTH{1'0}};
                fp_rd  = {FP_OPERAND_WIDTH{1'0}};
                imm = '0;
            end
      
        endcase
    end else begin
        matrix_opcode = STALL;
        element_opcode = STALL;
        reduce_opcode  = STALL;
        fp_opcode      = STALL;
        rs1             = {FIXED_OPERAND_WIDTH{1'0}};
        rs2             = {FIXED_OPERAND_WIDTH{1'0}};
        rd              = {FIXED_OPERAND_WIDTH{1'0}};
        fp_rs1 = {FP_OPERAND_WIDTH{1'0}};
        fp_rs2 = {FP_OPERAND_WIDTH{1'0}};
        fp_rd  = {FP_OPERAND_WIDTH{1'0}};
        imm = '0;
    end
    
end



decoder #(
    .INSTRUCTION_LENGTH(INSTRUCTION_LENGTH),
    .OPERAND_WIDTH(OPERAND_WIDTH),
    .OPCODE_WIDTH(OPCODE_WIDTH),
    .INST_BUFF_DEPTH(INST_BUFF_DEPTH)
) decoder_inst (
    .clk(clk),
    .rst(rst),

    // Instruction
    .instruction(instruction),
    .instruction_valid(instruction_valid),
    .instruction_ready(instruction_ready),

    // Decoded Instruction
    .current_instr_info(current_instr_info),
    .next_instr_info(next_instr_info),

    // Decoder Control
    .read_next_instr(read_next_instr),
    .decode_instr_valid(decode_instr_valid)
);

endmodule