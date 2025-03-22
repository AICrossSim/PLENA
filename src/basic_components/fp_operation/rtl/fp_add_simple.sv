`timescale 1ns / 1ps
/*
Module      : Floating Point Adder (Aligned Exponent)
Description : Adds two FP numbers with possibly different exponents.
              Outputs extended exponent and mantissa sum.
              Note that, the shifting will lose precision in this case.
              No rounding or normalisation included.
*/

module fp_add #(
    parameter int EXP_WIDTH = 5,
    parameter int MANT_WIDTH = 10
)(
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_a,  // {exp, mant}
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_b,
    output logic [EXP_WIDTH:0] exp_out,                // extended exponent
    output logic [MANT_WIDTH+1:0] mant_out             // extended mantissa (with carry)
);

    // Field decomposition
    logic [EXP_WIDTH-1:0] exp_a, exp_b;
    logic [MANT_WIDTH-1:0] mant_a, mant_b;

    // Extended mantissas
    logic [MANT_WIDTH:0] full_mant_a, full_mant_b;
    logic [MANT_WIDTH+1:0] mant_a_shifted, mant_b_shifted;
    logic [MANT_WIDTH+2:0] mant_sum;

    logic [EXP_WIDTH:0] exp_diff;
    logic [EXP_WIDTH:0] exp_max;

    always_comb begin
        // Extract fields
        exp_a  = data_a[EXP_WIDTH + MANT_WIDTH : MANT_WIDTH];
        mant_a = data_a[MANT_WIDTH-1:0];

        exp_b  = data_b[EXP_WIDTH + MANT_WIDTH : MANT_WIDTH];
        mant_b = data_b[MANT_WIDTH-1:0];

        // Add hidden bit
        full_mant_a = {1'b1, mant_a};
        full_mant_b = {1'b1, mant_b};

        // Align mantissas based on exponent difference
        if (exp_a > exp_b) begin
            exp_diff       = exp_a - exp_b;
            mant_a_shifted = {1'b0, full_mant_a}; // Extend by 1 to prevent overflow
            mant_b_shifted = ({1'b0, full_mant_b} >> exp_diff);
            exp_max        = exp_a;
        end else begin
            exp_diff       = exp_b - exp_a;
            mant_a_shifted = ({1'b0, full_mant_a} >> exp_diff);
            mant_b_shifted = {1'b0, full_mant_b};
            exp_max        = exp_b;
        end

        // Add aligned mantissas
        mant_sum = mant_a_shifted + mant_b_shifted;

        // Optional overflow handling (e.g., normalisation) — not included

        // Assign outputs
        mant_out = mant_sum[MANT_WIDTH+1:0]; // Preserve carry
        exp_out  = exp_max;
    end

endmodule
