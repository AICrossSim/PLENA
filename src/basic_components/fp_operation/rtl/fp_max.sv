`timescale 1ns / 1ps
/*
Module      : Floating Point Max (With Sign)
Timing      : Combinatorial Logic
Description : Compare two FP numbers with different exponents and signs.
              Returns the maximum of the two numbers.
              Output format: {sign, exp_out, mant_out}.
              No rounding.
Status      : Passed Simple Tests
*/

module fp_max #(
    parameter int EXP_WIDTH = 5,
    parameter int MANT_WIDTH = 10
)(
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_a,  // {sign, exp, mant}
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_b,
    output logic [EXP_WIDTH + MANT_WIDTH : 0] data_out
);

    // Bit field declarations
    logic sign_a, sign_b, sign_res;
    logic [EXP_WIDTH-1:0] exp_a, exp_b;
    logic [MANT_WIDTH-1:0] mant_a, mant_b;

    // Extract sign, exponent, mantissa
    assign sign_a = data_a[EXP_WIDTH + MANT_WIDTH];
    assign exp_a  = data_a[EXP_WIDTH + MANT_WIDTH - 1 : MANT_WIDTH];
    assign mant_a = data_a[MANT_WIDTH-1:0];

    assign sign_b = data_b[EXP_WIDTH + MANT_WIDTH];
    assign exp_b  = data_b[EXP_WIDTH + MANT_WIDTH -1 : MANT_WIDTH];
    assign mant_b = data_b[MANT_WIDTH-1:0];

    // Compare signs and exponents
    always_comb begin
        if (sign_a == sign_b) begin
            if (exp_a > exp_b) begin
                data_out = data_a;
            end else if (exp_a < exp_b) begin
                data_out = data_b;
            end else begin
                if (mant_a > mant_b) begin
                    data_out = data_a;
                end else begin
                    data_out = data_b;
                end
            end
        end else begin
            if (sign_a == 1'b0) begin
                data_out = data_a;
            end else begin
                data_out = data_b;
            end
        end
    end



endmodule