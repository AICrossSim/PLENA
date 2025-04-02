`timescale 1ns / 1ps
/*
Module      : Floating Point Configurable Precision Multiplier (With Sign)
Timing      : Combinatorial Logic
Description : Multiply two FP numbers with different exponents and signs.
              Aligns mantissas, preserves full precision (no bits discarded).
              Output format: {sign, exp_out, mant_out}.
              No rounding.
              It needs normalisation.
Status      : Passed Simple Tests
*/

module fp_cp_mult #(
    parameter   MANT_WIDTH = 4,
    parameter   EXP_WIDTH = 3,
    // Amount of bits needed to shift mantissas for alignment
    parameter   EXT_MANT_WIDTH = 4,
    // Need to increase exp width by 1 to handle overflow
    parameter   EXT_EXP_WIDTH = 1
) (
    input   logic [MANT_WIDTH + EXP_WIDTH : 0] data_a,
    input   logic [MANT_WIDTH + EXP_WIDTH : 0] data_b,
    output  logic [EXP_WIDTH + EXT_EXP_WIDTH + MANT_WIDTH + EXT_MANT_WIDTH : 0] data_out
);
    initial begin
        // To ensure the unnecessary bits in mantissa.
        assert (EXT_MANT_WIDTH <= MANT_WIDTH + 1);
    end
    localparam int BIAS = (1 << (EXP_WIDTH - 1)) - 1;
    localparam int NEW_BIAS = (1 << ((EXP_WIDTH + EXT_EXP_WIDTH) - 1)) - 1;
    localparam int UPDATED_BIAS = NEW_BIAS - 2*BIAS;

    // Internal signals
    logic sign_a, sign_b, sign_product;
    logic [EXP_WIDTH-1:0] exp_a, exp_b;
    logic [MANT_WIDTH-1:0] man_a, man_b;
    logic [MANT_WIDTH : 0] man_a_ext, man_b_ext;

    logic [2*(MANT_WIDTH + 1) - 1:0] mant_product_full;

    logic [MANT_WIDTH + EXT_MANT_WIDTH - 1:0] mant_product_norm;
    logic [EXP_WIDTH : 0] exp_product_raw;
    logic [EXP_WIDTH + EXT_EXP_WIDTH-1:0] exp_product;

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
    assign exp_product_raw = {{EXT_EXP_WIDTH{1'b0}}, exp_a} + {{EXT_EXP_WIDTH{1'b0}}, exp_b} + UPDATED_BIAS;

    // Normalisation logic
    always_comb begin
        if (mant_product_full[2*EXT_MANT_WIDTH-1] == 1'b0) begin
            // If no normalization needed, 1_xxxx * 1_xxxx = 01_xxxx_xxxx
            mant_product_norm = {mant_product_full[2*EXT_MANT_WIDTH - 3 -: (MANT_WIDTH + EXT_MANT_WIDTH)]};
            exp_product = exp_product_raw;
        end else begin
            // If normalization needed, 1_xxxx * 1_xxxx = 1x_xxxx_xxxx
            mant_product_norm = mant_product_full[2*EXT_MANT_WIDTH-2 -: (MANT_WIDTH + EXT_MANT_WIDTH)];
            exp_product = exp_product_raw + 1;
        end
    end

    // Output
    assign data_out = {sign_product, exp_product, mant_product_norm};

endmodule
