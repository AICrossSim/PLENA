`timescale 1ns / 1ps
// `include "operation.svh"

/*
Module      : FP Square Root
Timing      : Combinatorial Logic
Description : This module computes the square root of a floating point number
Status      : Under Development
*/

module fp_cp_sqrt #(
    parameter   EXP_WIDTH = 5,
    parameter   MANT_WIDTH = 10
)(
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_in,  // {sign, exp, mant}
    output logic [EXP_WIDTH + MANT_WIDTH : 0] data_out
);

    // initial begin
    //     assert (data_in[EXP_WIDTH + MANT_WIDTH : 0] != 0) else $error("data_in is not positive");
    // end
    logic sign_bit;
    assign sign_bit = data_in[EXP_WIDTH + MANT_WIDTH];
    
    // Runtime check for positive input
    // TODO Hide here due to multiple drive for data_out.
    
    logic [EXP_WIDTH + MANT_WIDTH : 0] computed_out;

    // always_comb begin
    //     if (sign_bit) begin
    //         // Handle negative input - return 0 or NaN
    //         data_out = '0; // Return 0 for negative inputs
    //     end
    // end
    assign data_out = sign_bit ? '0 : computed_out;

    localparam SIGN_MANT_WIDTH = MANT_WIDTH + 2;
    localparam UNSIGNED_MANT_WIDTH = MANT_WIDTH + 1;

    logic signed [SIGN_MANT_WIDTH-1:0] sign_mant;
    logic signed [EXP_WIDTH-1:0] signed_exp;

    logic [SIGN_MANT_WIDTH-1:0] signed_sqrt_mantissa;

    fp_ieee_partition #(
        .EXP_WIDTH(EXP_WIDTH),
        .MANT_WIDTH(MANT_WIDTH)
    ) fp_ieee_partition_inst (
        .data_in(data_in),
        .signed_mant(sign_mant),
        .signed_exp(signed_exp)
    );

    logic [EXP_WIDTH-1:0] new_exp;
    logic [MANT_WIDTH-1:0] new_mant;

    // For sqrt, exponent is divided by 2
    // If exponent is odd, we need to adjust the mantissa
    localparam K = 8'd127; // The value of 2^(0.5)
    
    always_comb begin
        if (!sign_bit) begin
            new_exp = (signed_exp[0] == 0) ? signed_exp >> 1 : (signed_exp - 1) >> 1;
            new_mant = (signed_exp[0] == 0) ? sign_mant : (sign_mant * K);
        end else begin
            new_exp = '0;
            new_mant = '0;
        end
    end

    // TODO
    logic [MANT_WIDTH : 0] round_new_mant;

    fixed_round #(
        .IN_WIDTH(SIGN_MANT_WIDTH + 8),
        .IN_FRAC_WIDTH(SIGN_MANT_WIDTH - 2 + 6),
        .OUT_WIDTH(SIGN_MANT_WIDTH),
        .OUT_FRAC_WIDTH(SIGN_MANT_WIDTH - 2)
    ) fixed_round_inst (
        .data_in(new_mant),
        .data_out(round_new_mant)
    );

    sqrt_lut #(
        .MANT_WIDTH(UNSIGNED_MANT_WIDTH)
    ) sqrt_lut_inst (
        .mantissa(round_new_mant[UNSIGNED_MANT_WIDTH-1:0]),
        .sqrt_mantissa(signed_sqrt_mantissa)
    );

    fp_ieee_normalize #(
        .EXP_WIDTH(EXP_WIDTH),
        .MANT_WIDTH(MANT_WIDTH)
    ) fp_ieee_normalize_inst (
        .signed_mant(signed_sqrt_mantissa),
        .signed_exp(new_exp),
        .fp_out(computed_out)
    );

endmodule

module sqrt_lut #(
    parameter   MANT_WIDTH = 10
)(
    input  logic [MANT_WIDTH-1:0] mantissa,
    output logic [MANT_WIDTH-1:0] sqrt_mantissa
);

    // TODO: Generate LUT
    assign sqrt_mantissa = mantissa;
endmodule
