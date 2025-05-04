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
    parameter   EXP_WIDTH = 5,
    parameter   MANT_WIDTH = 10
)(
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_in,  // {sign, exp, mant}
    output logic [EXP_WIDTH + MANT_WIDTH : 0] data_out
);
  logic sign_bit;
  logic [EXP_WIDTH - 1:0] exp_bit;
  logic [MANT_WIDTH - 1:0] mant_bit;

  logic [EXP_WIDTH - 1:0] reverse_exp_bit;

  logic [MANT_WIDTH:0] normalized_reciprocal_mant;

  localparam BIAS = (1 << (EXP_WIDTH - 1)) - 1;
  assign sign_bit = data_in[EXP_WIDTH + MANT_WIDTH];
  assign exp_bit = data_in[EXP_WIDTH + MANT_WIDTH - 1:MANT_WIDTH];
  assign mant_bit = data_in[MANT_WIDTH - 1:0];

  // we have reverse_exp_bit + real_exp_bit = -(exp_bit - bias) + bias = -exp_bit + 2*bias
  assign reverse_exp_bit = 2*BIAS - exp_bit;

  logic [MANT_WIDTH - 1:0] reciprocal_mant;
  logic [MANT_WIDTH:0] denormalized_mant;

  assign denormalized_mant = (exp_bit != 0) ? (1 << (MANT_WIDTH) + mant_bit) : mant_bit;

  // TODO:Do we need to round the reciprocal_mant?
  // Currently, denormalized_mant = * /2^(MANT_WIDTH)
  // the target reciporcal mant I want is * /2^(MANT_WIDTH) not round currently
  // So the divisor should be 1 << (MANT_WIDTH + 1 + MANT_WIDTH)
  assign reciprocal_mant = (1<<(MANT_WIDTH + MANT_WIDTH)) / denormalized_mant;

  assign unnormalized_fp = {sign_bit, reverse_exp_bit, reciprocal_mant};

  fp_normalize #(
    .EXP_WIDTH(EXP_WIDTH),
    .MANT_WIDTH(MANT_WIDTH)
  ) fp_normalize_inst (
    .data_in(unnormalized_fp),
    .data_out(data_out)
  );
endmodule

module fp_normalize #(
    parameter   EXP_WIDTH = 5,
    parameter   MANT_WIDTH = 10
)(
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_in,  // {sign, exp, mant}
    output logic [EXP_WIDTH + MANT_WIDTH : 0] data_out
);
  assign data_out = data_in;
endmodule
