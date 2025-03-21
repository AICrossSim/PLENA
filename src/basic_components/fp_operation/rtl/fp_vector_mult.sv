`timescale 1ns / 1ps
/*
Module      : two floating point vectors' elementwise multiplication
Description : FP datatype Sign Bit + MAN_WIDTH + EXP_WIDTH
*/
module fp_vector_mult #(
    parameter   A_MAN_WIDTH = 4,
    parameter   A_EXP_WIDTH = 3,
    parameter   B_MAN_WIDTH = 4,
    parameter   B_EXP_WIDTH = 3,
    parameter   VEC_DIM     = 8,
    localparam  RESULT_MAN_WIDTH = A_MAN_WIDTH + B_MAN_WIDTH + 1,
    localparam  RESULT_EXP_WIDTH = A_EXP_WIDTH
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
    output logic [VEC_DIM-1:0] [(RESULT_MAN_WIDTH + RESULT_EXP_WIDTH):0]     data_out,
    output                       data_out_valid,
    input                        data_out_ready
);

  // pv[i] = data_in[i] * w[i]
  logic [VEC_DIM-1:0] [(RESULT_MAN_WIDTH + RESULT_EXP_WIDTH):0]  product_vector;
  logic product_data_in_valid;
  logic product_data_in_ready;
  logic product_data_out_valid;
  logic product_data_out_ready;

//   logic [$bits(product_vector)-1:0] product_data_in;
//   logic [$bits(product_vector)-1:0] product_data_out;

  for (genvar i = 0; i < VEC_DIM; i = i + 1) begin : parallel_mult
    fp_mult #(
        .IN_A_WIDTH(IN_WIDTH),
        .IN_B_WIDTH(WEIGHT_WIDTH)
    ) fp_vector_element_mult (
        .data_a (data_in[i]),
        .data_b (weight[i]),
        .product(product_vector[i])
    );
  end



  join2 #() join_inst (
      .data_in_ready ({data_a_in_ready, data_b_in_ready}),
      .data_in_valid ({data_a_in_valid, data_b_in_valid}),
      .data_out_valid(product_data_in_valid),
      .data_out_ready(product_data_in_ready)
  );

  // Cocotb/verilator does not support array flattening, so
  // we need to manually add some reshaping process.


  skid_buffer #(
      .DATA_WIDTH($bits(product_vector))
  ) register_slice (
      .clk           (clk),
      .rst           (rst),
      .data_in       (product_vector),
      .data_in_valid (product_data_in_valid),
      .data_in_ready (product_data_in_ready),
      .data_out      (product_data_out),
      .data_out_valid(product_data_out_valid),
      .data_out_ready(product_data_out_ready)
  );

  // Casting array for product vector
  for (genvar i = 0; i < IN_SIZE; i++) begin : reshape_out
    assign data_out[i] = product_data_out[PRODUCT_WIDTH*i+PRODUCT_WIDTH-1:PRODUCT_WIDTH*i];
  end

  assign data_out_valid = product_data_out_valid;
  assign product_data_out_ready = data_out_ready;

endmodule
