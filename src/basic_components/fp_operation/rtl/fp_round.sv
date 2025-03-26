`timescale 1ns / 1ps

module fp_round #(
    parameter EXP_WIDTH      = 5,
    parameter IN_MANT_WIDTH  = 10,
    parameter OUT_MANT_WIDTH = 5
) (
    input  logic [1 + EXP_WIDTH + IN_MANT_WIDTH - 1:0] data_in,
    output logic [1 + EXP_WIDTH + OUT_MANT_WIDTH - 1:0] data_out
);

  // Decompose input
  localparam IN_WIDTH  = 1 + EXP_WIDTH + IN_MANT_WIDTH;
  localparam OUT_WIDTH = 1 + EXP_WIDTH + OUT_MANT_WIDTH;

  logic                      sign;
  logic [EXP_WIDTH-1:0]      exponent;
  logic [IN_MANT_WIDTH-1:0]  mantissa_in;

  assign sign        = data_in[IN_WIDTH-1];
  assign exponent    = data_in[IN_WIDTH-2 -: EXP_WIDTH];
  assign mantissa_in = data_in[IN_MANT_WIDTH-1:0];

  // Rounding bits
  logic guard_bit, round_bit, sticky_bit;
  logic [OUT_MANT_WIDTH:0] mantissa_rounded;

  // Extract rounding bits
  always_comb begin
    guard_bit = (IN_MANT_WIDTH > OUT_MANT_WIDTH) ? mantissa_in[IN_MANT_WIDTH - OUT_MANT_WIDTH - 1] : 1'b0;
    round_bit = (IN_MANT_WIDTH > OUT_MANT_WIDTH + 1) ? mantissa_in[IN_MANT_WIDTH - OUT_MANT_WIDTH - 2] : 1'b0;
    if (IN_MANT_WIDTH > OUT_MANT_WIDTH + 2)
      sticky_bit = |mantissa_in[0 +: (IN_MANT_WIDTH - OUT_MANT_WIDTH - 2)];
    else
      sticky_bit = 1'b0;
  end

  // Round-to-nearest-even decision
  logic round_up;
  always_comb begin
    if (guard_bit && (round_bit || sticky_bit || mantissa_in[IN_MANT_WIDTH - OUT_MANT_WIDTH] == 1'b1))
      round_up = 1'b1;
    else
      round_up = 1'b0;
  end

  // Round mantissa
  always_comb begin
    mantissa_rounded = mantissa_in[IN_MANT_WIDTH-1 -: (OUT_MANT_WIDTH+1)] + round_up;
  end

  // Handle mantissa overflow
  logic [EXP_WIDTH-1:0] exponent_out;
  logic [OUT_MANT_WIDTH-1:0] mantissa_out;

  always_comb begin
    if (mantissa_rounded[OUT_MANT_WIDTH]) begin
      mantissa_out = mantissa_rounded[OUT_MANT_WIDTH:1]; // shift down
      exponent_out = exponent + 1;
    end else begin
      mantissa_out = mantissa_rounded[OUT_MANT_WIDTH-1:0];
      exponent_out = exponent;
    end
  end

  // Reassemble output
  assign data_out = {sign, exponent_out, mantissa_out};

endmodule
