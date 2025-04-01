`timescale 1ns / 1ps
/*
Module      : Floating Point Rounding Unit
Timing      : Combinatorial Logic
Description : Rounds a floating point number to a different precision.
              Output format: {sign, exp_out, mant_out}.
              Round Mantissa based on Guard, Round, Sticky bits.
*/

module fp_round #(
    parameter IN_EXP_WIDTH   = 4,
    parameter IN_MANT_WIDTH  = 5,
    parameter OUT_EXP_WIDTH  = 4,
    parameter OUT_MANT_WIDTH = 3
) (
    input  logic [IN_EXP_WIDTH + IN_MANT_WIDTH:0] data_in,
    output logic [OUT_EXP_WIDTH + OUT_MANT_WIDTH:0] data_out
);

  initial begin
    assert(IN_EXP_WIDTH >= OUT_EXP_WIDTH)
    else $fatal("OUT_EXP_WIDTH must be less than or equal to IN_EXP_WIDTH");
    assert(IN_MANT_WIDTH >= OUT_MANT_WIDTH)
    else $fatal("OUT_MANT_WIDTH must be less than or equal to IN_MANT_WIDTH");
  end

  // Widths
  localparam IN_WIDTH  = IN_EXP_WIDTH + IN_MANT_WIDTH + 1;
  localparam OUT_WIDTH = OUT_EXP_WIDTH + OUT_MANT_WIDTH + 1;
  localparam RND_BITS  = IN_MANT_WIDTH - OUT_MANT_WIDTH;

  // Biases
  localparam int IN_BIAS  = (1 << (IN_EXP_WIDTH - 1)) - 1;
  localparam int OUT_BIAS = (1 << (OUT_EXP_WIDTH - 1)) - 1;

  // Internal signals
  logic sign;
  logic [IN_EXP_WIDTH-1:0]    exp_in;
  logic [IN_MANT_WIDTH-1:0]   mant_in;

  logic [OUT_MANT_WIDTH-1:0]  mant_trunc;
  logic                       guard, round_bit, sticky;
  logic [RND_BITS-1:0]        round_section;

  logic [OUT_MANT_WIDTH:0]    mant_rounded;
  logic                       round_up, mant_overflow;

  logic [IN_EXP_WIDTH:0]      exp_intermediate;
  logic [OUT_EXP_WIDTH-1:0]   exp_out;
  logic [OUT_MANT_WIDTH-1:0]  mant_final;
  logic                       exp_overflow;

  // mantissa truncation
  generate
    if (OUT_MANT_WIDTH < IN_MANT_WIDTH) begin : gen_truncate
      assign  mant_trunc = mant_in[IN_MANT_WIDTH-1 -: OUT_MANT_WIDTH];
      assign  round_section = mant_in[IN_MANT_WIDTH - OUT_MANT_WIDTH - 1:0];
    end else begin : gen_no_truncate
      assign mant_trunc = mant_in;
      assign round_section = '0;
    end
  endgenerate

  // Guard, Round, Sticky bits
  generate;
    if (RND_BITS >= 1) begin : gen_g
      assign guard = round_section[RND_BITS-1];
    end else begin : gen_no_g
      assign guard = 1'b0;
    end

    if (RND_BITS >= 2) begin : gen_r
      assign round_bit = round_section[RND_BITS-2];
    end else begin : gen_no_r
      assign round_bit = 1'b0;
    end

    if (RND_BITS > 2) begin : gen_s
      assign sticky = |round_section[RND_BITS-3:0];
    end else begin : gen_no_s
      assign sticky = 1'b0;
    end

  endgenerate

  always_comb begin
    // Decompose input
    sign     = data_in[IN_WIDTH-1];
    exp_in   = data_in[IN_WIDTH-2 -: IN_EXP_WIDTH];
    mant_in  = data_in[IN_MANT_WIDTH-1:0];

    // Round to Nearest Even
    round_up      = guard && (round_bit || sticky || mant_trunc[0]);
    mant_rounded  = mant_trunc + round_up;
    mant_overflow = mant_rounded[OUT_MANT_WIDTH]; // Carry out

    // Adjust exponent bias and add mantissa overflow
    exp_intermediate = exp_in - IN_BIAS + OUT_BIAS + mant_overflow;
    exp_overflow     = |exp_intermediate[IN_EXP_WIDTH:OUT_EXP_WIDTH];

    if (exp_overflow) begin
      exp_out = {OUT_EXP_WIDTH{1'b1}}; // Clamp on overflow
    end else begin
      exp_out = exp_intermediate[OUT_EXP_WIDTH-1:0];
    end

    // Final mantissa
    mant_final = mant_overflow ? mant_rounded[OUT_MANT_WIDTH:1] :
                                 mant_rounded[OUT_MANT_WIDTH-1:0];
  end

  // Final output
  assign data_out = {sign, exp_out, mant_final};

endmodule
