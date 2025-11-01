`timescale 1ns / 1ps

`include "configuration.svh"
`include "operation.svh"

/*
Module      : Elementwise Computation Module
Timing      : Sequential, Takes 1 cycles to compute the dot product
Description : This module includes elementwise vector computations
            : 1. Elementwise Add, 2. Elementwise Subtract, 3. Elementwise Multiply, 4. Elementwise Exponential, 8. prefix scan
Status      : Pass Simple Test, EXP not implemented yet.
*/

module fp_elementwise_compute_unit #(
    // FP Data Format
    parameter EXP_WIDTH     = 4,
    parameter MANT_WIDTH    = 3,
    parameter VLEN          = 8

) (
    input logic clk,
    input logic rst,

    // Input vector
    input   logic [VLEN - 1:0] [MANT_WIDTH + EXP_WIDTH : 0] v_in_a,
    input   logic v_in_a_valid,
    output  logic v_in_a_ready,
    input   logic [VLEN - 1:0] [MANT_WIDTH + EXP_WIDTH : 0] v_in_b,
    input   logic v_in_b_valid,
    output  logic v_in_b_ready,

    // Control
    input V_ELEMENT_OP operation, // 0: add, 1: sub, 2: mul, ... 8: prefix_scan

    // Output Vector
    output logic [VLEN - 1:0] [MANT_WIDTH + EXP_WIDTH : 0] v_out,
    output logic v_out_valid,
    input logic v_out_ready
);

// ALU path signals
logic v_compute_ready, v_compute_valid;
logic [VLEN - 1:0] [MANT_WIDTH + EXP_WIDTH : 0] v_alu_out;
logic [VLEN - 1:0] split_result_ready, split_result_valid;


// Select signals
logic element_in_valid;

// Input handshaking for ALU path (only when not using prefix scan)
join2 #() join_input_handshake (
    .data_in_valid({v_in_a_valid, v_in_b_valid}),
    .data_in_ready({v_in_a_ready, v_in_b_ready}),
    .data_out_valid(element_in_valid),
    .data_out_ready(1'b1)
);

// ALU path - parallel element processing
generate;
    for (genvar i = 0; i < VLEN; i = i + 1) begin : parallel_vec_alu
        fp_vector_element_alu #(
            .EXP_WIDTH(EXP_WIDTH),
            .MANT_WIDTH(MANT_WIDTH)
        ) vec_alu_inst (
            .clk(clk),
            .rst(rst),
            .data_in_valid       (element_in_valid),
            .data_a             (v_in_a[i]),
            .data_b             (v_in_b[i]),
            .operation          (operation),
            .data_out           (v_alu_out[i]),
            .data_out_valid     (split_result_valid[i]),
            .data_out_ready     (split_result_ready[i])
        );
    end
endgenerate

join_n #(
    .NUM_HANDSHAKES (VLEN)
) join_data_out (
    .data_in_valid(split_result_valid),
    .data_in_ready(split_result_ready),
    .data_out_valid(v_compute_valid),
    .data_out_ready(v_compute_ready)
);


// Output buffer
register_slice #(
    .DATA_WIDTH(VLEN * (MANT_WIDTH + EXP_WIDTH + 1))
) result_buf_inst (
    .clk(clk),
    .rst(rst),
    .data_in        (v_alu_out),
    .data_in_valid  (v_compute_valid),
    .data_in_ready  (v_compute_ready),
    .data_out       (v_out),
    .data_out_valid (v_out_valid),
    .data_out_ready (v_out_ready)
);

endmodule