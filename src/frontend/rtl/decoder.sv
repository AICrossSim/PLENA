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
    output INSTR_INFO decode_instr_info,

    // Decoder Control
    input   logic read_next_instr,
    output  logic decode_instr_valid
);

logic [INSTRUCTION_LENGTH - 1 : 0] loaded_instr;
logic read_instr_from_fifo;

assign read_instr_from_fifo = read_next_instr;

fifo #(
    .DATA_WIDTH(INSTRUCTION_LENGTH), 
    .DEPTH(INST_BUFF_DEPTH)
) fifo_inst (
    .clk(clk),
    .rst(rst),
    .data_in(instruction),
    .data_in_valid(instruction_valid),
    .data_in_ready(instruction_ready),
    .data_out(loaded_instr),
    .data_out_valid(decode_instr_valid),
    .data_out_ready(read_instr_from_fifo),
    .empty(),
    .full(instr_buffer_full)
);


// Operand Assignments
logic [OPCODE_WIDTH - 1 : 0]    loaded_opcode;
logic [OPERAND_WIDTH:0]         loaded_rs1;
logic [OPERAND_WIDTH:0]         loaded_rs2;
logic [OPERAND_WIDTH:0]         loaded_rd;
logic [IMM_WIDTH - 1 : 0]       loaded_imm;



assign loaded_imm       = (loaded_opcode == S_ADDI_FIX) ? {{(IMM_WIDTH - IMM_2_WIDTH){1'b0}} , loaded_instr[INSTRUCTION_LENGTH - 1 -: IMM_2_WIDTH]} : loaded_instr[INSTRUCTION_LENGTH - 1 -: IMM_WIDTH];
assign loaded_rs2       = loaded_instr[INSTRUCTION_LENGTH - 2 -: OPERAND_WIDTH];
assign loaded_rs1       = loaded_instr[(INSTRUCTION_LENGTH - OPERAND_WIDTH - 2) -: OPERAND_WIDTH];
assign loaded_rd        = loaded_instr[(INSTRUCTION_LENGTH - 2 * OPERAND_WIDTH - 2) -: OPERAND_WIDTH];
assign loaded_opcode    = loaded_instr[OPCODE_WIDTH - 1 : 0];

CUSTOM_ISA_TYPE decode_instruction_type;

always_comb begin
    case (loaded_opcode)
        // Matrix Operations
        M_MV, M_MV_O, M_TMV, M_TMV_O: begin
            decode_instruction_type = M;
        end

        // Vector Operations
        V_ADD_VV, V_ADD_VF, V_SUB_VV, V_SUB_VF, V_MUL_VV, V_MUL_VF, V_EXP_VV, V_RED_SUM, V_RED_MAX : begin
            decode_instruction_type = V;
        end

        // Scalar Operations
        S_ADD_FP, S_SUB_FP, S_MAX_FP, S_MUL_FP, S_EXP_FP, S_RECI_FP, S_SQRT_FP, S_LD_REG_FP, S_ST_REG_FP, S_ADD_FIX, S_ADDI_FIX, S_SUB_FIX, S_MUL_FIX, S_DIV_FIX, S_LUI_FIX, S_MV_FIX, S_LD_FIX, S_ST_FIX : begin
            decode_instruction_type = S;
        end

        // Memory Operations
        H_PREFETCH_M, H_PREFETCH_V, H_STORE_V: begin
            decode_instruction_type = H;
        end

        // CSR Setting
        C_SET_ADDR_REG, C_SET_M_OFFSET, C_SET_LUT: begin
            decode_instruction_type = C;
        end

        default: begin
            decode_instruction_type = INVALID_TYPE;
        end

    endcase
end

assign decode_instr_info = decode_instr_valid ? '{opcode: loaded_opcode, rs1: loaded_rs1, rs2: loaded_rs2, rd: loaded_rd, imm: loaded_imm, instruction_type: decode_instruction_type} : '{opcode: '0, rs1: '0, rs2: '0, rd: '0, imm: '0, instruction_type: INVALID_TYPE};


endmodule