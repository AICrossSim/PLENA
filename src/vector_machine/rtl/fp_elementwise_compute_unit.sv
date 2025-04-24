`timescale 1ns / 1ps
`include "operation.svh"
/*
Module      : Elementwise Computation Module
Timing      : Sequential, Takes 1 cycles to compute the dot product
Description : This module includes elementwise vector computations
            : 1. Elementwise Add, 2. Elementwise Subtract, 3. Elementwise Multiply, 4. Elementwise Exponential
Status      : Pass Simple Test, EXP not implemented yet.
*/


module fp_elementwise_compute_unit #(
    // FP Data Format
    parameter EXP_WIDTH    = 4,
    parameter MANT_WIDTH   = 3,

    // Dimensions
    parameter VLEN      = 8

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
    input V_ELEMENT_OP operation, // 0: add, 1: sub, 2: mul

    // Output Vector
    output logic [VLEN - 1:0] [MANT_WIDTH + EXP_WIDTH : 0] v_out,
    output logic v_out_valid,
    input logic v_out_ready
);

logic v_in_ready, v_in_valid;
logic [VLEN - 1:0] [MANT_WIDTH + EXP_WIDTH : 0] v_alu_out;

generate;
    for (genvar i = 0; i < VLEN; i = i + 1) begin : parallel_vec_alu
        
        vector_element_alu #(
            .EXP_WIDTH(EXP_WIDTH),
            .MANT_WIDTH(MANT_WIDTH)
        ) vec_alu_inst (
            .data_a(v_in_a[i]),
            .data_b(v_in_b[i]),
            .operation(operation),
            .data_out(v_alu_out[i])
        );

    end
endgenerate


join2 #() join_inst (
    .data_in_ready ({v_in_a_ready, v_in_b_ready}),
    .data_in_valid ({v_in_a_valid, v_in_b_valid}),
    .data_out_valid(v_in_valid),
    .data_out_ready(v_in_ready)
);


skid_buffer #(
    .DATA_WIDTH(VLEN * (MANT_WIDTH + EXP_WIDTH + 1))
) skid_buf_inst (
    .clk(clk),
    .rst(!rst),
    .data_in(v_alu_out),
    .data_in_valid(v_in_valid),
    .data_in_ready(v_in_ready),
    .data_out(v_out),
    .data_out_valid(v_out_valid),
    .data_out_ready(v_out_ready)
);


endmodule