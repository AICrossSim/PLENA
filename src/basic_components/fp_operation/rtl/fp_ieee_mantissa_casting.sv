`timescale 1ns / 1ps
/*
Module      : fp_ieee_mantissa_casting
Timing      : Combinatorial Logic
Description : FP_IEEE_Mantissa_Casting
            - Performs casting between IEEE floating-point formats.
            - Only **reducing** bit width is allowed.
            - This operation is **lossy**: For instance, to cast a value like xxxx to x000, we **first truncate/floor** to xxx0, then apply **round-to-nearest-even**.
            - This module is used to cast the mantissa of the IEEE floating-point number.
*/
module fp_ieee_mantissa_casting #(
    parameter   EXP_WIDTH = 5,
    parameter   IN_MANT_WIDTH = 10,
    parameter   OUT_MANT_WIDTH = 8
)(
    input  logic [EXP_WIDTH + IN_MANT_WIDTH : 0] data_in,  // {sign, exp, mant}
    output logic [EXP_WIDTH + OUT_MANT_WIDTH : 0] data_out
);
    initial begin
        assert (IN_MANT_WIDTH >= OUT_MANT_WIDTH)
            else $error("IN_MANT_WIDTH must be greater than or equal to OUT_MANT_WIDTH");
    end

    logic [IN_MANT_WIDTH - 1:0] in_mant;
    logic [OUT_MANT_WIDTH - 1:0] out_mant;

    assign in_mant = data_in[IN_MANT_WIDTH - 1:0];

    round_to_nearest_even #(
        .IN_WIDTH(IN_MANT_WIDTH),
        .OUT_WIDTH(OUT_MANT_WIDTH)
    ) round_to_nearest_even_inst (
        .data_in(in_mant),
        .data_out(out_mant)
    );
    assign data_out = {data_in[EXP_WIDTH + IN_MANT_WIDTH:IN_MANT_WIDTH], out_mant};
endmodule