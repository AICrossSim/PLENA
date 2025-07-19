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
    input logic clk,
    input logic rst,
    input  logic data_in_valid,
    output logic data_in_ready,
    input logic signed [IN_FIX_WIDTH - 1:0] signed_mant_in,
    input logic signed [IN_EXP_WIDTH - 1:0] signed_exp_in,
    output logic data_out_valid,
    input  logic data_out_ready,
    output logic signed [OUT_EXP_WIDTH - 1:0] signed_exp_out,
    output logic signed [OUT_FIX_WIDTH - 1:0] signed_mant_out
);

  localparam signed [7-1:0] MLOG2_E = 7'd92;
  localparam signed ELOG2_E = 4'd1;
  localparam LOG2_E_WIDTH = IN_FIX_WIDTH + EXTEND_WIDTH;

  localparam MAX_INT_WIDTH = 10;
  localparam FIXED_POINT_DATA_WIDTH = LOG2_E_WIDTH + MAX_INT_WIDTH;
  localparam FIXED_POINT_DATA_FRAC_WIDTH = IN_FIX_FRAC_WIDTH + EXTEND_WIDTH;
  localparam TAYLOR_OUTPUT_WIDTH = FIXED_POINT_DATA_FRAC_WIDTH + 3;


  // --------------
  // P1
  // --------------

  logic unsigned [IN_FIX_WIDTH - 1:0] unsigned_mant_in;
  logic unsigned [LOG2_E_WIDTH - 1:0] unsigned_mant_in_extended;
  assign unsigned_mant_in_extended = {unsigned_mant_in, {EXTEND_WIDTH{1'b0}}};

  logic [LOG2_E_WIDTH - 1:0] unsigned_mant_in_log2_e, p1_unsigned_mant_in_log2_e;
  logic signed [IN_EXP_WIDTH - 1:0] p1_signed_exp_in;

  logic mant_sign;
  assign mant_sign = signed_mant_in[IN_FIX_WIDTH-1];
  assign unsigned_mant_in = mant_sign ? -signed_mant_in : signed_mant_in; 

  logic p1_integer_mult_in_valid,   p1_integer_mult_in_ready;
  logic p1_integer_mult_out_valid,  p1_integer_mult_out_ready;
  logic p1_exp_stored_in_valid,     p1_exp_stored_in_ready;
  logic p1_exp_stored_out_valid,    p1_exp_stored_out_ready;
  logic p1_data_ready, p1_data_valid;
  logic p1_mant_sign;
  
  split_n #(
      .N(2)
  ) split_mant_signal (
      .data_in_valid(data_in_valid),
      .data_in_ready(data_in_ready),
      .data_out_valid({p1_integer_mult_in_valid, p1_exp_stored_in_valid}),
      .data_out_ready({p1_integer_mult_in_ready, p1_exp_stored_in_ready})
  );

  integer_mult #(
    .WIDTH(LOG2_E_WIDTH),
    .IN_1_WIDTH(7)
  ) integer_mult_inst_0 (
    .data_in_0(unsigned_mant_in_extended),
    .data_in_1(MLOG2_E),
    .data_out(unsigned_mant_in_log2_e)
  );

  skid_buffer #(
      .DATA_WIDTH(LOG2_E_WIDTH)
  ) buffer_mant_prod_result (
      .clk(clk),
      .rst(rst),
      .data_in        (unsigned_mant_in_log2_e),
      .data_in_valid  (p1_integer_mult_in_valid),
      .data_in_ready  (p1_integer_mult_in_ready),
      .data_out       (p1_unsigned_mant_in_log2_e),
      .data_out_valid (p1_integer_mult_out_valid),
      .data_out_ready (p1_integer_mult_out_ready)
  );

  skid_buffer #(
      .DATA_WIDTH(IN_EXP_WIDTH + 1)
  ) buffer_exp_stored (
      .clk(clk),
      .rst(rst),
      .data_in        ({mant_sign, signed_exp_in}),
      .data_in_valid  (p1_exp_stored_in_valid),
      .data_in_ready  (p1_exp_stored_in_ready),
      .data_out       ({p1_mant_sign, p1_signed_exp_in}),
      .data_out_valid (p1_exp_stored_out_valid),
      .data_out_ready (p1_exp_stored_out_ready)
  );


  // --------------
  // P2
  // --------------

  logic [LOG2_E_WIDTH - 1:0] p2_signed_mant_in_log2_e;
  logic [IN_EXP_WIDTH - 1:0] p2_signed_exp_in_log2_e;
  logic [FIXED_POINT_DATA_WIDTH - 1:0] p2_fixed_point_data_in, p2_fixed_point_data_out;
  logic p2_data_ready, p2_data_valid;

  assign p2_signed_mant_in_log2_e = p1_mant_sign ? -p1_unsigned_mant_in_log2_e : p1_unsigned_mant_in_log2_e;
  assign p2_signed_exp_in_log2_e = $signed(p1_signed_exp_in) + ELOG2_E;


  bit_width_aware_signed_left_shift #(
    .IN_WIDTH(LOG2_E_WIDTH),
    .OUT_WIDTH(FIXED_POINT_DATA_WIDTH),
    .SHIFT_WIDTH(IN_EXP_WIDTH)
  ) bit_width_aware_signed_left_shift_inst (
    .in_data(p2_signed_mant_in_log2_e),
    .shift_amt(p2_signed_exp_in_log2_e),
    .out_data(p2_fixed_point_data_in)
  );

  skid_buffer #(
      .DATA_WIDTH(FIXED_POINT_DATA_WIDTH)
  ) buffer_p2_exp_stored (
      .clk(clk),
      .rst(rst),
      .data_in        (p2_fixed_point_data_in),
      .data_in_valid  (p1_data_valid),
      .data_in_ready  (p1_data_ready),
      .data_out       (p2_fixed_point_data_out),
      .data_out_valid (p2_data_valid),
      .data_out_ready (p2_data_ready)
  );

  // --------------
  // P3
  // --------------

  logic [TAYLOR_OUTPUT_WIDTH - 1:0] taylor_output;
  logic [FIXED_POINT_DATA_WIDTH - 1:FIXED_POINT_DATA_FRAC_WIDTH] fixed_point_int_part;
  logic [FIXED_POINT_DATA_FRAC_WIDTH - 1:0] p3_fixed_point_frac_part_in, p3_fixed_point_frac_part_out;
  logic p3_data_ready, p3_data_valid;

  assign fixed_point_int_part   = p2_fixed_point_data_out[FIXED_POINT_DATA_WIDTH - 1:FIXED_POINT_DATA_FRAC_WIDTH];
  assign fixed_point_frac_part  = $signed(p2_fixed_point_data_out) - {fixed_point_int_part, {FIXED_POINT_DATA_FRAC_WIDTH{1'b0}}};

  skid_buffer #(
      .DATA_WIDTH(FIXED_POINT_DATA_FRAC_WIDTH)
  ) buffer_p3_exp_stored (
      .clk(clk),
      .rst(rst),
      .data_in        (p3_fixed_point_frac_part_in),
      .data_in_valid  (p2_data_valid),
      .data_in_ready  (p2_data_ready),
      .data_out       (p3_fixed_point_frac_part_out),
      .data_out_valid (p3_data_valid),
      .data_out_ready (p3_data_ready)
  );

  taylor_series_expansion #(
    .IN_WIDTH(FIXED_POINT_DATA_FRAC_WIDTH),
    .OUT_WIDTH(TAYLOR_OUTPUT_WIDTH)
  ) taylor_series_expansion_inst (
    .clk(clk),
    .rst(rst),
    .data_in_valid(p3_data_valid),
    .data_in_ready(p3_data_ready),
    .data_in(p3_fixed_point_frac_part_out),
    .data_out_valid(data_out_valid),
    .data_out_ready(data_out_ready),    
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
    input   logic clk,
    input   logic rst,
    input   logic data_in_valid,
    output  logic data_in_ready,
    input   logic unsigned [IN_WIDTH - 1:0] data_in,
    output  logic data_out_valid,
    input   logic data_out_ready,
    output  logic unsigned [OUT_WIDTH - 1:0] data_out
);

  localparam COEFFICIENT_WIDTH = IN_WIDTH + 2; // the maximum is 2.7..
  
  // Fix: Proper array declaration for coefficients
  localparam [IN_WIDTH : 0] TERM_0 = 1 << (IN_WIDTH); // 1.0 in fixed point
  localparam [IN_WIDTH - 1 : 0] TERM_1 = TERM_0 / 3; // 2.0 in fixed point
  localparam [5-1:0] LN_2 = 22 ; // ln(2) ≈ 0.693

  logic unsigned [IN_WIDTH - 1:0] element_list [4-1:0];

  // --------------
  // P1
  // --------------

  logic unsigned [IN_WIDTH - 1:0] p1_element_1;
  logic p1_mul_out_ready, p1_mul_out_valid;

  // Term 1: ln(2) * x
  integer_mult #(
    .WIDTH(IN_WIDTH),
    .IN_1_WIDTH(5)
  ) integer_mult_inst_0 (
    .data_in_0(data_in),
    .data_in_1(LN_2),
    .data_out(element_list[1])
  );

  skid_buffer #(
    .DATA_WIDTH(IN_WIDTH)
  ) buffer_element_1 (
    .clk(clk),
    .rst(rst),
    .data_in        (element_list[1]),
    .data_in_valid  (data_in_valid),
    .data_in_ready  (data_in_ready),
    .data_out       (p1_element_1),
    .data_out_valid (p1_mul_out_valid),
    .data_out_ready (p1_mul_out_ready)
  );

  // --------------
  // P2
  // --------------

  // Term 2: ln²(2) * x² / 2 = term1 * term1 / 2
  logic [IN_WIDTH - 1:0] p2_intermediate_data_out;
  logic p2_mul_in_ready, p2_mul_in_valid;
  logic p2_mul_out_ready, p2_mul_out_valid;
  logic p2_store_1_in_ready, p2_store_1_in_valid;
  logic p2_store_1_out_ready, p2_store_1_out_valid;
  logic p2_data_ready, p2_data_valid;

  logic unsigned [IN_WIDTH - 1:0] p2_element_1;
  logic unsigned [IN_WIDTH - 1:0] p2_element_2;

  integer_mult #(
    .WIDTH(IN_WIDTH)
  ) integer_mult_inst_1 (
    .data_in_0(p1_element_1),
    .data_in_1(p1_element_1),
    .data_out(p2_intermediate_data_out)
  );
  assign element_list[2] = (p2_intermediate_data_out) >> 1;

  split_n #(
    .N(2)
  ) split_p2_signal (
    .data_in_valid(p1_mul_out_valid),
    .data_in_ready(p1_mul_out_ready),
    .data_out_valid({p2_mul_in_valid, p2_store_1_in_valid}),
    .data_out_ready({p2_mul_in_ready, p2_store_1_in_ready})
  );

  skid_buffer #(
    .DATA_WIDTH(IN_WIDTH)
  ) buffer_p2_ele_1 (
    .clk(clk),
    .rst(rst),
    .data_in        (element_list[2]),
    .data_in_valid  (p2_mul_in_valid),
    .data_in_ready  (p2_mul_in_ready),
    .data_out       (p2_element_2),
    .data_out_valid (p2_mul_out_valid),
    .data_out_ready (p2_mul_out_ready)
  );

  skid_buffer #(
    .DATA_WIDTH(IN_WIDTH)
  ) buffer_p2_ele_2 (
    .clk(clk),
    .rst(rst),
    .data_in        (p1_element_1),
    .data_in_valid  (p2_store_1_in_valid),
    .data_in_ready  (p2_store_1_in_ready),
    .data_out       (p2_element_1),
    .data_out_valid (p2_store_1_out_valid),
    .data_out_ready (p2_store_1_out_ready)
  );

  join2 #() join_p2_signal (
    .data_in_valid({p2_mul_out_valid, p2_store_1_out_valid}),
    .data_in_ready({p2_mul_out_ready, p2_store_1_out_ready}),
    .data_out_valid(p2_data_valid),
    .data_out_ready(p2_data_ready)
  );

  // --------------
  // P3
  // --------------

  // Term 3: ln³(2) * x³ / 6 = term2 * term1 / 3
  logic [IN_WIDTH - 1:0] p3_intermediate_data_out;

  logic unsigned [IN_WIDTH - 1:0] p3_element_1;
  logic unsigned [IN_WIDTH - 1:0] p3_element_2;
  logic unsigned [IN_WIDTH - 1:0] p3_element_3;

  logic p3_store_1_in_ready,  p3_store_1_in_valid;
  logic p3_store_1_out_ready, p3_store_1_out_valid;
  logic p3_store_2_in_ready,  p3_store_2_in_valid;
  logic p3_store_2_out_ready, p3_store_2_out_valid;
  logic p3_mul_in_ready,      p3_mul_in_valid;
  logic p3_mul_out_ready,     p3_mul_out_valid;

  split_n #(
    .N(3)
  ) split_taylor_signal_3 (
    .data_in_valid(p2_data_valid),
    .data_in_ready(p2_data_ready),
    .data_out_valid({p3_mul_in_valid, p3_store_1_in_valid, p3_store_2_in_valid}),
    .data_out_ready({p3_mul_in_ready, p3_store_1_in_ready, p3_store_2_in_ready})
  );

  integer_mult #(
    .WIDTH(IN_WIDTH)
  ) integer_mult_inst_2 (
    .data_in_0(p2_element_2),
    .data_in_1(p2_element_1),
    .data_out(p3_intermediate_data_out)
  );

  integer_mult #(
    .WIDTH(IN_WIDTH),
    .IN_1_WIDTH(IN_WIDTH)
  ) integer_mult_inst_3 (
    .data_in_0(p3_intermediate_data_out),
    .data_in_1(TERM_1),
    .data_out(element_list[3])
  );


  skid_buffer #(
    .DATA_WIDTH(IN_WIDTH)
  ) buffer_p3_ele_1 (
    .clk(clk),
    .rst(rst),
    .data_in        (p2_element_1),
    .data_in_valid  (p3_store_1_in_valid),
    .data_in_ready  (p3_store_1_in_ready),
    .data_out       (p3_element_1),
    .data_out_valid (p3_store_1_out_valid),
    .data_out_ready (p3_store_1_out_ready)
  );

  skid_buffer #(
    .DATA_WIDTH(IN_WIDTH)
  ) buffer_p3_ele_2 (
    .clk(clk),
    .rst(rst),
    .data_in        (p2_element_2),
    .data_in_valid  (p3_store_2_in_valid),
    .data_in_ready  (p3_store_2_in_ready),
    .data_out       (p3_element_2),
    .data_out_valid (p3_store_2_out_valid),
    .data_out_ready (p3_store_2_out_ready)
  );

  skid_buffer #(
    .DATA_WIDTH(IN_WIDTH)
  ) buffer_p3_ele_3 (
    .clk(clk),
    .rst(rst),
    .data_in        (element_list[3]),
    .data_in_valid  (p3_mul_in_valid),
    .data_in_ready  (p3_mul_in_ready),
    .data_out       (p3_element_3),
    .data_out_valid (p3_mul_out_valid),
    .data_out_ready (p3_mul_out_ready)
  );

  join_n #(
    .NUM_HANDSHAKES(3)
  ) join_p3_signal (
    .data_in_valid({p3_mul_out_valid, p3_store_1_out_valid, p3_store_2_out_valid}),
    .data_in_ready({p3_mul_out_ready, p3_store_1_out_ready, p3_store_2_out_ready}),
    .data_out_valid(p3_data_valid),
    .data_out_ready(p3_data_ready)
  );


  // --------------
  // P4
  // --------------

  // Sum all terms
  logic [OUT_WIDTH - 1:0] sum_result;
  assign sum_result = TERM_0 + p3_element_1 + p3_element_2 + p3_element_3;

  skid_buffer #(
    .DATA_WIDTH(OUT_WIDTH)
  ) buffer_taylor_output (
    .clk(clk),
    .rst(rst),
    .data_in        (sum_result),
    .data_in_valid  (p3_data_valid),
    .data_in_ready  (p3_data_ready),
    .data_out       (data_out),
    .data_out_valid (data_out_valid),
    .data_out_ready (data_out_ready)
  );

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
  logic signed [INTERMEDIATE_WIDTH - 1:0] p2_intermediate_data_out;
  assign p2_intermediate_data_out = data_in_0 * data_in_1;
  
  round_to_nearest_even #(
    .IN_WIDTH(INTERMEDIATE_WIDTH),
    .OUT_WIDTH(WIDTH)
  ) round_to_nearest_even_inst (
    .data_in(p2_intermediate_data_out),
    .data_out(data_out)
  );

endmodule
