`timescale 1ns / 1ps
/*
Module      : Floating Point Adder (Full-Precision, With Sign)
Description : Adds two FP numbers with different exponents and signs.
              Aligns mantissas, preserves full precision (no bits discarded).
              Output format: {sign, exp_out, mant_out}.
              No rounding or normalisation.
*/

module fp_add_full_precision #(
    parameter int EXP_WIDTH = 5,
    parameter int MANT_WIDTH = 10,

    // Max possible shift bits needed
    localparam int EXT_BITS = (1 << EXP_WIDTH)
)(
    input  logic [EXP_WIDTH + MANT_WIDTH + 1 : 0] data_a,  // {sign, exp, mant}
    input  logic [EXP_WIDTH + MANT_WIDTH + 1 : 0] data_b,
    output logic [EXP_WIDTH + MANT_WIDTH + EXT_BITS + 2 : 0] data_out // {sign, exp, mant}
);

    // Bit field declarations
    logic sign_a, sign_b, sign_res;
    logic [EXP_WIDTH-1:0] exp_a, exp_b;
    logic [MANT_WIDTH-1:0] mant_a, mant_b;

    logic [MANT_WIDTH + EXT_BITS:0] full_mant_a, full_mant_b;
    logic [MANT_WIDTH + EXT_BITS:0] mant_a_shifted, mant_b_shifted;
    logic [MANT_WIDTH + EXT_BITS + 1:0] mant_sum;

    logic [EXP_WIDTH:0] exp_diff;
    logic [EXP_WIDTH:0] exp_max;

    always_comb begin
        // Extract sign, exponent, mantissa
        sign_a = data_a[EXP_WIDTH + MANT_WIDTH + 1];
        exp_a  = data_a[EXP_WIDTH + MANT_WIDTH : MANT_WIDTH];
        mant_a = data_a[MANT_WIDTH-1:0];

        sign_b = data_b[EXP_WIDTH + MANT_WIDTH + 1];
        exp_b  = data_b[EXP_WIDTH + MANT_WIDTH : MANT_WIDTH];
        mant_b = data_b[MANT_WIDTH-1:0];

        // Add implicit 1 and pad for alignment
        full_mant_a = {1'b1, mant_a, {EXT_BITS{1'b0}}};
        full_mant_b = {1'b1, mant_b, {EXT_BITS{1'b0}}};

        // Align mantissas
        if (exp_a > exp_b) begin
            exp_diff       = exp_a - exp_b;
            mant_a_shifted = full_mant_a;
            mant_b_shifted = full_mant_b >> exp_diff;
            exp_max        = exp_a;
        end else begin
            exp_diff       = exp_b - exp_a;
            mant_a_shifted = full_mant_a >> exp_diff;
            mant_b_shifted = full_mant_b;
            exp_max        = exp_b;
        end

        // Add/Subtract based on signs
        if (sign_a == sign_b) begin
            mant_sum = mant_a_shifted + mant_b_shifted;
            sign_res = sign_a;
        end else begin
            if (mant_a_shifted >= mant_b_shifted) begin
                mant_sum = mant_a_shifted - mant_b_shifted;
                sign_res = sign_a;
            end else begin
                mant_sum = mant_b_shifted - mant_a_shifted;
                sign_res = sign_b;
            end
        end

        // Output final packed value: {sign, exponent, extended mantissa}
        data_out = {sign_res, exp_max, mant_sum};
    end

endmodule
