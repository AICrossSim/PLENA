
`timescale 1ns / 1ps
/*
Module      : fp_hash_reciprocal
Timing      : Combinatorial Logic
Description : FP_Hash_Reciprocal
            - Performs hash operation on the reciprocal of the input floating-point number.
*/
module fp_hash_reciprocal #(
    parameter int IN_EXP_WIDTH = 5,
    parameter int IN_MANT_WIDTH = 10,
    // Amount of bits needed to shift mantissas for alignment
    parameter int OUT_EXP_WIDTH = -1,
    parameter int OUT_MANT_WIDTH = -1
)(
    input  logic signed [IN_EXP_WIDTH + IN_MANT_WIDTH:0] data_in,
    output logic signed [OUT_EXP_WIDTH + OUT_MANT_WIDTH:0] data_out
);

    reciprocal_lut #(
        .IN_ENTRY_WIDTH(IN_EXP_WIDTH + IN_MANT_WIDTH + 1),
        .OUT_ENTRY_WIDTH(OUT_EXP_WIDTH + OUT_MANT_WIDTH + 1)
    ) reciprocal_lut_inst (
        .data_in(data_in),
        .data_out(data_out)
    );

endmodule