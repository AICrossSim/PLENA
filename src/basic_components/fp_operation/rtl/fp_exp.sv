`timescale 1ns / 1ps
/*
 This code actually input mxint and then output rounded integer n,
 In the first version, we just keep the width of n is 8
 which means like output n range from [-128:127]
*/
module fp_exp #(
    parameter   IN_EXP_WIDTH = 5,
    parameter   IN_FIX_WIDTH = 8,
    parameter   IN_FIX_FRAC_WIDTH = 5,
    parameter   EXTEND_WIDTH = 5,
    parameter   OUT_EXP_WIDTH = -1,
    parameter   OUT_FIX_WIDTH = -1,
    parameter   OUT_FIX_FRAC_WIDTH = -1
)(
    input logic signed [IN_FIX_WIDTH - 1:0] signed_mant_in,
    input logic signed [IN_EXP_WIDTH - 1:0] signed_exp_in,
    output logic signed [OUT_EXP_WIDTH - 1:0] signed_exp_out,
    output logic signed [OUT_FIX_WIDTH - 1:0] signed_mant_out
);

  localparam signed MLOG2_E = 7'd92;
  localparam signed ELOG2_E = 4'd1;

  localparam LOG2_E_WIDTH = IN_FIX_WIDTH + EXTEND_WIDTH;

  localparam MAX_INT_WIDTH = 10;
  localparam FIXED_POINT_DATA_WIDTH = LOG2_E_WIDTH + MAX_INT_WIDTH;
  localparam FIXED_POINT_DATA_FRAC_WIDTH = IN_FIX_FRAC_WIDTH + EXTEND_WIDTH;
  localparam TAYLOR_OUTPUT_WIDTH = FIXED_POINT_DATA_FRAC_WIDTH + 3;

  logic unsigned [IN_FIX_WIDTH - 1:0] unsigned_mant_in;
  logic unsigned [LOG2_E_WIDTH - 1:0] unsigned_mant_in_extended;
  assign unsigned_mant_in_extended = {unsigned_mant_in, {EXTEND_WIDTH{1'b0}}};

  logic [IN_EXP_WIDTH - 1:0] signed_exp_in_log2_e;
  logic [LOG2_E_WIDTH - 1:0] signed_mant_in_log2_e;
  logic [LOG2_E_WIDTH - 1:0] unsigned_mant_in_log2_e;

  logic mant_sign;
  assign mant_sign = signed_mant_in[IN_FIX_WIDTH-1];
  assign unsigned_mant_in = mant_sign ? -signed_mant_in : signed_mant_in; 
  
  integer_mult #(
    .WIDTH(LOG2_E_WIDTH),
    .IN_1_WIDTH(7)
  ) integer_mult_inst_0 (
    .data_in_0(unsigned_mant_in_extended),
    .data_in_1(MLOG2_E),
    .data_out(unsigned_mant_in_log2_e)
  );

  assign signed_mant_in_log2_e = mant_sign ? -unsigned_mant_in_log2_e : unsigned_mant_in_log2_e;
  assign signed_exp_in_log2_e = $signed(signed_exp_in) + ELOG2_E;


  logic [FIXED_POINT_DATA_WIDTH - 1:0] fixed_point_data_in;
  logic [TAYLOR_OUTPUT_WIDTH - 1:0] taylor_output;

  bit_width_aware_signed_left_shift #(
    .IN_WIDTH(LOG2_E_WIDTH),
    .OUT_WIDTH(FIXED_POINT_DATA_WIDTH),
    .SHIFT_WIDTH(IN_EXP_WIDTH)
  ) bit_width_aware_signed_left_shift_inst (
    .in_data(signed_mant_in_log2_e),
    .shift_amt(signed_exp_in_log2_e),
    .out_data(fixed_point_data_in)
  );

  logic [FIXED_POINT_DATA_WIDTH - 1:FIXED_POINT_DATA_FRAC_WIDTH] fixed_point_int_part;
  logic [FIXED_POINT_DATA_FRAC_WIDTH - 1:0] fixed_point_frac_part;
  assign fixed_point_int_part = fixed_point_data_in[FIXED_POINT_DATA_WIDTH - 1:FIXED_POINT_DATA_FRAC_WIDTH];
  assign fixed_point_frac_part = $signed(fixed_point_data_in) - {fixed_point_int_part, {FIXED_POINT_DATA_FRAC_WIDTH{1'b0}}};

  taylor_series_expansion #(
    .IN_WIDTH(FIXED_POINT_DATA_FRAC_WIDTH),
    .OUT_WIDTH(TAYLOR_OUTPUT_WIDTH)
  ) taylor_series_expansion_inst (
    .data_in(fixed_point_frac_part),
    .data_out(taylor_output)
  );

  assign signed_exp_out = fixed_point_int_part;
  assign signed_mant_out = taylor_output >> EXTEND_WIDTH;
endmodule

module taylor_series_expansion #(
    // The input is assumed to be in the range of [0, 1]
    parameter   IN_WIDTH = 8,
    parameter   OUT_WIDTH = IN_WIDTH + 2
)(
    input logic unsigned [IN_WIDTH - 1:0] data_in,
    output logic unsigned [OUT_WIDTH - 1:0] data_out
);

  localparam COEFFICIENT_WIDTH = IN_WIDTH + 2; // the maximum is 2.7..
  
  // Fix: Proper array declaration for coefficients
  localparam  [IN_WIDTH:0] TERM_0 = 1 << (IN_WIDTH); // 1.0 in fixed point
  localparam  [5 - 1:0] LN_2 = 22 ; // ln(2) ≈ 0.693

  logic unsigned [OUT_WIDTH - 1:0] element_list [4-1:0];
  
  // Term 0: 1
  assign element_list[0] = TERM_0;
  
  // Term 1: ln(2) * x
  integer_mult #(
    .WIDTH(IN_WIDTH),
    .IN_1_WIDTH(5)
  ) integer_mult_inst_0 (
    .data_in_0(data_in),
    .data_in_1(LN_2),
    .data_out(element_list[1])
  );

  // Term 2: ln²(2) * x² / 2 = term1 * term1 / 2
  logic [IN_WIDTH - 1:0] intermediate_data_out;
  integer_mult #(
    .WIDTH(IN_WIDTH)
  ) integer_mult_inst_1 (
    .data_in_0(element_list[1]),
    .data_in_1(element_list[1]),
    .data_out(intermediate_data_out)
  );
  assign element_list[2] = (intermediate_data_out) >> 1;

  // Term 3: ln³(2) * x³ / 6 = term2 * term1 / 3
  logic [IN_WIDTH - 1:0] intermediate_data_out_2;
  integer_mult #(
    .WIDTH(IN_WIDTH)
  ) integer_mult_inst_2 (
    .data_in_0(element_list[2]),
    .data_in_1(element_list[1]),
    .data_out(intermediate_data_out_2)
  );
  integer_mult #(
    .WIDTH(IN_WIDTH),
    .IN_1_WIDTH(10)
  ) integer_mult_inst_3 (
    .data_in_0(intermediate_data_out_2),
    .data_in_1(TERM_0/3),
    .data_out(element_list[3])
  );

  // Sum all terms
  logic [IN_WIDTH + 2 - 1:0] fixed_tree_in [4-1:0];
  assign fixed_tree_in[0] = element_list[0];
  assign fixed_tree_in[1] = element_list[1];
  assign fixed_tree_in[2] = element_list[2];
  assign fixed_tree_in[3] = element_list[3];

  logic [OUT_WIDTH - 1:0] sum_result;
  assign sum_result = fixed_tree_in[0] + fixed_tree_in[1] + fixed_tree_in[2] + fixed_tree_in[3];
  assign data_out = sum_result;

endmodule

module integer_mult #(
    parameter   WIDTH = 8, 
    parameter   IN_1_WIDTH = WIDTH
)(
    input logic [WIDTH - 1:0] data_in_0,
    input logic [IN_1_WIDTH - 1:0] data_in_1,
    output logic [WIDTH - 1:0] data_out
);

  localparam INTERMEDIATE_WIDTH = WIDTH + IN_1_WIDTH;
  logic signed [INTERMEDIATE_WIDTH - 1:0] intermediate_data_out;
  assign intermediate_data_out = data_in_0 * data_in_1;
  
  round_to_nearest_even #(
    .IN_WIDTH(INTERMEDIATE_WIDTH),
    .OUT_WIDTH(WIDTH)
  ) round_to_nearest_even_inst (
    .data_in(intermediate_data_out),
    .data_out(data_out)
  );

endmodule
