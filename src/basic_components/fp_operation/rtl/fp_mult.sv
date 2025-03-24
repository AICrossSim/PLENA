`timescale 1ns / 1ps

/*
Module      : Floating Point Multiplication (Full-Precision, With Sign)
Description : Multiply two FP numbers with different exponents and signs.
              Aligns mantissas, preserves full precision (no bits discarded).
              Output format: {sign, exp_out, mant_out}.
              No rounding.
              It needs normalisation and re-biased.
              (Ea - B) + (Eb - B) = (Ea + Eb - 2B)
              Extended_Exp = 0Ea + 0Eb - (1 << (Extended_Exp_WIDTH - 1)) - 1
*/

module fp_mult #(
    parameter   MANT_WIDTH = 4,
    parameter   EXP_WIDTH = 3,
    localparam  EXT_MANT_WIDTH = MANT_WIDTH + 1,                            // account for implicit 1
    localparam  RESULT_MAN_WIDTH = 2 * EXT_MANT_WIDTH - 1,                 // result after mantissa mult
    localparam  RESULT_EXP_WIDTH = EXP_WIDTH + 1                           // allow for exponent growth
) (
    input   logic [MANT_WIDTH + EXP_WIDTH : 0] data_a,
    input   logic [MANT_WIDTH + EXP_WIDTH : 0] data_b,
    output  logic [RESULT_MAN_WIDTH + RESULT_EXP_WIDTH : 0] data_out
);

    localparam int BIAS = (1 << (EXP_WIDTH - 1)) - 1;
    localparam int NEW_BIAS = (1 << (RESULT_EXP_WIDTH - 1)) - 1;
    localparam int UPDATED_BIAS = NEW_BIAS - 2*BIAS;

    // Internal signals
    logic sign_a, sign_b, sign_product;
    logic [EXP_WIDTH-1:0] exp_a, exp_b;
    logic [MANT_WIDTH-1:0] man_a, man_b;
    logic [EXT_MANT_WIDTH-1:0] man_a_ext, man_b_ext;
    logic [2*EXT_MANT_WIDTH-1:0] mant_product_full;
    logic [RESULT_MAN_WIDTH-1:0] mant_product_norm;
    logic [RESULT_EXP_WIDTH-1:0] exp_product_raw;
    logic [RESULT_EXP_WIDTH-1:0] exp_product;

    // Extract fields
    assign sign_a = data_a[MANT_WIDTH + EXP_WIDTH];
    assign exp_a  = data_a[MANT_WIDTH + EXP_WIDTH - 1 : MANT_WIDTH];
    assign man_a  = data_a[MANT_WIDTH - 1 : 0];

    assign sign_b = data_b[MANT_WIDTH + EXP_WIDTH];
    assign exp_b  = data_b[MANT_WIDTH + EXP_WIDTH - 1 : MANT_WIDTH];
    assign man_b  = data_b[MANT_WIDTH - 1 : 0];

    // Sign
    assign sign_product = sign_a ^ sign_b;

    // Add implicit leading 1
    assign man_a_ext = {1'b1, man_a};
    assign man_b_ext = {1'b1, man_b};

    // Multiply mantissas
    assign mant_product_full = man_a_ext * man_b_ext; // 2*(MANT_WIDTH+1) bits

    // Raw exponent sum (before normalisation correction)
    assign exp_product_raw = {1'b0, exp_a} + {1'b0, exp_b} + UPDATED_BIAS;

    // Normalisation logic
    always_comb begin
        if (mant_product_full[2*EXT_MANT_WIDTH-1] == 1'b0) begin
            // 
            mant_product_norm = {mant_product_full[2*EXT_MANT_WIDTH - 3 -: (RESULT_MAN_WIDTH - 1)], 1'b0};
            exp_product = exp_product_raw;
        end else begin
            // Need normalization
            mant_product_norm = mant_product_full[2*EXT_MANT_WIDTH-2 -: RESULT_MAN_WIDTH];
            exp_product = exp_product_raw + 1;
        end
    end

    // Output
    assign data_out = {sign_product, exp_product, mant_product_norm};

endmodule
