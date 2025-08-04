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

    DW_fp_add #(MANT_WIDTH, EXP_WIDTH, 1)
        U1 ( .a(data_in), .b(data_out), .rnd(3'b000), .z(partial_sum), .status() );

endmodule
