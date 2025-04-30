`timescale 1ns / 1ps
// `include "operation.svh"

/*
Module      : Vector Exp
Timing      : Combinatorial Logic
Description : This module includes elementwise vector computations 
            : 4. Elementwise Exponential
Status      : Under Development
*/

module  fp_exp #(
    parameter   EXP_WIDTH = 5,
    parameter   MANT_WIDTH = 10
)(
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_in,  // {sign, exp, mant}
    output logic [EXP_WIDTH + MANT_WIDTH : 0] data_out,
);
  localparam DATA_LOG2_E_WIDTH = 8;
  localparam DATA_LOG2_E_FRAC_WIDTH = 4;
  localparam signed FIXED_LOG2_E = 8'H40;

  localparam DATA_N_WIDTH = 8; // Including sign bit
  localparam DATA_R_WIDTH = 8; // Including sign bit
  localparam DATA_IN_FIXED_WIDTH = DATA_N_WIDTH + DATA_R_WIDTH - 1;

  logic [DATA_IN_FIXED_WIDTH - 1:0] data_in_fixed;

  logic [DATA_IN_FIXED_WIDTH - 1:0] data_in_fixed_log2_e;

  logic [DATA_IN_FIXED_WIDTH - 1:0] data_in_fixed_log2_e_rounded;
  // data_n is the integer part of the fixed point number
  // data_r is the fractional part of the fixed point number
  logic [DATA_N_WIDTH - 1:0] data_in_n;
  logic [DATA_R_WIDTH - 1:0] data_in_r;
  logic [MANT_WIDTH - 1:0] data_in_mant;
  logic [EXP_WIDTH - 1:0] data_in_exp;
  logic sign_bit;
  logic [DATA_R_WIDTH - 1:0] shift_value;

  fp_2_sign_mag #(
    .FP_EXP_WIDTH(EXP_WIDTH),
    .FP_MANT_WIDTH(MANT_WIDTH),
    .SIGN_MAG_WIDTH(DATA_IN_FIXED_WIDTH),
    .SIGN_MAG_FRAC_WIDTH(DATA_R_WIDTH - 1)
  ) fp_to_fixed_conversion_inst (
    .data_in(data_in),
    .data_out(data_in_fixed)
  );

  assign data_in_fixed_log2_e = data_in_fixed * FIXED_LOG2_E;
  fixed_round #(
    .IN_WIDTH(DATA_IN_FIXED_WIDTH + DATA_LOG2_E_WIDTH),
    .IN_FRAC_WIDTH(DATA_IN_FIXED_WIDTH - 1 + DATA_LOG2_E_FRAC_WIDTH),
    .OUT_WIDTH(DATA_IN_FIXED_WIDTH),
    .OUT_FRAC_WIDTH(DATA_IN_FIXED_WIDTH - 1)
  ) fixed_round_inst (
    .data_in(data_in_fixed_log2_e),
    .data_out(data_in_fixed_log2_e_rounded)
  );
  
  assign data_in_n = {data_in_fixed_log2_e_rounded[DATA_IN_FIXED_WIDTH - 1], data_in_fixed_log2_e_rounded[DATA_N_WIDTH + DATA_R_WIDTH - 3:DATA_R_WIDTH - 1]};
  assign data_in_r = {data_in_fixed_log2_e_rounded[DATA_IN_FIXED_WIDTH - 1], data_in_fixed_log2_e_rounded[DATA_R_WIDTH - 2:0]};

  // Calculate shift value based on fractional widths
  assign shift_value = DATA_LOG2_E_FRAC_WIDTH - DATA_R_WIDTH - $signed(data_in_fixed_log2_e);

  fixed_2_n #(
    .DATA_IN_WIDTH(DATA_R_WIDTH),
    .DATA_IN_FRAC_WIDTH(DATA_R_WIDTH - 1),
    .DATA_OUT_WIDTH(MANT_WIDTH),
    .DATA_OUT_FRAC_WIDTH(MANT_WIDTH - 2)
  ) fixed_2_n_inst (
    .data_in(data_in_r),
    .data_out(data_in_mant)
  );

  fix_with_shift_2_fp_fake #(
    .FIXED_DATA_WIDTH(DATA_R_WIDTH),
    .SHIFT_WIDTH(DATA_R_WIDTH),
    .FP_EXP_WIDTH(EXP_WIDTH),
    .FP_MANT_WIDTH(MANT_WIDTH)
  ) fix_with_shift_2_fp_inst (
    .data_in(data_in_r),
    .shift_in(data_in_n),
    .exp_out(data_in_exp),
    .mant_out(data_in_mant)
  );

  assign sign_bit = data_in_mant[MANT_WIDTH - 1];
  assign data_out = {sign_bit, data_in_exp, data_in_mant};

endmodule

module fix_with_shift_2_fp_fake #(
    parameter FIXED_DATA_WIDTH      = 8,
    parameter FP_EXP_WIDTH          = 3,
    parameter FP_MANT_WIDTH         = 2,
    parameter SHIFT_WIDTH           = 8
)(
    input  logic signed         [FIXED_DATA_WIDTH-1:0]  data_in,
    input  logic unsigned       [SHIFT_WIDTH-1:0]       shift_in,
    output logic                [FP_EXP_WIDTH-1:0]      exp_out,
    output logic                [FP_MANT_WIDTH-1:0]     mant_out
);
    assign exp_out = shift_in;
    assign mant_out = data_in;
endmodule

module fixed_2_n #(
    parameter   DATA_IN_WIDTH = 8,
    parameter   DATA_IN_FRAC_WIDTH = 7,
    parameter   DATA_OUT_WIDTH = 8,
    parameter   DATA_OUT_FRAC_WIDTH = 8
)(
    input logic [DATA_IN_WIDTH - 1:0] data_in,
    output logic [DATA_OUT_WIDTH - 1:0] data_out
);
    // TODO: testing
    // TODO: 1st get the value  
    // TODO: 2nd normalize the value
    // Linear approximation of 2^n using the formula: 2^n ≈ 1 + n*ln(2)
    // For fixed-point representation, we scale by 2^FRAC_WIDTH
    // 1 is represented as 2^FRAC_WIDTH in our fixed-point format
    // ln(2) ≈ 0.693147... is scaled to fixed-point
    localparam logic [DATA_IN_WIDTH-1:0] ONE_FIXED = (1 << DATA_IN_FRAC_WIDTH);
    localparam logic [DATA_IN_WIDTH-1:0] LN2_FIXED = (DATA_IN_FRAC_WIDTH > 8) ? 
                                                 (177 << (DATA_IN_FRAC_WIDTH - 8)) : // 0.693147 * 2^8 ≈ 177
                                                 (177 >> (8 - DATA_IN_FRAC_WIDTH));  // Scale down if needed
    
    // Linear approximation: 2^n ≈ 1 + n*ln(2)
    assign data_out = ONE_FIXED + ((data_in * LN2_FIXED) >>> DATA_IN_FRAC_WIDTH);

endmodule


