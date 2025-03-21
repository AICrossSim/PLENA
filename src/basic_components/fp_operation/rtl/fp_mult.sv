`timescale 1ns / 1ps
// fixed-point multiplier

module fp_mult #(
    parameter   A_MAN_WIDTH = 4,
    parameter   A_EXP_WIDTH = 3,
    parameter   B_MAN_WIDTH = 4,
    parameter   B_EXP_WIDTH = 3,
    localparam  RESULT_MAN_WIDTH = A_MAN_WIDTH + B_MAN_WIDTH + 1,
    localparam  RESULT_EXP_WIDTH = A_EXP_WIDTH
) (
    input   logic [A_MAN_WIDTH + A_EXP_WIDTH : 0] data_a,
    input   logic [B_MAN_WIDTH + B_EXP_WIDTH : 0] data_b,
    output  logic [RESULT_MAN_WIDTH + RESULT_EXP_WIDTH : 0] product
);

    // Internal signals
    logic sign_a, sign_b, sign_product;
    logic [A_EXP_WIDTH-1:0] exp_a;
    logic [B_EXP_WIDTH-1:0] exp_b;
    logic [A_MAN_WIDTH-1:0] man_a;
    logic [B_MAN_WIDTH-1:0] man_b;
    logic [RESULT_MAN_WIDTH-1:0] mant_product;
    logic [RESULT_EXP_WIDTH-1:0] exp_product;

    // Extract fields from input
    assign sign_a = data_a[A_MAN_WIDTH + A_EXP_WIDTH];
    assign exp_a  = data_a[A_MAN_WIDTH + A_EXP_WIDTH - 1 : A_MAN_WIDTH];
    assign man_a  = data_a[A_MAN_WIDTH - 1 : 0];

    assign sign_b = data_b[B_MAN_WIDTH + B_EXP_WIDTH];
    assign exp_b  = data_b[B_MAN_WIDTH + B_EXP_WIDTH - 1 : B_MAN_WIDTH];
    assign man_b  = data_b[B_MAN_WIDTH - 1 : 0];

    // Compute sign
    assign sign_product = sign_a ^ sign_b;

    // Multiply mantissas (unsigned)
    assign mant_product = man_a * man_b;

    // Add exponents (unsigned), assume no overflow
    assign exp_product = exp_a + exp_b;

    // Concatenate the result
    assign product = {sign_product, exp_product, mant_product};

endmodule
