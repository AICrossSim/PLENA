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
    parameter   OUT_MANT_WIDTH = 10
)(
    input  logic clk,
    input  logic rst,
    input  logic data_in_valid,
    output logic data_in_ready,
    input  logic [IN_EXP_WIDTH + IN_MANT_WIDTH : 0] data_in,  // {sign, exp, mant}
    output logic data_out_valid,
    input  logic data_out_ready,
    output logic [OUT_EXP_WIDTH + OUT_MANT_WIDTH : 0] data_out
);

    localparam int IN_FIXED_WIDTH = IN_MANT_WIDTH + 2;
    localparam int IN_FIXED_FRAC_WIDTH = IN_MANT_WIDTH;

    localparam int RECIP_OUT_EXP_WIDTH = OUT_EXP_WIDTH + 1;
    localparam int RECIP_OUT_FIXED_WIDTH = OUT_MANT_WIDTH + 2;
    localparam int NORMALIZE_OUT_MANT_WIDTH = RECIP_OUT_FIXED_WIDTH - 1;
    
    localparam NORM_DATA_WIDTH = RECIP_OUT_EXP_WIDTH + NORMALIZE_OUT_MANT_WIDTH + 1;
    logic [NORM_DATA_WIDTH - 1:0] normalized_data;
    
    // Signal declarations for connecting the modules
    logic signed [IN_EXP_WIDTH - 1:0]       signed_exp_in;
    logic signed [IN_MANT_WIDTH + 2 - 1:0]  signed_mant_in;
    logic signed [IN_EXP_WIDTH - 1:0]       p1_signed_exp_in;
    logic signed [IN_MANT_WIDTH + 2 - 1:0]  p1_signed_mant_in;
    logic p1_partition_valid, p1_partition_ready;

    logic signed [OUT_EXP_WIDTH - 1:0]      reciprocal_exp_out;
    logic signed [OUT_MANT_WIDTH + 2 - 1:0] reciprocal_mant_out;
    logic signed [OUT_EXP_WIDTH - 1:0]      p2_signed_reciprocal_exp_out;
    logic signed [OUT_MANT_WIDTH + 2 - 1:0] p2_signed_reciprocal_mant_out;
    logic p2_reciprocal_valid, p2_reciprocal_ready;
    logic p3_reciprocal_valid, p3_reciprocal_ready;

    logic [OUT_EXP_WIDTH + OUT_MANT_WIDTH : 0] casted_data;
    
    fp_ieee_partition #(
        .EXP_WIDTH(IN_EXP_WIDTH),
        .MANT_WIDTH(IN_MANT_WIDTH)
    ) partition_init (
        .data_in        (data_in),
        .signed_exp     (signed_exp_in),
        .signed_mant    (signed_mant_in)
    );

    skid_buffer #(
        .DATA_WIDTH(IN_EXP_WIDTH + IN_MANT_WIDTH + 2)
    ) buffer_partition (
        .clk(clk),
        .rst(rst),
        .data_in({signed_exp_in, signed_mant_in}),
        .data_in_valid(data_in_valid),
        .data_in_ready(data_in_ready),
        .data_out({p1_signed_exp_in, p1_signed_mant_in}),
        .data_out_valid(p1_partition_valid),
        .data_out_ready(p1_partition_ready)
    );

    fp_reciprocal #(
        .IN_EXP_WIDTH       (IN_EXP_WIDTH),
        .IN_FIX_WIDTH       (IN_MANT_WIDTH + 2),
        .IN_FIX_FRAC_WIDTH  (IN_MANT_WIDTH),
        .OUT_EXP_WIDTH      (OUT_EXP_WIDTH),
        .OUT_FIX_WIDTH      (OUT_MANT_WIDTH + 2),
        .OUT_FIX_FRAC_WIDTH (OUT_MANT_WIDTH)
    ) fp_reciprocal_inst (
        .clk(clk),
        .rst(rst),
        .data_in_valid      (p1_partition_valid),
        .data_in_ready      (p1_partition_ready),
        .signed_exp_in      (p1_signed_exp_in),
        .signed_mant_in     (p1_signed_mant_in),
        .data_out_valid     (p2_reciprocal_valid),
        .data_out_ready     (p2_reciprocal_ready),
        .signed_exp_out     (reciprocal_exp_out),
        .signed_mant_out    (reciprocal_mant_out)
    );

    skid_buffer #(
        .DATA_WIDTH(OUT_EXP_WIDTH + OUT_MANT_WIDTH + 2)
    ) buffer_reciprocal (
        .clk(clk),
        .rst(rst),
        .data_in        ({reciprocal_exp_out, reciprocal_mant_out}),
        .data_in_valid  (p2_reciprocal_valid),
        .data_in_ready  (p2_reciprocal_ready),
        .data_out       ({p2_signed_reciprocal_exp_out, p2_signed_reciprocal_mant_out}),
        .data_out_valid (p3_reciprocal_valid),
        .data_out_ready (p3_reciprocal_ready)
    );

    fp_ieee_normalize #(
        .IN_FIXED_WIDTH(RECIP_OUT_FIXED_WIDTH),
        .IN_FIXED_FRAC_WIDTH(OUT_MANT_WIDTH),
        .IN_EXP_WIDTH(OUT_EXP_WIDTH),
        .OUT_MANT_WIDTH(NORMALIZE_OUT_MANT_WIDTH)
    ) fp_normalize (
        .signed_mant    (p2_signed_reciprocal_mant_out),
        .signed_exp     (p2_signed_reciprocal_exp_out),
        .fp_out(normalized_data)
    );

    fp_ieee_casting #(
        .IN_EXP_WIDTH(RECIP_OUT_EXP_WIDTH),
        .IN_MANT_WIDTH(NORMALIZE_OUT_MANT_WIDTH),
        .OUT_EXP_WIDTH(OUT_EXP_WIDTH),
        .OUT_MANT_WIDTH(OUT_MANT_WIDTH)
    ) fp_casting (
        .data_in(normalized_data),
        .data_out(casted_data)
    );

    skid_buffer #(
        .DATA_WIDTH(OUT_EXP_WIDTH + OUT_MANT_WIDTH + 1)
    ) buffer_normalise_cast (
        .clk(clk),
        .rst(rst),
        .data_in(casted_data),
        .data_in_valid(p3_reciprocal_valid),
        .data_in_ready(p3_reciprocal_ready),
        .data_out(data_out),
        .data_out_valid(data_out_valid),
        .data_out_ready(data_out_ready)
    );

endmodule
