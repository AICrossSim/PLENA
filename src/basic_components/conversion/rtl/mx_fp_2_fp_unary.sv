`timescale 1ns / 1ps

/*
Module      : Unary Convertion from MX-FP to FP
Timing      : Combinatorial Logic
Description : 
Status      : Passed Simple Tests
*/

module mx_fp_2_fp_unary #(
    parameter MXFP_EXP_WIDTH = 4,
    parameter MXFP_MANT_WIDTH = 3,
    parameter MXFP_SCALE_WIDTH = 8,
    parameter FP_EXP_WIDTH = 4,
    parameter FP_MANT_WIDTH = 3
)(
    input   logic [MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] element_data_in,
    input   logic [MXFP_SCALE_WIDTH - 1 : 0] scale_data_in,
    output  logic [FP_EXP_WIDTH + FP_MANT_WIDTH : 0] fp_out
);
    initial begin
        assert (MXFP_SCALE_WIDTH >= FP_EXP_WIDTH)
        else $error("MXFP_SCALE_WIDTH must be greater than or equal to FP_EXP_WIDTH");

        assert (MXFP_MANT_WIDTH <= FP_MANT_WIDTH)
        else $error("MXFP_MANT_WIDTH must be less than or equal to FP_MANT_WIDTH");
    end

    localparam MXFP_FIX_WIDTH = MXFP_MANT_WIDTH + 2;
    localparam MXFP_FIX_FRAC_WIDTH = MXFP_MANT_WIDTH;
    localparam SCALE_BIAS = 2**(MXFP_SCALE_WIDTH - 1) - 1;
    localparam SCALE_WIDTH = MXFP_SCALE_WIDTH + 1;
    localparam NORMALIZE_OUT_EXP_WIDTH = SCALE_WIDTH + 1;
    localparam NORMALIZE_OUT_MANT_WIDTH = FP_MANT_WIDTH;

    logic [MXFP_EXP_WIDTH-1:0] signed_exp_element;
    logic [MXFP_FIX_WIDTH-1:0] signed_mant_element;

    logic [MXFP_SCALE_WIDTH-1:0] signed_scale_element;
    logic [SCALE_WIDTH-1:0] signed_out_exp_element;
    logic [NORMALIZE_OUT_EXP_WIDTH + FP_MANT_WIDTH:0] normalized_data;

    fp_ieee_partition #(
        .EXP_WIDTH(MXFP_EXP_WIDTH),
        .MANT_WIDTH(MXFP_MANT_WIDTH)
    ) partition_a (
        .data_in(element_data_in),
        .signed_exp(signed_exp_element),
        .signed_mant(signed_mant_element)
    );

    assign signed_out_exp_element = $signed(signed_exp_element) + $signed({1'b0, scale_data_in}) - SCALE_BIAS;

    fp_ieee_normalize #(
        .IN_FIXED_WIDTH         (MXFP_FIX_WIDTH),
        .IN_FIXED_FRAC_WIDTH    (MXFP_FIX_FRAC_WIDTH),
        .IN_EXP_WIDTH           (SCALE_WIDTH),
        .OUT_MANT_WIDTH         (FP_MANT_WIDTH)
    ) fp_normalize (
        .signed_mant    (signed_mant_element),
        .signed_exp     (signed_out_exp_element),
        .fp_out         (normalized_data)
    );



    fp_ieee_exponent_casting #(
        .IN_EXP_WIDTH       (NORMALIZE_OUT_EXP_WIDTH),
        .OUT_EXP_WIDTH      (FP_EXP_WIDTH),
        .MANT_WIDTH         (FP_MANT_WIDTH)
    ) fp_casting (
        .data_in    (normalized_data),
        .data_out   (fp_out)
    );

endmodule