`timescale 1ns / 1ps

/*
Module      : MX-FP Rescale Unit
Timing      : Sequential, Takes x cycles to compute the dot product
Description : e1s1, e2s2, e3s3, e4s4 - > {e1, e2, e3, e4} s
            : Format a block of elements, rescale them to have the same scale.
Status      : Under Development
*/

module mx_fp_rescale #(
    // MX-FP Data Format
    parameter INPUT_EXP_WIDTH    = 4,
    parameter INPUT_MANT_WIDTH   = 3,
    parameter MXFP_SCALE_WIDTH  = 8,

    // Dimension
    parameter   BLOCK_DIM            = 4,

    // MX-FP Data Format
    parameter MXFP_EXP_WIDTH    = 4,
    parameter MXFP_MANT_WIDTH   = 3

) (
    input logic clk,
    input logic rst,

    // Input matrix
    input  logic [BLOCK_DIM - 1 : 0] [INPUT_MANT_WIDTH + INPUT_EXP_WIDTH : 0] element_in,
    input  logic [BLOCK_DIM - 1 : 0] [MXFP_SCALE_WIDTH - 1 : 0]             scale_in,

    output logic [BLOCK_DIM - 1 : 0] [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] element_data_out,
    output logic [MXFP_SCALE_WIDTH - 1 : 0] scale_data_out,
);

    logic [BLOCK_DIM - 1 : 0] [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] p0_rounded_element_out, p1_rounded_element_out;
    logic [BLOCK_DIM - 1 : 0] [MXFP_SCALE_WIDTH - 1 : 0] rounded_element_scale_out;
    

    generate;

        for (genvar i = 0; i < BLOCK_DIM; i++) begin : round_element
            mx_fp_element_round #(
                .IN_EXP_WIDTH   (INPUT_EXP_WIDTH),
                .IN_MANT_WIDTH  (INPUT_MANT_WIDTH),
                .SCALE_WIDTH    (MXFP_SCALE_WIDTH),
                .OUT_EXP_WIDTH  (MXFP_EXP_WIDTH),
                .OUT_MANT_WIDTH (MXFP_MANT_WIDTH)
            ) mxfp_round (
                .clk(clk),
                .rst(rst),
                .element_data_in    (element_in[i]),
                .scale_data_in      (scale_in[i]),
                .element_data_out   (p0_rounded_element_out[i]),
                .scale_data_out     (rounded_element_scale_out[i])
            );
        end

    endgenerate

    logic [MXFP_SCALE_WIDTH - 1 : 0] exp_max;
    unsigned_max #(
        .width(IN_MAN_WIDTH),
        .length(CONVERT_DIM),
        .flop_output(0)
    ) u0_exp_max (
        .clk(clk),
        .input_data(rounded_element_scale_out),
        .max_val(exp_max)
    );

    generate;
        for (genvar i = 0; i < BLOCK_DIM; i++) begin : gen_rescale
            logic [MXFP_EXP_WIDTH - 1 : 0] exp_reduce_amount, new_element_exp;
            assign exp_reduce_amount = exp_max - rounded_element_scale_out[i];
            assign new_element_exp = p1_rounded_element_out[i][MXFP_MANT_WIDTH + MXFP_EXP_WIDTH - 1 : MXFP_MANT_WIDTH] - exp_reduce_amount;
            // TODO: How to handle the case when the exponent is negative?
            assign element_data_out[i] = {p1_rounded_element_out[i][MXFP_MANT_WIDTH + MXFP_EXP_WIDTH], new_element_exp, p1_rounded_element_out[i][MXFP_MANT_WIDTH - 1 : 0]};
        end    
    endgenerate

endmodule
