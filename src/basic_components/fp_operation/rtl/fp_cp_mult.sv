`timescale 1ns / 1ps
/*
Module      : Floating Point Configurable Precision Adder (With Sign)
Timing      : Combinatorial Logic
Description : Adds two FP numbers with different exponents and signs.
              Aligns mantissas, preserves full precision (no bits discarded).
              Output format: {sign, exp_out, mant_out}.
              No rounding.
              It needs normalisation.
              The lossy part will be at the mantissa adder
Status      : Passed Simple Tests
*/

module fp_cp_mult #(
    parameter int EXP_WIDTH = 6,
    parameter int MANT_WIDTH = 5,
    // Amount of bits needed to shift mantissas for alignment
    parameter int EXT_MANT_WIDTH = 0,
    // Need to increase exp width by 1 to handle overflow
    parameter int EXT_EXP_WIDTH = 0
)(
    input  logic clk,
    input  logic rst,
    input  logic data_in_valid,
    output logic data_in_ready,
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_a,  // {sign, exp, mant}
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_b,
    output logic [EXP_WIDTH + EXT_EXP_WIDTH + MANT_WIDTH + EXT_MANT_WIDTH : 0] data_out,
    output logic data_out_valid,
    input  logic data_out_ready
);

    localparam int IN_EXP_WIDTH = EXP_WIDTH;
    localparam int IN_FIXED_WIDTH = MANT_WIDTH + 2;
    localparam int IN_FIXED_FRAC_WIDTH = MANT_WIDTH;

    localparam int MULT_OUT_EXP_WIDTH = IN_EXP_WIDTH + 1;
    localparam int MULT_OUT_FIXED_FRAC_WIDTH = IN_FIXED_FRAC_WIDTH + IN_FIXED_FRAC_WIDTH;
    localparam int MULT_OUT_FIXED_WIDTH = 1 + 2*(IN_FIXED_WIDTH - IN_FIXED_FRAC_WIDTH - 1) + MULT_OUT_FIXED_FRAC_WIDTH;

    localparam int NORMALIZE_OUT_EXP_WIDTH = MULT_OUT_EXP_WIDTH + 1;
    localparam int NORMALIZE_OUT_MANT_WIDTH = MULT_OUT_FIXED_WIDTH - 1;

    // Internal signal declarations
    logic signed [IN_EXP_WIDTH - 1:0]   signed_exp_a, signed_exp_b;
    logic signed [IN_FIXED_WIDTH - 1:0] signed_mant_a, signed_mant_b;
    logic signed [MULT_OUT_EXP_WIDTH - 1:0] signed_exp_out;
    logic signed [MULT_OUT_FIXED_WIDTH - 1:0] signed_mant_out;
    logic signed [NORMALIZE_OUT_EXP_WIDTH + NORMALIZE_OUT_MANT_WIDTH:0] normalized_data;

    logic signed [MULT_OUT_EXP_WIDTH - 1:0] reg_signed_exp_out;
    logic signed [MULT_OUT_FIXED_WIDTH - 1:0] reg_signed_mant_out;
    logic reg_mult_out_valid, reg_mult_out_ready;

    // Instantiate fp_ieee_partition for data_a
    fp_ieee_partition #(
        .EXP_WIDTH(EXP_WIDTH),
        .MANT_WIDTH(MANT_WIDTH)
    ) partition_a (
        .data_in(data_a),
        .signed_exp(signed_exp_a),
        .signed_mant(signed_mant_a)
    );


    // Instantiate fp_ieee_partition for data_b
    fp_ieee_partition #(
        .EXP_WIDTH(EXP_WIDTH),
        .MANT_WIDTH(MANT_WIDTH)
    ) partition_b (
        .data_in(data_b),
        .signed_exp(signed_exp_b),
        .signed_mant(signed_mant_b)
    );

    // Instantiate fp_mult
    fp_mult #(
        .IN_EXP_WIDTH(IN_EXP_WIDTH),
        .IN_FIX_WIDTH(IN_FIXED_WIDTH),
        .IN_FIX_FRAC_WIDTH(IN_FIXED_FRAC_WIDTH),
        .OUT_FIX_FRAC_WIDTH(MULT_OUT_FIXED_FRAC_WIDTH)
    ) fp_mult_inst (
        .exp_a(signed_exp_a),
        .mant_a(signed_mant_a),
        .exp_b(signed_exp_b),
        .mant_b(signed_mant_b),
        .exp_out(signed_exp_out),
        .mant_out(signed_mant_out)
    );
    register_slice #(
        .DATA_WIDTH(MULT_OUT_EXP_WIDTH + MULT_OUT_FIXED_WIDTH)
    ) register_slice_inst (
        .clk(clk),
        .rst(rst),
        .data_in({signed_exp_out, signed_mant_out}),
        .data_in_valid(data_in_valid),
        .data_in_ready(data_in_ready),
        .data_out({reg_signed_exp_out, reg_signed_mant_out}),
        .data_out_valid(reg_mult_out_valid),
        .data_out_ready(reg_mult_out_ready)
    );
    // Instantiate fp_ieee_normalize for output
    fp_ieee_normalize #(
        .IN_FIXED_WIDTH(MULT_OUT_FIXED_WIDTH),
        .IN_FIXED_FRAC_WIDTH(MULT_OUT_FIXED_FRAC_WIDTH),
        .IN_EXP_WIDTH(MULT_OUT_EXP_WIDTH),
        .OUT_MANT_WIDTH(NORMALIZE_OUT_MANT_WIDTH)
    ) fp_normalize (
        .signed_mant(reg_signed_mant_out),
        .signed_exp(reg_signed_exp_out),
        .fp_out(normalized_data)
    );

    fp_ieee_casting #(
        .IN_EXP_WIDTH(NORMALIZE_OUT_EXP_WIDTH),
        .IN_MANT_WIDTH(NORMALIZE_OUT_MANT_WIDTH),
        .OUT_EXP_WIDTH(EXP_WIDTH + EXT_EXP_WIDTH),
        .OUT_MANT_WIDTH(MANT_WIDTH + EXT_MANT_WIDTH)
    ) fp_casting (
        .clk(clk),
        .rst(rst),
        .data_in(normalized_data),
        .data_in_valid(reg_mult_out_valid),
        .data_in_ready(reg_mult_out_ready),
        .data_out(data_out),
        .data_out_valid(data_out_valid),
        .data_out_ready(data_out_ready)
    );




endmodule
