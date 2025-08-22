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
    parameter EXP_WIDTH    = 4,
    parameter MANT_WIDTH   = 3,

    // Dimensions
    parameter VLEN      = 8

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

// Prefix scan path signals
logic [VLEN - 1:0] [MANT_WIDTH + EXP_WIDTH : 0] prefix_scan_out;
logic prefix_scan_valid, prefix_scan_ready;

// Select signals
logic use_prefix_scan;
logic element_in_valid;


// Determine which path to use
assign use_prefix_scan = (operation == PREFIX_SCAN_V_ELEMENT);

// Input handshaking for ALU path (only when not using prefix scan)
join2 #() join_input_handshake (
    .data_in_valid({v_in_a_valid, use_prefix_scan ? 1'b1 : v_in_b_valid}),
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
            .data_in_valid       (element_in_valid & ~use_prefix_scan),
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
    .data_out_ready(use_prefix_scan ? prefix_scan_ready : v_compute_ready)
);

// Prefix scan path - vector processing
fp_prefix_scan_syn #(
    .N(VLEN),
    .EXP_WIDTH(EXP_WIDTH),
    .MANT_WIDTH(MANT_WIDTH),
    .ADDER_CYCLES(1)
) prefix_scan_unit (
    .clk(clk),
    //.rst(!rst),
    .rst(rst),
    .vin(v_in_a),
    .vout(prefix_scan_out),
    .in_ready(v_in_a_valid & use_prefix_scan),  // ADD THIS
    .out_ready(prefix_scan_valid)
);

// Remove or fix the input ready logic:
always_comb begin
    if (use_prefix_scan) begin
        prefix_scan_ready = v_out_ready;  // Connect prefix scan ready to output ready
        // Don't override v_in_a_ready, v_in_b_ready here - let join2 handle them
    end else begin
        prefix_scan_ready = 1'b0;  // Not used when not doing prefix scan
    end
end

// Output selection based on operation
logic [VLEN - 1:0] [MANT_WIDTH + EXP_WIDTH : 0] selected_output;
logic selected_valid;

always_comb begin
    if (use_prefix_scan) begin
        selected_output = prefix_scan_out;
        selected_valid  = prefix_scan_valid;
    end else begin
        selected_output = v_alu_out;
        selected_valid  = v_compute_valid;
    end
end

// Output buffer
register_slice #(
    .DATA_WIDTH(VLEN * (MANT_WIDTH + EXP_WIDTH + 1))
) result_buf_inst (
    .clk(clk),
    //.rst(!rst),
    .rst(rst),
    .data_in        (selected_output),
    .data_in_valid  (selected_valid),
    .data_in_ready  (use_prefix_scan ? prefix_scan_ready : v_compute_ready),
    .data_out       (v_out),
    .data_out_valid (v_out_valid),
    .data_out_ready (v_out_ready)
);

endmodule