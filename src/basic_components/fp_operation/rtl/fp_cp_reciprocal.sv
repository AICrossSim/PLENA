`timescale 1ns / 1ps
// `include "operation.svh"

/*
Module      : Vector Exp
Timing      : Combinatorial Logic
Description : This module includes elementwise vector computations 
            : 4. Elementwise Exponential
Status      : Under Development
*/

module fp_cp_reciprocal #(
    parameter   IN_EXP_WIDTH = 5,
    parameter   IN_MANT_WIDTH = 10,
    parameter   OUT_EXP_WIDTH = 5,
    parameter   OUT_MANT_WIDTH = 10,
    parameter   IEEE_COMPLIANCE = 0,
    parameter   FAITHFUL_ROUNDING = 0
)(
    input  logic clk,
    input  logic rst,
    input  logic [IN_EXP_WIDTH + IN_MANT_WIDTH : 0] data_in,  // {sign, exp, mant}
    input  logic data_in_valid,
    output  logic data_in_ready,

    output logic [OUT_EXP_WIDTH + OUT_MANT_WIDTH : 0] data_out,
    output logic data_out_valid,
    input logic data_out_ready
);

    localparam int IN_FIXED_WIDTH = IN_MANT_WIDTH + 2;
    localparam int IN_FIXED_FRAC_WIDTH = IN_MANT_WIDTH;

    localparam int RECIP_OUT_EXP_WIDTH = OUT_EXP_WIDTH + 1;
    localparam int RECIP_OUT_FIXED_WIDTH = OUT_MANT_WIDTH + 2;
    localparam int NORMALIZE_OUT_MANT_WIDTH = RECIP_OUT_FIXED_WIDTH - 1;
    
    localparam NORM_DATA_WIDTH = RECIP_OUT_EXP_WIDTH + NORMALIZE_OUT_MANT_WIDTH + 1;
    logic [NORM_DATA_WIDTH - 1:0] normalized_data;
    
    // Signal declarations for connecting the modules
    logic signed [IN_EXP_WIDTH - 1:0] signed_exp_in;
    logic signed [IN_MANT_WIDTH + 2 - 1:0] signed_mant_in;
    logic signed [OUT_EXP_WIDTH - 1:0] reciprocal_exp_out;
    logic signed [OUT_MANT_WIDTH + 2 - 1:0] reciprocal_mant_out;


    
    fp_ieee_partition #(
        .EXP_WIDTH(IN_EXP_WIDTH),
        .MANT_WIDTH(IN_MANT_WIDTH)
    ) partition_a (
        .data_in(data_in),
        .signed_exp(signed_exp_in),
        .signed_mant(signed_mant_in)
    );
    fp_reciprocal #(
        .IN_EXP_WIDTH(IN_EXP_WIDTH),
        .IN_FIX_WIDTH(IN_MANT_WIDTH + 2),
        .IN_FIX_FRAC_WIDTH(IN_MANT_WIDTH),
        .OUT_EXP_WIDTH(OUT_EXP_WIDTH),
        .OUT_FIX_WIDTH(OUT_MANT_WIDTH + 2),
        .OUT_FIX_FRAC_WIDTH(OUT_MANT_WIDTH)
    ) fp_reciprocal_inst (
        .clk(clk),
        .rst(rst),
        .data_in_valid(data_in_valid),
        .data_in_ready(data_in_ready),
        .data_out_ready(data_out_ready),
        .data_out_valid(data_out_valid),
        .signed_exp_in(signed_exp_in),
        .signed_mant_in(signed_mant_in),
        .signed_exp_out(reciprocal_exp_out),
        .signed_mant_out(reciprocal_mant_out)
    );

    fp_ieee_normalize #(
        .IN_FIXED_WIDTH(RECIP_OUT_FIXED_WIDTH),
        .IN_FIXED_FRAC_WIDTH(OUT_MANT_WIDTH),
        .IN_EXP_WIDTH(OUT_EXP_WIDTH),
        .OUT_MANT_WIDTH(NORMALIZE_OUT_MANT_WIDTH)
    ) fp_normalize (
        .signed_mant(reciprocal_mant_out),
        .signed_exp(reciprocal_exp_out),
        .fp_out(normalized_data)
    );

    fp_ieee_casting #(
        .IN_EXP_WIDTH(RECIP_OUT_EXP_WIDTH),
        .IN_MANT_WIDTH(NORMALIZE_OUT_MANT_WIDTH),
        .OUT_EXP_WIDTH(OUT_EXP_WIDTH),
        .OUT_MANT_WIDTH(OUT_MANT_WIDTH)
    ) fp_casting (
        .data_in(normalized_data),
        .data_out(data_out)
    );

endmodule
