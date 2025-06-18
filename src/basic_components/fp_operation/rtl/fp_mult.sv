`timescale 1ns / 1ps
/*
Module      : Floating Point Configurable Precision Adder (With Sign)
Timing      : Combinatorial Logic
Description : Adds two FP numbers with different exponents and signs.
              Aligns mantissas, preserves full precision (no bits discarded).
              Output format: {sign, exp_out, mant_out}.
              No rounding.
              It needs normalisation.
Status      : Passed Simple Tests
*/

module fp_mult #(
    parameter int IN_EXP_WIDTH = 5,
    parameter int IN_FIX_WIDTH = 10,
    parameter int IN_FIX_FRAC_WIDTH = IN_FIX_WIDTH - 1,
    parameter int OUT_FIX_FRAC_WIDTH = IN_FIX_FRAC_WIDTH + IN_FIX_FRAC_WIDTH,
    // Amount of bits needed to shift mantissas for alignment
    localparam int OUT_FIX_WIDTH = 1 + (IN_FIX_WIDTH - IN_FIX_FRAC_WIDTH - 1) * 2 + OUT_FIX_FRAC_WIDTH,
    localparam int OUT_EXP_WIDTH = IN_EXP_WIDTH + 1
)(
    input  logic signed [IN_EXP_WIDTH - 1:0] exp_a,
    input  logic signed [IN_FIX_WIDTH - 1:0] mant_a,
    input  logic signed [IN_EXP_WIDTH - 1:0] exp_b,
    input  logic signed [IN_FIX_WIDTH - 1:0] mant_b,
    output logic signed [OUT_EXP_WIDTH - 1:0] exp_out,
    output logic signed [OUT_FIX_WIDTH - 1:0] mant_out
);

    localparam int INTERMEDIATE_FIX_WIDTH = IN_FIX_WIDTH + IN_FIX_WIDTH - 1;
    localparam int INTERMEDIATE_FIX_FRAC_WIDTH = IN_FIX_FRAC_WIDTH + IN_FIX_FRAC_WIDTH;

    initial begin
        assert (IN_FIX_WIDTH <= OUT_FIX_WIDTH)
            else $error("IN_FIX_WIDTH must be less or equal than OUT_FIX_WIDTH");
    end

    logic signed [INTERMEDIATE_FIX_WIDTH - 1:0] intermediate_mant;

    always_comb begin
        exp_out = exp_a + exp_b;
        intermediate_mant = mant_a * mant_b;
        mant_out = intermediate_mant[INTERMEDIATE_FIX_WIDTH - 1 : INTERMEDIATE_FIX_WIDTH - OUT_FIX_WIDTH];
    end

endmodule
