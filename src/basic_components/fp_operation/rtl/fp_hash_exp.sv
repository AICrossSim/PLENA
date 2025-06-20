
`timescale 1ns / 1ps
/*
Module      : fp_ieee_casting
Timing      : Combinatorial Logic
Description : FP_IEEE_Casting
            - Performs casting between IEEE floating-point formats.
            - Only **reducing** bit width is allowed.
            - This operation is **lossy**: For instance, to cast a value like xxxx to x000, we **first truncate/floor** to xxx0, then apply **round-to-nearest-even**.
*/
module fp_hash_exp #(
    parameter int IN_EXP_WIDTH = 5,
    parameter int IN_MANT_WIDTH = 10,
    // Amount of bits needed to shift mantissas for alignment
    parameter int OUT_EXP_WIDTH = -1,
    parameter int OUT_MANT_WIDTH = -1
)(
    input  logic signed [IN_EXP_WIDTH + IN_MANT_WIDTH:0] data_in,
    output logic signed [OUT_EXP_WIDTH + OUT_MANT_WIDTH:0] data_out
);

    exp_lut #(
        .IN_ENTRY_WIDTH(IN_EXP_WIDTH + IN_MANT_WIDTH + 1),
        .OUT_ENTRY_WIDTH(OUT_EXP_WIDTH + OUT_MANT_WIDTH + 1)
    ) exp_lut_inst (
        .data_in(data_in),
        .data_out(data_out)
    );

endmodule