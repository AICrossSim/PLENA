`timescale 1ns / 1ps

/*
Module      : Vector Reduction Computation Module
Timing      : Sequential, Takes x cycles to compute the dot product
Description : This module includes vector reduction computations
            : 1. SUM, 2. MAX
Status      : Under Development
*/


module reduction_compute_unit #(
    // FP Data Format
    parameter EXP_WIDTH    = 4,
    parameter MANT_WIDTH   = 3,

    // Dimensions
    parameter VLEN      = 8,

    // Precision Control
    parameter ACC_EXT_EXP_WIDTH   = 1,
    parameter ACC_EXT_MANT_WIDTH  = 4,

    // Operation Control
    parameter OPERAND_WIDTH = 4

) (
    input logic clk,
    input logic rst,

    // Input vector
    input logic [VLEN - 1:0] [MANT_WIDTH + EXP_WIDTH : 0] v_in_a,
    input logic v_in_a_valid,
    output logic v_in_a_ready,
    input logic [VLEN - 1:0] [MANT_WIDTH + EXP_WIDTH : 0] v_in_b,
    input logic v_in_b_valid,
    output logic v_in_b_ready,

    // Control
    input logic [OPERAND_WIDTH - 1:0] operation,

    // Output Vector
    output logic [VLEN - 1:0] [MANT_WIDTH + EXP_WIDTH : 0] v_out,
    output logic v_out_valid,
    input logic v_out_ready
);


endmodule