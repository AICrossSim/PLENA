`timescale 1ns / 1ps
// `include "operation.svh"

/*
Module      : Vector Exp
Timing      : Combinatorial Logic
Description : This module includes elementwise vector computations 
            : 4. Elementwise Exponential
Status      : Under Development
*/

module fp_cp_exp #(
    parameter   IN_EXP_WIDTH = 5,
    parameter   IN_MANT_WIDTH = 10,
    parameter   OUT_EXP_WIDTH = 5,
    parameter   OUT_MANT_WIDTH = 10
)(
    input  logic clk,
    input  logic rst,
    input  logic [IN_EXP_WIDTH + IN_MANT_WIDTH : 0] data_in,  // {sign, exp, mant}
    input  logic data_in_valid,
    output logic [OUT_EXP_WIDTH + OUT_MANT_WIDTH : 0] data_out,
    output logic data_out_valid
);

    localparam int EXTEND_WIDTH = 5;
    localparam int IN_FIXED_WIDTH = IN_MANT_WIDTH + 2;
    localparam int IN_FIXED_FRAC_WIDTH = IN_MANT_WIDTH;

    localparam int EXP_IN_EXP_WIDTH = IN_EXP_WIDTH;
    localparam int EXP_IN_FIXED_WIDTH = IN_MANT_WIDTH + 2;
    localparam int EXP_IN_FIXED_FRAC_WIDTH = IN_MANT_WIDTH;

    localparam int EXP_OUT_EXP_WIDTH = OUT_EXP_WIDTH;
    localparam int EXP_OUT_FIXED_FRAC_WIDTH = IN_MANT_WIDTH;
    localparam int EXP_OUT_FIXED_WIDTH = EXP_OUT_FIXED_FRAC_WIDTH + 3;
    localparam int NORMALIZE_OUT_MANT_WIDTH = EXP_OUT_FIXED_WIDTH - 1;
    localparam int NORMALIZE_OUT_EXP_WIDTH = EXP_OUT_EXP_WIDTH + 1;
    
    localparam NORM_DATA_WIDTH = NORMALIZE_OUT_EXP_WIDTH + NORMALIZE_OUT_MANT_WIDTH + 1;
    logic [NORM_DATA_WIDTH - 1:0] normalized_data;
    
    // Signal declarations for connecting the modules
    logic signed [IN_EXP_WIDTH - 1:0] signed_exp_in;
    logic signed [IN_MANT_WIDTH + 2 - 1:0] signed_mant_in;
    logic signed [EXP_OUT_EXP_WIDTH - 1:0] exp_out_exp;
    logic signed [EXP_OUT_FIXED_WIDTH - 1:0] exp_out_mant;
    
    fp_ieee_partition #(
        .EXP_WIDTH(IN_EXP_WIDTH),
        .MANT_WIDTH(IN_MANT_WIDTH)
    ) partition_a (
        .data_in(data_in),
        .signed_exp(signed_exp_in),
        .signed_mant(signed_mant_in)
    );

    fp_exp #(
        .IN_EXP_WIDTH(EXP_IN_EXP_WIDTH),
        .IN_FIX_WIDTH(EXP_IN_FIXED_WIDTH),
        .IN_FIX_FRAC_WIDTH(EXP_IN_FIXED_FRAC_WIDTH),
        .EXTEND_WIDTH(EXTEND_WIDTH),
        .OUT_EXP_WIDTH(EXP_OUT_EXP_WIDTH),
        .OUT_FIX_WIDTH(EXP_OUT_FIXED_WIDTH),
        .OUT_FIX_FRAC_WIDTH(EXP_OUT_FIXED_FRAC_WIDTH)
    ) fp_exp_inst (
        .signed_exp_in(signed_exp_in),
        .signed_mant_in(signed_mant_in),
        .signed_exp_out(exp_out_exp),
        .signed_mant_out(exp_out_mant)
    );

    fp_ieee_normalize #(
        .IN_FIXED_WIDTH(EXP_OUT_FIXED_WIDTH),
        .IN_FIXED_FRAC_WIDTH(EXP_OUT_FIXED_FRAC_WIDTH),
        .IN_EXP_WIDTH(EXP_OUT_EXP_WIDTH),
        .OUT_MANT_WIDTH(NORMALIZE_OUT_MANT_WIDTH)
    ) fp_normalize (
        .signed_mant(exp_out_mant),
        .signed_exp(exp_out_exp),
        .fp_out(normalized_data)
    );

    fp_ieee_casting #(
        .IN_EXP_WIDTH(NORMALIZE_OUT_EXP_WIDTH),
        .IN_MANT_WIDTH(NORMALIZE_OUT_MANT_WIDTH),
        .OUT_EXP_WIDTH(OUT_EXP_WIDTH),
        .OUT_MANT_WIDTH(OUT_MANT_WIDTH)
    ) fp_casting (
        .data_in(normalized_data),
        .data_out(data_out)
    );
endmodule


