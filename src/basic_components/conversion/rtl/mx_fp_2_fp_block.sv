`timescale 1ns / 1ps

/*
Module      : Convertion a block unit of mx-fp data to fp data
Timing      : Combinatorial Logic
Status      : Passed Simple Tests, 
TODO:       : Need to consider the case MXFP_SCALE < FP_EXP_WIDTH
*/


module mx_fp_2_fp_block #(
    parameter BLOCK_DIM = 8, 
    parameter MXFP_MANT_WIDTH = 3,
    parameter MXFP_EXP_WIDTH = 4,
    parameter MXFP_SCALE_WIDTH = 8,
    parameter FP_MANT_WIDTH = 3,
    parameter FP_EXP_WIDTH = 4
)(
    input   logic clk,
    input   logic rst,
    input   logic data_in_valid,
    output  logic data_in_ready,
    input   logic [BLOCK_DIM-1:0][MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] element_in,
    input   logic [MXFP_SCALE_WIDTH-1:0] scale_in,
    output  logic data_out_valid,
    input   logic data_out_ready,
    output  logic [BLOCK_DIM-1:0][FP_MANT_WIDTH + FP_EXP_WIDTH : 0] fp_out
);
    initial begin
        // To ensure the output mantissa is large enough to hold the input mantissa.
        assert (MXFP_SCALE_WIDTH >= FP_EXP_WIDTH)
            else $error("MXFP_SCALE_WIDTH must be greater than or equal to FP_EXP_WIDTH");
    end
    logic [BLOCK_DIM-1:0] split_data_in_valid, split_data_in_ready;
    logic [BLOCK_DIM-1:0] converted_data_out_valid, converted_data_out_ready;

    split_n #(
        .N(BLOCK_DIM)
    ) split_input_signal_in (
        .data_in_valid  (data_in_valid),
        .data_in_ready  (data_in_ready),
        .data_out_valid (split_data_in_valid),
        .data_out_ready (split_data_in_ready)
    );

    for (genvar i = 0; i < BLOCK_DIM; i++) begin
        mx_fp_2_fp_unary #(
            .MXFP_EXP_WIDTH     (MXFP_EXP_WIDTH),
            .MXFP_MANT_WIDTH    (MXFP_MANT_WIDTH),
            .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH),
            .FP_MANT_WIDTH      (FP_MANT_WIDTH),
            .FP_EXP_WIDTH       (FP_EXP_WIDTH)
        ) mx_fp_2_fp_unary_inst (
            .clk(clk),
            .rst(rst),
            .data_in_valid      (split_data_in_valid[i]),
            .data_in_ready      (split_data_in_ready[i]),
            .element_data_in    (element_in[i]),
            .scale_data_in      (scale_in),
            .data_out_valid     (converted_data_out_valid[i]),
            .data_out_ready     (converted_data_out_ready[i]),
            .fp_out             (fp_out[i])
        );
    end

    join_n #(
        .NUM_HANDSHAKES(BLOCK_DIM)
    ) join_output_signal_out (
        .data_in_valid(converted_data_out_valid),
        .data_in_ready(converted_data_out_ready),
        .data_out_valid(data_out_valid),
        .data_out_ready(data_out_ready)
    );


endmodule
