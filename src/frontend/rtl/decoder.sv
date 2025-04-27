`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Decoder
Timing      : Conbinatorial
Description :
// Assuming the Instruction Format is as follows:
//  [RS2] [RS1] [RD] [OPCODE_WID]   
//  [IMM] [RS1] [RD] [OPCODE_WID]

*/

module decoder #(
    parameter INSTRUCTION_LENGTH = 16,
    parameter OPERAND_WIDTH = 5,
    parameter OPCODE_WIDTH = 4,
    parameter IMM_WIDTH = 32,
    parameter INST_BUFF_DEPTH = 8
)(
    input   logic clk,
    input   logic rst,

    // Instruction
    input   logic [INSTRUCTION_LENGTH - 1 : 0] instruction,
    input   logic instruction_valid,
    output  logic instruction_ready,
    output  logic instr_buffer_full,

    // Decoded Instruction
    output INSTR_INFO current_instr_info,
    output INSTR_INFO next_instr_info,

    // Decoder Control
    input   logic read_next_instr,
    output  logic decode_instr_valid
);

logic loaded_instr_valid;

fifo #(
    .DATA_WIDTH(INSTRUCTION_LENGTH), 
    .DEPTH(INST_BUFF_DEPTH),
) fifo_inst (
    .clk(clk),
    .rst(rst),
    .data_in(instruction),
    data_in_valid(instruction_valid),
    .data_in_ready(instruction_ready),
    .data_out(loaded_instr),
    .data_out_valid(loaded_instr_valid),
    .data_out_ready(read_next_instr),
    .empty(),
    .full(instr_buffer_full)
);


// Operand Assignments
logic [OPCODE_WIDTH - 1 : 0] loaded_opcode;
logic [OPERAND_WIDTH:0]      loaded_rs1;
logic [OPERAND_WIDTH:0]      loaded_rs2;
logic [OPERAND_WIDTH:0]      loaded_rd;

assign loaded_opcode    = (load_next == 1'b1) ? loaded_instr[INSTRUCTION_LENGTH - 1 : INSTRUCTION_LENGTH - OPCODE_WIDTH]  : 1'b0;
assign loaded_rs2       = (load_next == 1'b1) ? loaded_instr[INSTRUCTION_LENGTH - 1 : INSTRUCTION_LENGTH - OPERAND_WIDTH] : 1'b0;
assign loaded_rs1       = (load_next == 1'b1) ? loaded_instr[INSTRUCTION_LENGTH - OPERAND_WIDTH - 1 -: OPERAND_WIDTH]     : 1'b0;
assign loaded_rd        = (load_next == 1'b1) ? loaded_instr[INSTRUCTION_LENGTH - 2 * OPERAND_WIDTH - 1 -: OPERAND_WIDTH] : 1'b0;


always_comb begin
    case (loaded_opcode)
        // Matrix Operations
        M_MV, M_TMV: begin
            next_instruction_type = M;
        end

        // Vector Operations
        V_ADD_VV, V_ADD_VF, V_SUB_VV, V_SUB_VF, V_MUL_VV, V_MUL_VF, V_EXP_VV, V_RED_SUM, V_RED_MAX : begin
            next_instruction_type = V;
        end

        // Scalar Operations
        S_ADD_FP, S_SUB_FP, S_MUL_FP, S_EXP_FP, S_ISQRT_FP, S_LOG_FP, S_ADD_FIX, S_SUB_FIX: begin
            next_instruction_type = S;
        end

        // Memory Operations
        H_PREFETCH_MATRIX, H_PREFETCH_VECTOR, H_LOAD_MATRIX, H_LOAD_VECTOR, H_LOAD_SCALAR, H_STORE_VECTOR, H_STORE_SCALAR, H_STORE_HBM, H_SET_HBM_OFFSET: begin
            next_instruction_type = H;
        end

        default: begin
            next_instruction_type = INVALID;
        end

    endcase
end

assign next_instr_info = '{opcode: loaded_opcode, rs1: loaded_rs1, rs2: loaded_rs2, rd: loaded_rd, imm: loaded_imm, instruction_type: next_instruction_type};

always_ff @(posedge clk) begin
    decode_instr_valid <= loaded_instr_valid;
    if (read_next_instr) begin
        current_instr_info <= next_instr_info;
    end
end
    
endmodule