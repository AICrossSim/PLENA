`timescale 1ns / 1ps

/*
Module      : Floating Point Configurable Precision Matrix Vector Multiplication Unit (With Sign)
Timing      : Sequential, Takes x cycles to compute the dot product
Description : Matrix Vector Multiplication with the same Tile
            : The Rounding at FP level is performed at this module, keeping highest configurable precision.
*/

module fp_cp_mv #(
    // Assuming square matrix, this is the dimension of the matrix and the vector.
    parameter COMPUTE_DIM = 8, 
    parameter IN_MAN_WIDTH = 3,
    parameter IN_EXP_WIDTH = 4,

    // Precision Control
    parameter   PRODUCT_EXT_EXP_WIDTH = 1,
    parameter   PRODUCT_EXT_MANT_WIDTH = 4,
    parameter   ADD_EXT_EXP_WIDTH = 1,
    parameter   ADD_EXT_MANT_WIDTH = 4,

    // Output Rounding Control
    parameter OUTPUT_ROUNDING = 1,
    parameter OUT_MAN_WIDTH = 3,
    parameter OUT_EXP_WIDTH = 4

) (
    input logic clk,
    input logic rst,

    // Input matrix
    input  logic [COMPUTE_DIM * COMPUTE_DIM - 1 : 0] [IN_MAN_WIDTH + IN_EXP_WIDTH : 0] m_data,
    input  logic               m_data_valid,
    output logic               m_data_ready,

    // Input vector
    input  logic [COMPUTE_DIM - 1 : 0] [IN_MAN_WIDTH + IN_EXP_WIDTH : 0] v_data,
    input  logic               v_data_valid,
    output logic               v_data_ready,

    // Output Vector
    output logic [COMPUTE_DIM - 1 : 0] [OUT_MAN_WIDTH + OUT_EXP_WIDTH : 0] out_data,
    output logic                 out_data_valid,
    input  logic                 out_data_ready
);

  localparam ACC_EXP_WIDTH  = IN_EXP_WIDTH + PRODUCT_EXT_EXP_WIDTH + ADD_EXT_EXP_WIDTH * $clog2(COMPUTE_DIM);
  localparam ACC_MANT_WIDTH = IN_MAN_WIDTH + PRODUCT_EXT_MANT_WIDTH + ADD_EXT_MANT_WIDTH * $clog2(COMPUTE_DIM);

  initial begin
    if (OUTPUT_ROUNDING == 0) begin
      assert (ACC_EXP_WIDTH == OUT_EXP_WIDTH)
      else $fatal("OUT_EXP_WIDTH must be %d if OUTPUT_ROUNDING == 0", ACC_EXP_WIDTH);
      assert (ACC_MANT_WIDTH == OUT_MAN_WIDTH)
      else $fatal("OUT_MAN_WIDTH must be %d if OUTPUT_ROUNDING == 0", ACC_MANT_WIDTH);
    end
  end


  // -----
  // Wires
  // -----

  logic dot_product_ready;
  logic inputs_valid, inputs_ready;

  logic [COMPUTE_DIM-1:0] dot_product_valid;
  logic [COMPUTE_DIM-1:0] sync_ready;

  logic [COMPUTE_DIM - 1 : 0][ACC_EXP_WIDTH + ACC_MANT_WIDTH - 1:0] dot_product_data_out;
  logic [COMPUTE_DIM - 1 : 0][OUT_EXP_WIDTH + OUT_MAN_WIDTH - 1:0]  rounded_dot_product;


  // -----
  // Logic
  // -----

  // Need to synchronise x & y inputs
  assign inputs_ready = sync_ready[0];
  join2 sync_handshake (
      .data_in_valid ({m_data_valid, v_data_valid}),
      .data_in_ready ({m_data_ready, v_data_ready}),
      .data_out_valid(inputs_valid),
      .data_out_ready(inputs_ready)
  );


  // Instantiate COMPUTE_DIM number of dot products
  for (genvar i = 0; i < COMPUTE_DIM; i++) begin : multi_row

      fp_dot_product #(
        .MANT_WIDTH(IN_MAN_WIDTH),
        .EXP_WIDTH(IN_EXP_WIDTH),
        .VEC_DIM(COMPUTE_DIM),
        .PRODUCT_EXT_EXP_WIDTH(PRODUCT_EXT_EXP_WIDTH),
        .PRODUCT_EXT_MANT_WIDTH(PRODUCT_EXT_MANT_WIDTH),
        .ADD_EXT_EXP_WIDTH(ADD_EXT_EXP_WIDTH),
        .ADD_EXT_MANT_WIDTH(ADD_EXT_MANT_WIDTH),

      ) dot_product_inst (
          .clk           (clk),
          .rst           (rst),
          .data_a_in       (m_data[((i+1)*COMPUTE_DIM)-1 : i*M]),
          .data_a_in_valid (inputs_valid),
          .data_a_in_ready (sync_ready[i]),
          .data_b_in        (v_data),
          .data_b_in_valid  (inputs_valid),
          .data_b_in_ready  (), // same as data_a_in_ready
          .data_out      (dot_product_data_out[i]),
          .data_out_valid(dot_product_valid[i]),
          .data_out_ready(dot_product_ready)
      );

      if (OUTPUT_ROUNDING) begin : rounding
        // Rounded output
        fp_round #(
            .IN_WIDTH      (ACC_WIDTH),
            .IN_FRAC_WIDTH (ACC_FRAC_WIDTH),
            .OUT_WIDTH     (OUT_WIDTH),
            .OUT_FRAC_WIDTH(OUT_FRAC_WIDTH)
        ) round_inst (
            .data_in (dot_product_data_out[i]),
            .data_out(rounded_dot_product[i])
        );
        assign out_data[i] = rounded_dot_product[i];
      end else begin : no_rounding
        assign out_data[i] = dot_product_data_out[i];
      end
  end

  assign out_data_valid = dot_product_valid[0];
  assign dot_product_ready = out_data_ready;

endmodule
