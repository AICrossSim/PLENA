`timescale 1ns / 1ps
/*
Module      : Floating Point Asymmetric Configurable Precision Adder (With Sign)
Timing      : Combinatorial Logic
Description : Adds two FP numbers with different exponents and signs.
              Aligns mantissas, preserves full precision (no bits discarded).
              Output format: {sign, exp_out, mant_out}.
              No rounding.
              It needs normalisation.
              The lossy part will be at the mantissa adder
Status      : Passed Simple Tests
*/

module fp_cp_asym_mult #(
    parameter int EXP_WIDTH_A       = 5,
    parameter int MANT_WIDTH_A      = 10,
    parameter int EXP_WIDTH_B       = 5,
    parameter int MANT_WIDTH_B      = 10,
    // Amount of bits needed to shift mantissas for alignment
    parameter int EXT_MANT_WIDTH    = 0,
    // Need to increase exp width by 1 to handle overflow
    parameter int EXT_EXP_WIDTH     = 0,
    localparam int OUT_EXP_WIDTH    = (IN_EXP_WIDTH_A > IN_EXP_WIDTH_B ? IN_EXP_WIDTH_A : IN_EXP_WIDTH_B),
    localparam int OUT_MANT_WIDTH   = (IN_MANT_WIDTH_A > IN_MANT_WIDTH_B ? IN_MANT_WIDTH_A : IN_MANT_WIDTH_B)
)(
    input  logic [EXP_WIDTH_A + MANT_WIDTH_A : 0] data_a,  // {sign, exp, mant}
    input  logic [EXP_WIDTH_B + MANT_WIDTH_B : 0] data_b,
    output logic [OUT_EXP_WIDTH + EXT_EXP_WIDTH + OUT_MANT_WIDTH + EXT_MANT_WIDTH : 0] data_out
);

    localparam int IN_EXP_WIDTH_A = EXP_WIDTH_A;
    localparam int IN_FIXED_WIDTH_A = MANT_WIDTH_A + 2;
    localparam int IN_FIXED_FRAC_WIDTH_A = MANT_WIDTH_A;
    localparam int IN_EXP_WIDTH_B = EXP_WIDTH_B;
    localparam int IN_FIXED_WIDTH_B = MANT_WIDTH_B + 2;
    localparam int IN_FIXED_FRAC_WIDTH_B = MANT_WIDTH_B;

    localparam int MULT_OUT_EXP_WIDTH = OUT_EXP_WIDTH + 1;
    localparam int MULT_OUT_FIXED_FRAC_WIDTH = IN_FIXED_FRAC_WIDTH_A + IN_FIXED_FRAC_WIDTH_B;
    localparam int MULT_OUT_FIXED_WIDTH = 1 + (IN_EXP_WIDTH_A - IN_FIXED_FRAC_WIDTH_A - 1) + (IN_EXP_WIDTH_B - IN_FIXED_FRAC_WIDTH_B - 1) + MULT_OUT_FIXED_FRAC_WIDTH;

    localparam int NORMALIZE_OUT_EXP_WIDTH  = MULT_OUT_EXP_WIDTH + 1;
    localparam int NORMALIZE_OUT_MANT_WIDTH = MULT_OUT_FIXED_WIDTH - 1;

    // Internal signal declarations
    logic signed [IN_EXP_WIDTH_A - 1:0] signed_exp_a;
    logic signed [IN_FIXED_WIDTH_A - 1:0] signed_mant_a;
    logic signed [IN_EXP_WIDTH_B - 1:0] signed_exp_b;
    logic signed [IN_FIXED_WIDTH_B - 1:0] signed_mant_b;

    logic signed [MULT_OUT_EXP_WIDTH - 1:0] signed_exp_out;
    logic signed [MULT_OUT_FIXED_WIDTH - 1:0] signed_mant_out;

    logic signed [NORMALIZE_OUT_EXP_WIDTH + NORMALIZE_OUT_MANT_WIDTH:0] normalized_data;

    // Instantiate fp_ieee_partition for data_a
    fp_ieee_partition #(
        .EXP_WIDTH(EXP_WIDTH_A),
        .MANT_WIDTH(MANT_WIDTH_A)
    ) partition_a (
        .data_in(data_a),
        .signed_exp(signed_exp_a),
        .signed_mant(signed_mant_a)
    );

    // Instantiate fp_ieee_partition for data_b
    fp_ieee_partition #(
        .EXP_WIDTH(EXP_WIDTH_B),
        .MANT_WIDTH(MANT_WIDTH_B)
    ) partition_b (
        .data_in(data_b),
        .signed_exp(signed_exp_b),
        .signed_mant(signed_mant_b)
    );

    // Instantiate fp_mult
    fp_asym_mult #(
        .IN_EXP_WIDTH_A(IN_EXP_WIDTH_A),
        .IN_FIX_WIDTH_A(IN_FIX_WIDTH_A),
        .IN_FIX_FRAC_WIDTH_A(IN_FIXED_FRAC_WIDTH_A),
        .IN_EXP_WIDTH_B(IN_EXP_WIDTH_B),
        .IN_FIX_WIDTH_B(IN_FIX_WIDTH_B),
        .IN_FIX_FRAC_WIDTH_B(IN_FIXED_FRAC_WIDTH_B),
        .IN_FIX_FRAC_WIDTH(IN_FIXED_FRAC_WIDTH),
        .OUT_FIX_FRAC_WIDTH(MULT_OUT_FIXED_FRAC_WIDTH)
    ) fp_mult_inst (
        .exp_a(signed_exp_a),
        .mant_a(signed_mant_a),
        .exp_b(signed_exp_b),
        .mant_b(signed_mant_b),
        .exp_out(signed_exp_out),
        .mant_out(signed_mant_out)
    );


    // Instantiate fp_ieee_normalize for output
    fp_ieee_normalize #(
        .IN_FIXED_WIDTH(MULT_OUT_FIXED_WIDTH),
        .IN_FIXED_FRAC_WIDTH(MULT_OUT_FIXED_FRAC_WIDTH),
        .IN_EXP_WIDTH(MULT_OUT_EXP_WIDTH),
        .OUT_MANT_WIDTH(NORMALIZE_OUT_MANT_WIDTH)
    ) fp_normalize (
        .signed_mant(signed_mant_out),
        .signed_exp(signed_exp_out),
        .fp_out(normalized_data)
    );

    fp_ieee_casting #(
        .IN_EXP_WIDTH(NORMALIZE_OUT_EXP_WIDTH),
        .IN_MANT_WIDTH(NORMALIZE_OUT_MANT_WIDTH),
        .OUT_EXP_WIDTH(EXP_WIDTH + EXT_EXP_WIDTH),
        .OUT_MANT_WIDTH(MANT_WIDTH + EXT_MANT_WIDTH)
    ) fp_casting (
        .data_in(normalized_data),
        .data_out(data_out)
    );

endmodule
