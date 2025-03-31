`timescale 1ns / 1ps
module fp_dot_product #(
    parameter   MAN_WIDTH = 4,
    parameter   EXP_WIDTH = 3,
    parameter   VEC_DIM     = 8,
    localparam  PRODUCT_MAN_WIDTH = MAN_WIDTH + MAN_WIDTH + 1, 
    localparam  PRODUCT_EXP_WIDTH = EXP_WIDTH
    localparam  EXT_BITS_PER_LAYER = 1 << PRODUCT_EXP_WIDTH,
    localparam  RESULT_MAN_WIDTH = PRODUCT_MAN_WIDTH + $clog2(IN_SIZE),
    localparam  RESULT_EXP_WIDTH = PRODUCT_EXP_WIDTH

    // parameter OUT_WIDTH = IN_WIDTH + WEIGHT_WIDTH + $clog2(IN_SIZE) * 
) (
    input clk,
    input rst,

    // input port A
    input  logic [VEC_DIM-1:0] [(MAN_WIDTH + EXP_WIDTH):0] data_a_in,
    input                       data_a_in_valid,
    output                      data_a_in_ready,

    // input port B
    input  logic [VEC_DIM-1:0] [(MAN_WIDTH + EXP_WIDTH):0] data_b_in,
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
      .MAN_WIDTH(MAN_WIDTH),
      .EXP_WIDTH(EXP_WIDTH),
      .MAN_WIDTH(MAN_WIDTH),
      .EXP_WIDTH(EXP_WIDTH),
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
  fp_adder_tree #(
      .LAYER_DIM (IN_SIZE),
      .IN_WIDTH(PRODUCT_WIDTH)
  ) fp_full_precision_add_tree (
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
