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
    parameter IN_MXFP_EXP_WIDTH    = 4,
    parameter IN_MXFP_MANT_WIDTH   = 3,
    parameter MXFP_SCALE_WIDTH  = 8,

    // Dimension
    parameter   BLOCK_DIM            = 4,

    // MX-FP Data Format
    parameter OUT_MXFP_EXP_WIDTH    = 4,
    parameter OUT_MXFP_MANT_WIDTH   = 3

) (
    input logic clk,
    input logic rst,

    // Input matrix
    input  logic [BLOCK_DIM - 1 : 0] [IN_MXFP_MANT_WIDTH + IN_MXFP_EXP_WIDTH : 0] element_in,
    input  logic [BLOCK_DIM - 1 : 0] [MXFP_SCALE_WIDTH - 1 : 0]             scale_in,

    output logic [BLOCK_DIM - 1 : 0] [OUT_MXFP_MANT_WIDTH + OUT_MXFP_EXP_WIDTH : 0] element_data_out,
    output logic [MXFP_SCALE_WIDTH - 1 : 0] scale_data_out
);

    logic [BLOCK_DIM - 1 : 0] [OUT_MXFP_MANT_WIDTH + OUT_MXFP_EXP_WIDTH : 0] p0_rounded_element_out, p1_rounded_element_out;
    logic [BLOCK_DIM - 1 : 0] [MXFP_SCALE_WIDTH - 1 : 0] rounded_scale;
    

    generate;
        if (IN_MXFP_EXP_WIDTH != OUT_MXFP_EXP_WIDTH || IN_MXFP_MANT_WIDTH != OUT_MXFP_MANT_WIDTH) begin : round_element
            mx_fp_element_round #(
                .IN_EXP_WIDTH   (IN_MXFP_EXP_WIDTH),
                .IN_MANT_WIDTH  (IN_MXFP_MANT_WIDTH),
                .SCALE_WIDTH    (MXFP_SCALE_WIDTH),
                .OUT_EXP_WIDTH  (OUT_MXFP_EXP_WIDTH),
                .OUT_MANT_WIDTH (OUT_MXFP_MANT_WIDTH)
            ) mxfp_round (
                .data_in    (element_in),
                .scale_in      (scale_in),
                .data_out   (p0_rounded_element_out),
                .scale_out     (rounded_scale)
            );
        end else begin : no_round
            assign p0_rounded_element_out = element_in;
            assign rounded_scale = scale_in;
        end

    endgenerate

    logic [MXFP_SCALE_WIDTH - 1 : 0] exp_max;

    unsigned_max #(
        .width(MXFP_SCALE_WIDTH),
        .length(BLOCK_DIM),
        .flop_output(0)
    ) u0_exp_max (
        .clk(clk),
        .input_data(rounded_scale),
        .max_val(exp_max)
    );

    always_ff @(posedge clk or negedge rst) begin
        if (!rst) begin
            p1_rounded_element_out <= '0;
        end else begin
            p1_rounded_element_out <= p0_rounded_element_out;
        end
    end

    generate;
        for (genvar i = 0; i < BLOCK_DIM; i++) begin : gen_rescale
            logic [OUT_MXFP_EXP_WIDTH - 1 : 0] exp_reduce_amount, new_element_exp;
            assign exp_reduce_amount = exp_max - rounded_scale[i];
            assign new_element_exp = p1_rounded_element_out[i][OUT_MXFP_MANT_WIDTH + OUT_MXFP_EXP_WIDTH - 1 : OUT_MXFP_MANT_WIDTH] - exp_reduce_amount;
            // TODO: How to handle the case when the exponent is negative?
            assign element_data_out[i] = {p1_rounded_element_out[i][OUT_MXFP_MANT_WIDTH + OUT_MXFP_EXP_WIDTH], new_element_exp, p1_rounded_element_out[i][OUT_MXFP_MANT_WIDTH - 1 : 0]};
        end    
    endgenerate

endmodule
