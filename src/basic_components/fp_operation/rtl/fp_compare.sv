`timescale 1ns / 1ps

/*
Module      : Floating Point Comparison
Timing      : Combinatorial Logic
Description : Compares two floating point numbers (data_a and data_b).
              Provides a_gt_b, a_lt_b, and a_eq_b outputs.
              Supports custom exponent and mantissa widths.
              Follows IEEE 754 rules for +/-0.
*/

module fp_compare #(
    parameter int EXP_WIDTH = 5,
    parameter int MANT_WIDTH = 10
)(
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_a,
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_b,
    output logic a_gt_b,
    output logic a_lt_b,
    output logic a_eq_b
);

    // Bit field extractions
    logic sign_a, sign_b;
    logic [EXP_WIDTH-1:0] exp_a, exp_b;
    logic [MANT_WIDTH-1:0] mant_a, mant_b;

    assign sign_a = data_a[EXP_WIDTH + MANT_WIDTH];
    assign exp_a  = data_a[EXP_WIDTH + MANT_WIDTH - 1 : MANT_WIDTH];
    assign mant_a = data_a[MANT_WIDTH-1:0];

    assign sign_b = data_b[EXP_WIDTH + MANT_WIDTH];
    assign exp_b  = data_b[EXP_WIDTH + MANT_WIDTH - 1 : MANT_WIDTH];
    assign mant_b = data_b[MANT_WIDTH-1:0];

    logic is_zero_a, is_zero_b;
    assign is_zero_a = (exp_a == '0) && (mant_a == '0);
    assign is_zero_b = (exp_b == '0) && (mant_b == '0);

    always_comb begin
        a_gt_b = 1'b0;
        a_lt_b = 1'b0;
        a_eq_b = 1'b0;

        if (is_zero_a && is_zero_b) begin
            // +/-0 are equal
            a_eq_b = 1'b1;
        end else if (data_a == data_b) begin
            a_eq_b = 1'b1;
        end else if (sign_a != sign_b) begin
            // Signs are different: positive is always greater
            if (sign_a == 1'b0) a_gt_b = 1'b1;
            else                a_lt_b = 1'b1;
        end else begin
            // Signs are the same
            if (sign_a == 1'b0) begin
                // Both positive: standard magnitude comparison
                if (exp_a > exp_b)      a_gt_b = 1'b1;
                else if (exp_a < exp_b) a_lt_b = 1'b1;
                else if (mant_a > mant_b) a_gt_b = 1'b1;
                else if (mant_a < mant_b) a_lt_b = 1'b1;
                else                      a_eq_b = 1'b1;
            end else begin
                // Both negative: smaller absolute magnitude is greater
                if (exp_a > exp_b)      a_lt_b = 1'b1;
                else if (exp_a < exp_b) a_gt_b = 1'b1;
                else if (mant_a > mant_b) a_lt_b = 1'b1;
                else if (mant_a < mant_b) a_gt_b = 1'b1;
                else                      a_eq_b = 1'b1;
            end
        end
    end

endmodule
