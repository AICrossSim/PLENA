`timescale 1ns / 1ps
/*
Module      : fp_ieee_casting
Timing      : Combinatorial Logic
Description : FP_IEEE_Casting
            - Performs casting between IEEE floating-point formats.
            - Only **reducing** bit width is allowed.
            - This operation is **lossy**: For instance, to cast a value like xxxx to x000, we **first truncate/floor** to xxx0, then apply **round-to-nearest-even**.
*/

module fp_ieee_casting #(
    parameter   IN_EXP_WIDTH = 5,
    parameter   IN_MANT_WIDTH = 10,
    parameter   OUT_EXP_WIDTH = 5,
    parameter   OUT_MANT_WIDTH = 8
)(
    input  logic [IN_EXP_WIDTH + IN_MANT_WIDTH : 0] data_in,  // {sign, exp, mant}
    output logic [OUT_EXP_WIDTH + OUT_MANT_WIDTH : 0] data_out
);
    initial begin
        assert (IN_EXP_WIDTH >= OUT_EXP_WIDTH)
            else $error("IN_EXP_WIDTH must be greater than or equal to OUT_EXP_WIDTH");
        assert (IN_MANT_WIDTH >= OUT_MANT_WIDTH)
            else $error("IN_MANT_WIDTH must be greater than or equal to OUT_MANT_WIDTH");
    end

    logic [OUT_EXP_WIDTH + IN_MANT_WIDTH : 0] intermediate_data;

    fp_ieee_exponent_casting #(
        .IN_EXP_WIDTH(IN_EXP_WIDTH),
        .OUT_EXP_WIDTH(OUT_EXP_WIDTH),
        .MANT_WIDTH(IN_MANT_WIDTH)
    ) fp_ieee_exponent_casting_inst (
        .data_in(data_in),
        .data_out(intermediate_data)
    );

    fp_ieee_mantissa_casting #(
        .EXP_WIDTH(OUT_EXP_WIDTH),
        .IN_MANT_WIDTH(IN_MANT_WIDTH),
        .OUT_MANT_WIDTH(OUT_MANT_WIDTH)
    ) fp_ieee_mantissa_casting_inst (
        .data_in(intermediate_data),
        .data_out(data_out)
    );
endmodule

