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
    localparam EXP_LOWER_BOUND = 0 - OUT_BIAS + IN_BIAS;

    logic [IN_EXP_WIDTH - 1:0] in_exp;
    logic [OUT_EXP_WIDTH - 1:0] out_exp;

    logic [IN_EXP_WIDTH - 1:0] exp_difference;
    logic [MANT_WIDTH+2:0] mantissa;
    logic [MANT_WIDTH+2:0] mantissa_shifted;
    logic [MANT_WIDTH-1:0] mantissa_rounded;
    logic round_up;

    assign in_exp = data_in[IN_EXP_WIDTH + MANT_WIDTH - 1:MANT_WIDTH];
    assign out_exp = in_exp - SHIFT_EXP;

    assign exp_difference = EXP_LOWER_BOUND - in_exp;
    assign mantissa = in_exp != 0 ? {1'b1, data_in[MANT_WIDTH - 1:0], 2'd0} : {1'b0, data_in[MANT_WIDTH - 1:0], 2'd0};

    bit_width_aware_right_shift #(
        .IN_WIDTH(MANT_WIDTH + 3),
        .OUT_WIDTH(MANT_WIDTH + 3),
        .SHIFT_WIDTH(IN_EXP_WIDTH)
    ) bit_width_aware_right_shift_inst (
        .in_data(mantissa),
        .shift_amt(exp_difference),
        .out_data(mantissa_shifted)
    );

    round_to_nearest_even #(
        .IN_WIDTH(MANT_WIDTH + 2),
        .OUT_WIDTH(MANT_WIDTH)
    ) round_to_nearest_even_inst (
        .data_in(mantissa_shifted[MANT_WIDTH+1:0]),
        .data_out(mantissa_rounded)
    );

    assign round_up = mantissa[MANT_WIDTH+1] && (|mantissa_rounded[MANT_WIDTH:0]);

    always_comb begin
        if (in_exp < EXP_LOWER_BOUND) begin
            data_out = {1'b0, {OUT_EXP_WIDTH{1'b0}}, mantissa_rounded};
        end
        else if (in_exp == EXP_LOWER_BOUND) begin
            data_out = round_up ? {1'b0, {OUT_EXP_WIDTH-1{1'b0}}, 1'b1, {MANT_WIDTH{1'b0}}} : {1'b0, {OUT_EXP_WIDTH{1'b0}}, {MANT_WIDTH{1'b1}}};
        end
        else if (in_exp > EXP_UPPER_BOUND) begin
            data_out = {data_in[IN_EXP_WIDTH + MANT_WIDTH], {(OUT_EXP_WIDTH-1){1'b1}}, 1'b0, {MANT_WIDTH{1'b1}}};
        end
        else begin
            data_out = {data_in[IN_EXP_WIDTH + MANT_WIDTH], out_exp, data_in[MANT_WIDTH - 1:0]};
        end
    end

endmodule


