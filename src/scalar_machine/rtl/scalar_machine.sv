`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Scalar Machine Module
Timing      : Sequential, all the operations completed in 1 cycle
Description : This module contains two modules:
            : FP ALU for all the fp computation related operations
            : Fixed ALU, only have addition and subtraction operations for address manipulation
Status      : Under Testing
*/

module scalar_machine #(
    // MX-FP Data Format
    parameter   MXFP_MANT_WIDTH   = 8,
    parameter   MXFP_EXP_WIDTH    = 4,
    parameter   MXFP_SCALE_WIDTH = 8,

    // FP Data Format
    parameter   FP_EXP_WIDTH = 5,
    parameter   FP_MANT_WIDTH = 10,

    // Fixed Data Format
    parameter   FIXED_DATA_WIDTH = 32

    // Dimensions
) (
    input   logic clk,
    input   logic rst,

    // Control
    input   S_FP_OP fp_control,
    input   S_FIXED_OP fixed_control,

    // Fixed Register Control
    input   logic [OPERAND_WIDTH - 1 : 0] rs1,
    input   logic [OPERAND_WIDTH - 1 : 0] rs2,
    input   logic [OPERAND_WIDTH - 1 : 0] rd,

    // FP Register Control
    input   logic [FP_EXP_WIDTH + FP_MANT_WIDTH - 1 : 0] fp_rs1,
    input   logic [FP_EXP_WIDTH + FP_MANT_WIDTH - 1 : 0] fp_rs2,
    input   logic [FP_EXP_WIDTH + FP_MANT_WIDTH - 1 : 0] fp_rd,

    // Fixed Value input
    input   logic [FIXED_DATA_WIDTH - 1 : 0] fixed_in,
    input   logic [FIXED_DATA_WIDTH - 1 : 0] imm_in,
    // input   logic fixed_in_valid,
    // output  logic fixed_in_ready,
    output  logic [FIXED_DATA_WIDTH - 1 : 0] fixed_out_1,
    output  logic [FIXED_DATA_WIDTH - 1 : 0] fixed_out_2,
    // output  logic fixed_out_valid,
    // input   logic fixed_out_ready,

    // FP Value input
    input   logic [FP_EXP_WIDTH + FP_MANT_WIDTH - 1 : 0] fp_in,

    // input   logic fp_in_valid,
    // output  logic fp_in_ready,

    output   logic [FP_EXP_WIDTH + FP_MANT_WIDTH - 1 : 0] fp_out_1,
    output   logic [FP_EXP_WIDTH + FP_MANT_WIDTH - 1 : 0] fp_out_2
    // output  logic fp_out_valid,
    // input   logic fp_out_ready
);



logic fp_we;

assign fp_we = (fp_control != STALL_S_FP && fp_control !=LOAD_FP ) ? 1'b1 : 1'b0;

fp_alu #(
    .EXP_WIDTH(FP_EXP_WIDTH),
    .MANT_WIDTH(FP_MANT_WIDTH)
) fp_alu (
    .data_a(fp_rs1),
    .data_b(fp_rs2),
    .operation(fp_control),
    .data_out(fp_rd)
);


regfile_2p1w #(
    .BITWIDTH(FP_EXP_WIDTH + FP_MANT_WIDTH + 1),
    .DEPTH(2 << FP_OPERAND_WIDTH)
) fp_reg_file (
    .clk(clk),
    .we(fp_we),
    .waddr(rd[FP_OPERAND_WIDTH - 1 : 0]),
    .wdata(fp_rd),
    .raddr1(rs1[FP_OPERAND_WIDTH - 1 : 0]),
    .raddr2(rs2[FP_OPERAND_WIDTH - 1 : 0]),
    .rdata1(fp_rs1),
    .rdata2(fp_rs2)
);

always_ff @(posedge clk or posedge rst) begin
    if (rst) begin
        fp_out_1 <= 'b0;
        fp_out_2 <= 'b0;
    end else begin
        fp_out_1 <= (fp_control == LOAD_FP) ? fp_rs1 : fp_rd;
        fp_out_2 <= (fp_control == LOAD_FP) ? fp_rs2 : {FP_EXP_WIDTH + FP_MANT_WIDTH{1'b0}};
    end
end


logic [FIXED_DATA_WIDTH - 1 : 0] fixed_rs1;
logic [FIXED_DATA_WIDTH - 1 : 0] fixed_rs2;
logic [FIXED_DATA_WIDTH - 1 : 0] fixed_rd;
logic fix_we;

assign fix_we = (fixed_control != STALL_S_FIXED && fixed_control != LOAD_FOR_ADDR) ? 1'b1 : 1'b0;
assign fixed_out_1 = fixed_rs1;
assign fixed_out_2 = fixed_rd;

fixed_alu #(
    .BITWIDTH(FIXED_DATA_WIDTH)
) fixed_alu (
    .operand_a(fixed_rs1),
    .operand_b(fixed_rs2),
    .imm_value(imm_in),
    .operation(fixed_control),
    .result(fixed_rd)
);


regfile_2p1w #(
    .BITWIDTH(FIXED_DATA_WIDTH),
    .DEPTH(2 << FIXED_OPERAND_WIDTH)
) fixed_reg_file (
    .clk(clk),
    .we(fix_we),
    .waddr(rd[FIXED_OPERAND_WIDTH - 1 : 0]),
    .wdata(fixed_rd),
    .raddr1(rs1[FIXED_OPERAND_WIDTH - 1 : 0]),
    .raddr2(rs2[FIXED_OPERAND_WIDTH - 1 : 0]),
    .rdata1(fixed_rs1),
    .rdata2(fixed_rs2)
);

endmodule