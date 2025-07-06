`timescale 1ns / 1ps
/*
Module      : Floating Point Configurable Precision Adder (With Sign)
Timing      : Combinatorial Logic
Description : FP_Adder
            - The lossy trade-off in FP adder is between output width and exp_difference.
            - (If the exponent difference is large, maintaining full precision may require a wider output to preserve underflowed bits. We choose truncate(floor) the extra, which is also the lossy part.)
*/

module fp_adder #(
    parameter int IN_EXP_WIDTH = 5,
    parameter int IN_FIX_WIDTH = 10,
    parameter int IN_FIX_FRAC_WIDTH = IN_FIX_WIDTH - 1,
    // Amount of bits needed to shift mantissas for alignment
    parameter int OUT_EXP_WIDTH = -1,
    parameter int OUT_FIX_WIDTH = -1,
    parameter int OUT_FIX_FRAC_WIDTH = -1
)(
    input  logic signed [IN_EXP_WIDTH - 1:0] exp_a,
    input  logic signed [IN_FIX_WIDTH - 1:0] mant_a,
    input  logic signed [IN_EXP_WIDTH - 1:0] exp_b,
    input  logic signed [IN_FIX_WIDTH - 1:0] mant_b,
    output logic signed [OUT_EXP_WIDTH - 1:0] exp_out,
    output logic signed [OUT_FIX_WIDTH - 1:0] mant_out
);

    localparam int DATA_FIX_WIDTH = OUT_FIX_WIDTH - 1;
    localparam int DATA_FIX_FRAC_WIDTH = OUT_FIX_FRAC_WIDTH;
    localparam int IN_FIX_INT_WIDTH = IN_FIX_WIDTH - IN_FIX_FRAC_WIDTH  - 1;
    initial begin
        assert (IN_FIX_FRAC_WIDTH <= OUT_FIX_FRAC_WIDTH)
            else $error("IN_FIX_FRAC_WIDTH must be less than OUT_FIX_FRAC_WIDTH");
        assert (OUT_FIX_FRAC_WIDTH + 2*IN_FIX_INT_WIDTH <= OUT_FIX_WIDTH)
            else $error("When OUT_FIX_FRAC_WIDTH > IN_FIX_FRAC_WIDTH, IN_FIX_WIDTH must be less than OUT_FIX_WIDTH, casting should be else where");
    end

    localparam signed FRAC_DIFF = DATA_FIX_FRAC_WIDTH - IN_FIX_FRAC_WIDTH;


    logic signed [IN_EXP_WIDTH - 1:0] exp_diff;
    logic signed [DATA_FIX_WIDTH - 1:0] mant_a_shifted, mant_b_shifted;

    always_comb begin
        if (exp_a > exp_b) begin
            exp_diff = exp_a - exp_b;
            mant_a_shifted = mant_a << FRAC_DIFF;
            mant_b_shifted = (mant_b << FRAC_DIFF) >>> exp_diff;
            exp_out = exp_a;
        end
        else begin
            exp_diff = exp_b - exp_a;
            mant_a_shifted = (mant_a << FRAC_DIFF) >>> exp_diff;
            mant_b_shifted = mant_b << FRAC_DIFF;
            exp_out = exp_b;
        end
        mant_out = mant_a_shifted + mant_b_shifted;
    end

endmodule
