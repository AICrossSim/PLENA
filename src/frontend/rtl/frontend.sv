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
    parameter INSTRUCTION_LENGTH = 16,
    parameter OPERAND_WIDTH = 5,
    parameter OPCODE_WIDTH = 4,
    parameter INST_BUFF_DEPTH = 8,
    parameter LOOKAHEAD_EN = 1
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
    input   logic last_matrix_complete,

    // Control Vector Computation
    output  V_ELEMENT_OP      element_opcode,
    output  V_REDUCT_OP       reduce_opcode,
    input   logic last_vector_complete,

    // Control Scalar Computation
    output S_FP_OP           fp_opcode,
    output S_FIXED_OP        fixed_opcode,
    output logic [31:0]      imm,
    output logic [OPERAND_WIDTH:0]      rs1,
    output logic [OPERAND_WIDTH:0]      rs2,
    output logic [OPERAND_WIDTH:0]      rd
);


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