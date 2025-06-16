`timescale 1ns / 1ps
/*
Module      : Floating Point Configurable Precision Adder (With Sign)
Timing      : Combinatorial Logic
Description : Adds two FP numbers with different exponents and signs.
              Aligns mantissas, preserves full precision (no bits discarded).
              Output format: {sign, exp_out, mant_out}.
              No rounding.
              It needs normalisation.
              The lossy part will be at the mantissa adder
Status      : Passed Simple Tests
*/

module fp_cp_adder #(
    parameter int EXP_WIDTH = 5,
    parameter int MANT_WIDTH = 10,
    // Amount of bits needed to shift mantissas for alignment
    parameter int EXT_MANT_WIDTH = 0,
    // Need to increase exp width by 1 to handle overflow
    parameter int EXT_EXP_WIDTH = 0
)(
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_a,  // {sign, exp, mant}
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_b,
    output logic [EXP_WIDTH + EXT_EXP_WIDTH + MANT_WIDTH + EXT_MANT_WIDTH : 0] data_out
);

    localparam int IN_EXP_WIDTH = EXP_WIDTH;
    localparam int IN_FIXED_WIDTH = MANT_WIDTH + 2;
    localparam int IN_FIXED_FRAC_WIDTH = MANT_WIDTH;

    localparam int ADDER_OUT_EXP_WIDTH = EXP_WIDTH + EXT_MANT_WIDTH;
    localparam int ADDER_OUT_FIXED_WIDTH = IN_FIXED_WIDTH + EXT_MANT_WIDTH;
    localparam int ADDER_OUT_FIXED_FRAC_WIDTH = IN_FIXED_FRAC_WIDTH;

    // Internal signal declarations
    logic signed [IN_EXP_WIDTH - 1:0] signed_exp_a, signed_exp_b;
    logic signed [IN_FIXED_WIDTH - 1:0] signed_mant_a, signed_mant_b;

    logic signed [ADDER_OUT_EXP_WIDTH - 1:0] signed_exp_out;
    logic signed [ADDER_OUT_FIXED_WIDTH - 1:0] signed_mant_out;
    
    // Extended signals for normalization
    logic signed [EXP_WIDTH + EXT_EXP_WIDTH - 1:0] exp_out_ext;
    logic signed [MANT_WIDTH + EXT_MANT_WIDTH + 2 - 1:0] mant_out_ext;

    // Instantiate fp_ieee_partition for data_a
    fp_ieee_partition #(
        .EXP_WIDTH(EXP_WIDTH),
        .MANT_WIDTH(MANT_WIDTH),
    ) fp_a (
        .data_in(data_a),
        .signed_exp(signed_exp_a),
        .signed_mant(signed_mant_a)
    );

    // Instantiate fp_ieee_partition for data_b
    fp_ieee_partition #(
        .EXP_WIDTH(EXP_WIDTH),
        .MANT_WIDTH(MANT_WIDTH),
        .OUT_MANT_WIDTH(MANT_WIDTH + 2)
    ) fp_b (
        .data_in(data_b),
        .signed_exp(signed_exp_b),
        .signed_mant(signed_mant_b)
    );

    // Instantiate fp_adder
    fp_adder #(
        .IN_EXP_WIDTH(IN_EXP_WIDTH),
        .IN_FIX_WIDTH(IN_FIXED_WIDTH),
        .IN_FIX_FRAC_WIDTH(IN_FIXED_FRAC_WIDTH),
        .OUT_EXP_WIDTH(ADDER_OUT_EXP_WIDTH),
        .OUT_FIX_WIDTH(ADDER_OUT_FIXED_WIDTH),
        .OUT_FIX_FRAC_WIDTH(ADDER_OUT_FIXED_FRAC_WIDTH)
    ) fp_adder_inst (
        .exp_a(signed_exp_a),
        .mant_a(signed_mant_a),
        .exp_b(signed_exp_b),
        .mant_b(signed_mant_b),
        .exp_out(signed_exp_out),
        .mant_out(signed_mant_out)
    );

    // Instantiate fp_ieee_normalize for output
    fp_ieee_normalize #(
        .EXP_WIDTH(ADDER_OUT_EXP_WIDTH),
        .MANT_WIDTH(ADDER_OUT_FIXED_WIDTH)
    ) fp_normalize (
        .signed_mant(mant_out_ext),
        .signed_exp(exp_out_ext),
        .fp_out(data_out)
    );

endmodule
