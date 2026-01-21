`timescale 1ns / 1ps

/*
Module      : Unary Convertion from MX-FP to FP
Timing      : Combinatorial Logic
Description :
Status      : Passed Simple Tests
*/

module mx_int_2_fp_unary #(
    parameter MXINT_SCALE_WIDTH = 16,
    parameter MXINT_WIDTH = 16,
    parameter MXINT_FRAC_WIDTH = 16,
    parameter FP_EXP_WIDTH = 4,
    parameter FP_MANT_WIDTH = 3
)(
    input   logic clk,
    input   logic rst,
    input   logic data_in_valid,
    output  logic data_in_ready,
    input   logic [MXINT_WIDTH - 1 : 0] element_data_in,
    input   logic [MXINT_SCALE_WIDTH - 1 : 0] scale_data_in,
    output  logic data_out_valid,
    input   logic data_out_ready,
    output  logic [FP_EXP_WIDTH + FP_MANT_WIDTH : 0] fp_out
);
    // initial begin
    //     assert (FP_SCALE_WIDTH >= FP_EXP_WIDTH)
    //     else $error("FP_SCALE_WIDTH must be greater than or equal to FP_EXP_WIDTH");

    //     assert (MX_INT_WIDTH <= FP_MANT_WIDTH)
    //     else $error("MX_INT_WIDTH must be less than or equal to FP_MANT_WIDTH");
    // end
    localparam NORMALIZE_OUT_EXP_WIDTH = MXINT_SCALE_WIDTH + 1;
    logic [NORMALIZE_OUT_EXP_WIDTH + FP_MANT_WIDTH:0] normalized_data;
    logic [FP_EXP_WIDTH + FP_MANT_WIDTH : 0] reg_fp_out;

    fp_ieee_normalize #(
        .IN_FIXED_WIDTH         (MXINT_WIDTH),
        .IN_FIXED_FRAC_WIDTH    (MXINT_FRAC_WIDTH),
        .IN_EXP_WIDTH           (MXINT_SCALE_WIDTH),
        .OUT_MANT_WIDTH         (FP_MANT_WIDTH)
    ) fp_normalize (
        .signed_mant    (element_data_in),
        .signed_exp     (scale_data_in),
        .fp_out         (normalized_data)
    );

    fp_ieee_exponent_casting #(
        .IN_EXP_WIDTH       (NORMALIZE_OUT_EXP_WIDTH),
        .OUT_EXP_WIDTH      (FP_EXP_WIDTH),
        .MANT_WIDTH         (FP_MANT_WIDTH)
    ) fp_casting (
        .data_in    (normalized_data),
        .data_out   (reg_fp_out)
    );

    register_slice #(
        .DATA_WIDTH(FP_EXP_WIDTH + FP_MANT_WIDTH  + 1)
    ) casted_reg_inst (
        .clk(clk),
        .rst(rst),
        .data_in        (reg_fp_out),
        .data_in_valid  (data_in_valid),
        .data_in_ready  (data_in_ready),
        .data_out       (fp_out),
        .data_out_valid (data_out_valid),
        .data_out_ready (data_out_ready)
    );

endmodule