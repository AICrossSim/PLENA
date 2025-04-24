`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Vector Machine Module
Timing      : Sequential, Takes x cycles to compute the dot product
Description : This module is the first version of the vector machine based on FP data type.
Status      : Under Testing
*/

module scalar_machine #(
    // MX-FP Data Format
    parameter   MXFP_MANT_WIDTH   = 8,
    parameter   MXFP_EXP_WIDTH    = 4,
    parameter   MX_FP_SCALE_WIDTH = 8,

    // FP Data Format
    parameter   FP_EXP_WIDTH = 5,
    parameter   FP_MANT_WIDTH = 10

    // Dimensions
) (
    input   logic clk,
    input   logic rst,

    // Control
    input   logic select_b_from_scalar,
    input   S_ALU_OP element_s_control,

    // Scalar Value
    input   logic [FP_EXP_WIDTH + FP_MANT_WIDTH] s_in,
    input   logic s_in_valid,
    output  logic s_in_ready,

    output  logic [FP_EXP_WIDTH + FP_MANT_WIDTH] s_out,
    output  logic s_out_valid,
    input   logic s_out_ready
)



fp_alu #(
    .EXP_WIDTH(FP_EXP_WIDTH),
    .MANT_WIDTH(FP_MANT_WIDTH)
) fp_alu (
    .data_a(s_in),
    .data_b(s_in),
    .operation(element_s_control),
    .data_out(s_out)
);



skid_buffer #(
    .Width(FP_EXP_WIDTH + FP_MANT_WIDTH + 1)
) s_in_buffer (
    .clk(clk),
    .rst(rst),
    .in(s_in),
    .valid(s_in_valid),
    .ready(s_in_ready),
    .out(s_out),
    .out_valid(s_out_valid),
    .out_ready(s_out_ready)
);




endmodule