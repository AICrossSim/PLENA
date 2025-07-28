
`timescale 1ns / 1ps
/*
Module      : fp_hash_exp
Timing      : Combinatorial Logic
Description : FP_Hash_Exp
            - Performs hash operation on the exponent of the input floating-point number.
*/
module fp_hash_exp #(
    parameter int IN_EXP_WIDTH = 6,
    parameter int IN_MANT_WIDTH = 5,
    // Amount of bits needed to shift mantissas for alignment
    parameter int OUT_EXP_WIDTH = 6,
    parameter int OUT_MANT_WIDTH = 5
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