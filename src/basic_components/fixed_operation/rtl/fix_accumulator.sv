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

module fix_accumulator #(
    parameter int WIDTH = 16,
    parameter int EXPAND_WIDTH = 0
)(
    input  logic clk,
    input  logic rst,
    input  logic clear_accumulator,
    input  logic data_in_valid,
    output logic data_in_ready,
    input  logic [WIDTH - 1 : 0] data_in,
    output logic [WIDTH+EXPAND_WIDTH - 1 : 0] data_out,
    output logic data_out_valid,
    input  logic data_out_ready
);


  logic [WIDTH+EXPAND_WIDTH - 1 : 0] partial_sum;
  /* verilator lint_off WIDTH */
  assign data_in_ready = data_out_ready;
  assign data_out_valid  = 1'b1;
  /* verilator lint_on WIDTH */

  // data_out
  always_ff @(posedge clk)
    if (rst || clear_accumulator) data_out <= '0;
    else if (data_in_valid && data_in_ready) data_out <= partial_sum;

    assign partial_sum = $signed(data_in) + $signed(data_out);


endmodule
