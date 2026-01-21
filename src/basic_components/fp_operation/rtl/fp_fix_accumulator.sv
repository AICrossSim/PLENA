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

module fp_fix_accumulator #(
    parameter int EXP_WIDTH = 5,
    parameter int MANT_WIDTH = 10
)(
    input  logic clk,
    input  logic rst,
    input  logic clear_accumulator,
    input  logic data_in_valid,
    output logic data_in_ready,
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_in,  // {sign, exp, mant}
    output logic [EXP_WIDTH + MANT_WIDTH : 0] data_out,
    output logic data_out_valid,
    input  logic data_out_ready
);

  logic [EXP_WIDTH + MANT_WIDTH : 0] partial_sum;
  /* verilator lint_off WIDTH */
  assign data_in_ready = data_out_ready;
  assign data_out_valid  = 1'b1;
  /* verilator lint_on WIDTH */

  // data_out
  always_ff @(posedge clk)
    if (rst || clear_accumulator) data_out <= '0;
    else if (data_in_valid && data_in_ready) data_out <= partial_sum;

`ifdef DC_LIB_EN
    DW_fp_add #(MANT_WIDTH, EXP_WIDTH, 1)
        U1 ( .a(data_in), .b(data_out), .rnd(3'b000), .z(partial_sum), .status() );
`else
    // Generic implementation (Combinational)
    localparam int IN_FIXED_WIDTH = MANT_WIDTH + 2;
    localparam int IN_FIXED_FRAC_WIDTH = MANT_WIDTH;
    localparam int ADDER_OUT_EXP_WIDTH = EXP_WIDTH;
    localparam int ADDER_OUT_FIXED_WIDTH = IN_FIXED_WIDTH + IN_FIXED_FRAC_WIDTH + 1;
    localparam int ADDER_OUT_FIXED_FRAC_WIDTH = 2 * IN_FIXED_FRAC_WIDTH;
    localparam int NORMALIZE_OUT_EXP_WIDTH = ADDER_OUT_EXP_WIDTH + 1;
    localparam int NORMALIZE_OUT_MANT_WIDTH = ADDER_OUT_FIXED_WIDTH - 1;

    logic signed [EXP_WIDTH - 1:0]   signed_exp_a, signed_exp_b;
    logic signed [IN_FIXED_WIDTH - 1:0] signed_mant_a, signed_mant_b;
    logic signed [ADDER_OUT_EXP_WIDTH - 1:0]    signed_exp_out;
    logic signed [ADDER_OUT_FIXED_WIDTH - 1:0]  signed_mant_out;
    logic [NORMALIZE_OUT_EXP_WIDTH + NORMALIZE_OUT_MANT_WIDTH: 0] normalized_data;
    logic [EXP_WIDTH + NORMALIZE_OUT_MANT_WIDTH : 0] exp_casted_data;

    fp_ieee_partition #(.EXP_WIDTH(EXP_WIDTH), .MANT_WIDTH(MANT_WIDTH)) part_a (.data_in(data_in), .signed_exp(signed_exp_a), .signed_mant(signed_mant_a));
    fp_ieee_partition #(.EXP_WIDTH(EXP_WIDTH), .MANT_WIDTH(MANT_WIDTH)) part_b (.data_in(data_out), .signed_exp(signed_exp_b), .signed_mant(signed_mant_b));

    fp_adder #(.IN_EXP_WIDTH(EXP_WIDTH), .IN_FIX_WIDTH(IN_FIXED_WIDTH), .IN_FIX_FRAC_WIDTH(IN_FIXED_FRAC_WIDTH),
        .OUT_EXP_WIDTH(ADDER_OUT_EXP_WIDTH), .OUT_FIX_WIDTH(ADDER_OUT_FIXED_WIDTH), .OUT_FIX_FRAC_WIDTH(ADDER_OUT_FIXED_FRAC_WIDTH)) fp_adder_inst (
        .exp_a(signed_exp_a), .mant_a(signed_mant_a), .exp_b(signed_exp_b), .mant_b(signed_mant_b),
        .exp_out(signed_exp_out), .mant_out(signed_mant_out));

    fp_ieee_normalize #(.IN_FIXED_WIDTH(ADDER_OUT_FIXED_WIDTH), .IN_FIXED_FRAC_WIDTH(ADDER_OUT_FIXED_FRAC_WIDTH),
        .IN_EXP_WIDTH(ADDER_OUT_EXP_WIDTH), .OUT_MANT_WIDTH(NORMALIZE_OUT_MANT_WIDTH)) fp_normalize (
        .signed_mant(signed_mant_out), .signed_exp(signed_exp_out), .fp_out(normalized_data));

    fp_ieee_exponent_casting #(.IN_EXP_WIDTH(NORMALIZE_OUT_EXP_WIDTH), .OUT_EXP_WIDTH(EXP_WIDTH), .MANT_WIDTH(NORMALIZE_OUT_MANT_WIDTH)) exp_cast (
        .data_in(normalized_data), .data_out(exp_casted_data));

    fp_ieee_mantissa_casting #(.EXP_WIDTH(EXP_WIDTH), .IN_MANT_WIDTH(NORMALIZE_OUT_MANT_WIDTH), .OUT_MANT_WIDTH(MANT_WIDTH)) mant_cast (
        .data_in(exp_casted_data), .data_out(partial_sum));
`endif

endmodule
