`timescale 1ns / 1ps
module fp_dot_product #(
    parameter   A_MAN_WIDTH = 4,
    parameter   A_EXP_WIDTH = 3,
    parameter   B_MAN_WIDTH = 4,
    parameter   B_EXP_WIDTH = 3,
    parameter   VEC_DIM     = 8,
    localparam  RESULT_MAN_WIDTH = A_MAN_WIDTH + B_MAN_WIDTH + 1,   // TODO
    localparam  RESULT_EXP_WIDTH = A_EXP_WIDTH

    // parameter OUT_WIDTH = IN_WIDTH + WEIGHT_WIDTH + $clog2(IN_SIZE)
) (
    input clk,
    input rst,

    // input port A
    input  logic [VEC_DIM-1:0] [(A_MAN_WIDTH + A_EXP_WIDTH):0] data_a_in,
    input                       data_a_in_valid,
    output                      data_a_in_ready,

    // input port B
    input  logic [VEC_DIM-1:0] [(B_MAN_WIDTH + B_EXP_WIDTH):0] data_b_in,
    input                       data_b_in_valid,
    output                      data_b_in_ready,

    // output port
    output logic [(RESULT_MAN_WIDTH + RESULT_EXP_WIDTH) :0] data_out,
    output                       data_out_valid,
    input                        data_out_ready

);



  logic [VEC_DIM-1:0] [(RESULT_MAN_WIDTH + RESULT_EXP_WIDTH)-1:0] pv;
  logic                     pv_valid;
  logic                     pv_ready;

  logic [  OUT_WIDTH-1:0] sum;
  logic                     sum_valid;
  logic                     sum_ready;

  fp_vector_mult #(
      .A_MAN_WIDTH(A_MAN_WIDTH),
      .A_EXP_WIDTH(A_EXP_WIDTH),
      .B_MAN_WIDTH(B_MAN_WIDTH),
      .B_EXP_WIDTH(B_EXP_WIDTH),
      .VEC_DIM(VEC_DIM),
      .RESULT_EXP_WIDTH(RESULT_MAN_WIDTH),
      .RESULT_EXP_WIDTH(RESULT_EXP_WIDTH)
  ) fp_vector_mult_inst (
      .clk(clk),
      .rst(rst),
      .data_a_in(data_a_in),
      .data_a_in_valid(data_a_in_valid),
      .data_a_in_ready(data_a_in_ready),
      .data_b_in(data_b_in),
      .data_b_in_valid(data_b_in_valid),
      .data_b_in_ready(data_b_in_ready),
      .data_out(pv),
      .data_out_valid(pv_valid),
      .data_out_ready(pv_ready)
  );


  // sum the products
  // sum = sum(pv)
  fixed_adder_tree #(
      .IN_SIZE (IN_SIZE),
      .IN_WIDTH(PRODUCT_WIDTH)
  ) fixed_adder_tree_inst (
      .clk(clk),
      .rst(rst),
      .data_in(pv),
      .data_in_valid(pv_valid),
      .data_in_ready(pv_ready),

      .data_out(sum),
      .data_out_valid(sum_valid),
      .data_out_ready(sum_ready)
  );

  // Picking the end of the buffer, wire them to the output port
  assign data_out = sum;
  assign data_out_valid = sum_valid;
  assign sum_ready = data_out_ready;

endmodule
