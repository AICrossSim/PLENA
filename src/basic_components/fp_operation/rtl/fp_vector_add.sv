`timescale 1ns / 1ps
/*
Module      : Floating Point Configurable Precision Adder (With Sign)
Timing      : Combinatorial Logic
Description : Add two FP numbers with different exponents and signs.
Status      : Not used
*/
module fp_vector_add #(
    parameter   VEC_DIM     = 8,
    parameter   MANT_WIDTH  = 4,
    parameter   EXP_WIDTH   = 3,
    // Amount of bits needed to shift mantissas for alignment
    parameter   EXT_MANT_WIDTH = 4,
    // Need to increase exp width by 1 to handle overflow
    parameter   EXT_EXP_WIDTH = 1
) (
    input clk,
    input rst,

    // input port A
    input  logic [VEC_DIM-1:0] [(MANT_WIDTH + EXP_WIDTH):0] data_a_in,
    input                       data_a_in_valid,
    output                      data_a_in_ready,

    // input port B
    input  logic [VEC_DIM-1:0] [(MANT_WIDTH + EXP_WIDTH):0] data_b_in,
    input                       data_b_in_valid,
    output                      data_b_in_ready,


    // output port
    output logic [VEC_DIM-1:0] [EXP_WIDTH + EXT_EXP_WIDTH + MANT_WIDTH + EXT_MANT_WIDTH : 0]     data_out,
    output                       data_out_valid,
    input                        data_out_ready
);

  // pv[i] = data_in[i] * w[i]
  logic [VEC_DIM-1:0] [EXP_WIDTH + EXT_EXP_WIDTH + MANT_WIDTH + EXT_MANT_WIDTH:0]  result_vector;
  logic add_data_in_valid;
  logic add_data_in_ready;


  for (genvar i = 0; i < VEC_DIM; i = i + 1) begin : parallel_mult
    fp_cp_adder_v2 #(
        .MANT_WIDTH(MANT_WIDTH),
        .EXP_WIDTH(EXP_WIDTH),
        .EXT_MANT_WIDTH(EXT_MANT_WIDTH),
        .EXT_EXP_WIDTH(EXT_EXP_WIDTH)
    ) fp_vector_element_mult (
        .data_a (data_a_in[i]),
        .data_b (data_b_in[i]),
        .data_out(result_vector[i])
    );
  end

  join2 #() join_inst (
      .data_in_ready ({data_a_in_ready, data_b_in_ready}),
      .data_in_valid ({data_a_in_valid, data_b_in_valid}),
      .data_out_valid(add_data_in_valid),
      .data_out_ready(add_data_in_ready)
  );

  skid_buffer #(
      .DATA_WIDTH(VEC_DIM * (EXP_WIDTH + EXT_EXP_WIDTH + MANT_WIDTH + EXT_MANT_WIDTH + 1)) 
  ) register_slice (
      .clk           (clk),
      .rst           (rst),
      .data_in       (result_vector),
      .data_in_valid (add_data_in_valid),
      .data_in_ready (add_data_in_ready),
      .data_out      (data_out),
      .data_out_valid(data_out_valid),
      .data_out_ready(data_out_ready)
  );


endmodule
