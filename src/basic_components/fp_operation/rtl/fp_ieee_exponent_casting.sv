`timescale 1ns / 1ps
/*
Module      : fp_ieee_exponent_casting
Timing      : Combinatorial Logic
Description : FP_IEEE_Exponent_Casting
            - Performs casting between IEEE floating-point formats.
            - Only **reducing** bit width is allowed.
            - This operation is **lossy**: For instance, to cast a value like xxxx to x000, we **first truncate/floor** to xxx0, then apply **round-to-nearest-even**.
            - This module is used to cast the exponent of the IEEE floating-point number.
*/

module fp_ieee_exponent_casting #(
    parameter   IN_EXP_WIDTH = 5,
    parameter   OUT_EXP_WIDTH = 5,
    parameter   MANT_WIDTH = 10
)(
    input  logic [IN_EXP_WIDTH + MANT_WIDTH : 0] data_in,  // {sign, exp, mant}
    output logic [OUT_EXP_WIDTH + MANT_WIDTH : 0] data_out
);

    initial begin
        assert (IN_EXP_WIDTH >= OUT_EXP_WIDTH)
            else $error("IN_EXP_WIDTH must be greater than or equal to OUT_EXP_WIDTH");
    end

    localparam IN_BIAS = (1 << (IN_EXP_WIDTH - 1)) - 1;
    localparam OUT_BIAS = (1 << (OUT_EXP_WIDTH - 1)) - 1;

    localparam SHIFT_EXP = OUT_BIAS - IN_BIAS;

    // if 1 - OUT_BIAS <=in_exp - IN_BIAS <= 2**(OUT_EXP_WIDTH) - 1  - 1 - OUT_BIAS
    // lower bound = 1 - OUT_BIAS + IN_BIAS
    // upper bound = 2**(OUT_EXP_WIDTH) - 1 - OUT_BIAS + IN_BIAS
    localparam EXP_UPPER_BOUND = 2**(OUT_EXP_WIDTH) - 2 - OUT_BIAS + IN_BIAS;
    localparam EXP_LOWER_BOUND = 1 - OUT_BIAS + IN_BIAS;

    logic [IN_EXP_WIDTH - 1:0] in_exp;
    logic [OUT_EXP_WIDTH - 1:0] out_exp;

    assign in_exp = data_in[IN_EXP_WIDTH + MANT_WIDTH - 1:MANT_WIDTH];
    assign out_exp = in_exp - SHIFT_EXP;

    always_comb begin
        if (in_exp < EXP_LOWER_BOUND) begin
            data_out = {1'b0, {OUT_EXP_WIDTH{1'b0}}, {MANT_WIDTH{1'b0}}};
        end
        else if (in_exp > EXP_UPPER_BOUND) begin
            data_out = {data_in[IN_EXP_WIDTH + MANT_WIDTH], {(OUT_EXP_WIDTH-1){1'b1}}, 1'b0, {MANT_WIDTH{1'b1}}};
        end
        else begin
            data_out = {data_in[IN_EXP_WIDTH + MANT_WIDTH], out_exp, data_in[MANT_WIDTH - 1:0]};
        end
    end

endmodule


