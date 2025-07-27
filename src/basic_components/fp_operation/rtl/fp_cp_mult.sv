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
    parameter int EXP_WIDTH = 5,
    parameter int MANT_WIDTH = 10,
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
    logic signed [IN_EXP_WIDTH - 1:0]   p1_signed_exp_a, p1_signed_exp_b;
    logic signed [IN_FIXED_WIDTH - 1:0] p1_signed_mant_a, p1_signed_mant_b;
    logic partition_a_valid, partition_a_ready;
    logic partition_b_valid, partition_b_ready;

    logic signed [MULT_OUT_EXP_WIDTH - 1:0] signed_exp_out;
    logic signed [MULT_OUT_FIXED_WIDTH - 1:0] signed_mant_out;

    logic signed [MULT_OUT_EXP_WIDTH - 1:0]     p2_signed_exp_out;
    logic signed [MULT_OUT_FIXED_WIDTH - 1:0]   p2_signed_mant_out;

    logic p1_mult_ready, p1_mult_valid;
    logic p2_mult_ready, p2_mult_valid;

    logic signed [NORMALIZE_OUT_EXP_WIDTH + NORMALIZE_OUT_MANT_WIDTH:0] normalized_data;
    logic [EXP_WIDTH + EXT_EXP_WIDTH + MANT_WIDTH + EXT_MANT_WIDTH : 0] casted_data;

    split_n #(
        .N(2)
    ) split_mult_signal (
        .data_in_valid(data_in_valid),
        .data_in_ready(data_in_ready),
        .data_out_valid({partition_a_valid, partition_b_valid}),
        .data_out_ready({partition_a_ready, partition_b_ready})
    );

    // Instantiate fp_ieee_partition for data_a
    fp_ieee_partition #(
        .EXP_WIDTH(EXP_WIDTH),
        .MANT_WIDTH(MANT_WIDTH)
    ) partition_a (
        .data_in(data_a),
        .signed_exp(signed_exp_a),
        .signed_mant(signed_mant_a)
    );

    register_slice #(
        .DATA_WIDTH(IN_EXP_WIDTH + IN_FIXED_WIDTH)
    ) buffer_partition_a (
        .clk(clk),
        .rst(rst),
        .data_in({signed_exp_a, signed_mant_a}),
        .data_in_valid(partition_a_valid),
        .data_in_ready(partition_a_ready),
        .data_out({p1_signed_exp_a, p1_signed_mant_a}),
        .data_out_valid(p1_partition_a_valid),
        .data_out_ready(p1_partition_a_ready)
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

    register_slice #(
        .DATA_WIDTH(IN_EXP_WIDTH + IN_FIXED_WIDTH)
    ) buffer_partition_b (
        .clk(clk),
        .rst(rst),
        .data_in({signed_exp_b, signed_mant_b}),
        .data_in_valid(partition_b_valid),
        .data_in_ready(partition_b_ready),
        .data_out({p1_signed_exp_b, p1_signed_mant_b}),
        .data_out_valid(p1_partition_b_valid),
        .data_out_ready(p1_partition_b_ready)
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

    join2 #() join_mult_result (
        .data_in_valid({p1_partition_a_valid, p1_partition_b_valid}),
        .data_in_ready({p1_partition_a_ready, p1_partition_b_ready}),
        .data_out_valid(p1_mult_valid),
        .data_out_ready(p1_mult_ready)
    );

    register_slice #(
        .DATA_WIDTH(MULT_OUT_EXP_WIDTH + MULT_OUT_FIXED_WIDTH)
    ) buffer_mult (
        .clk(clk),
        .rst(rst),
        .data_in({signed_exp_out, signed_mant_out}),
        .data_in_valid(p1_mult_valid),
        .data_in_ready(p1_mult_ready),
        .data_out({p2_signed_exp_out, p2_signed_mant_out}),
        .data_out_valid(p2_mult_valid),
        .data_out_ready(p2_mult_ready)
    );

    // Instantiate fp_ieee_normalize for output
    fp_ieee_normalize #(
        .IN_FIXED_WIDTH(MULT_OUT_FIXED_WIDTH),
        .IN_FIXED_FRAC_WIDTH(MULT_OUT_FIXED_FRAC_WIDTH),
        .IN_EXP_WIDTH(MULT_OUT_EXP_WIDTH),
        .OUT_MANT_WIDTH(NORMALIZE_OUT_MANT_WIDTH)
    ) fp_normalize (
        .signed_mant(signed_mant_out),
        .signed_exp(signed_exp_out),
        .fp_out(normalized_data)
    );

    fp_ieee_casting #(
        .IN_EXP_WIDTH(NORMALIZE_OUT_EXP_WIDTH),
        .IN_MANT_WIDTH(NORMALIZE_OUT_MANT_WIDTH),
        .OUT_EXP_WIDTH(EXP_WIDTH + EXT_EXP_WIDTH),
        .OUT_MANT_WIDTH(MANT_WIDTH + EXT_MANT_WIDTH)
    ) fp_casting (
        .data_in(normalized_data),
        .data_out(casted_data)
    );

    register_slice #(
        .DATA_WIDTH(EXP_WIDTH + EXT_EXP_WIDTH + MANT_WIDTH + EXT_MANT_WIDTH + 1)
    ) buffer_normalise_cast (
        .clk(clk),
        .rst(rst),
        .data_in(casted_data),
        .data_in_valid(p2_mult_valid),
        .data_in_ready(p2_mult_ready),
        .data_out(data_out),
        .data_out_valid(data_out_valid),
        .data_out_ready(data_out_ready)
    );


endmodule
