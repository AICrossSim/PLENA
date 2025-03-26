`timescale 1ns / 1ps

/*
Module      : Floating Point Adder Tree
Description : This module contains hierarchical adder tree for floating point numbers.

Input   d1  |   d12  |  d1234  Output
        d2  |   d34  |  x
        d3  |   x    |  x
        d4  |   x    |  x

*/

module fp_adder_tree #(
    parameter VEC_DIM       = 4,
    parameter IN_EXP_WIDTH  = 3,
    parameter IN_MAN_WIDTH  = 4,
    localparam IN_WIDTH     = IN_MAN_WIDTH + IN_EXP_WIDTH + 1,
    localparam EXT_BITS_PER_LAYER = 1 << IN_EXP_WIDTH,
    localparam OVERALL_EXT_BITS = $clog2(VEC_DIM) * EXT_BITS_PER_LAYER, 
    localparam OUT_MAN_WIDTH = OVERALL_EXT_BITS + IN_MAN_WIDTH,    // TODO: 
    localparam OUT_WIDTH = OUT_MAN_WIDTH + IN_EXP_WIDTH + 1
) (
    /* verilator lint_off UNUSEDSIGNAL */
    input  logic                 clk,
    input  logic                 rst,
    /* verilator lint_on UNUSEDSIGNAL */
    input  logic [VEC_DIM-1:0] [IN_WIDTH - 1 : 0] data_in,
    input  logic                 data_in_valid,
    output logic                 data_in_ready,
    output logic [OUT_WIDTH - 1 : 0] data_out,
    output logic                 data_out_valid,
    input  logic                 data_out_ready
);

  localparam LEVELS = $clog2(VEC_DIM);

  initial begin
    assert (VEC_DIM > 0);
  end

  generate
    if (LEVELS == 0) begin : gen_skip_adder_tree

      assign data_out = {{OVERALL_EXT_BITS{1'b0}}, data_in[0]};
      assign data_out_valid = data_in_valid;
      assign data_in_ready = data_out_ready;

    end else begin : gen_adder_tree

      // data & sum wires are oversized on purpose for vivado.
      logic [OUT_WIDTH*VEC_DIM-1:0] data [LEVELS:0];
      logic [OUT_WIDTH*VEC_DIM-1:0] sum  [LEVELS-1:0];
      logic valid[VEC_DIM-1:0];
      logic ready[VEC_DIM-1:0];

      // Generate adder for each layer
      for (genvar i = 0; i < LEVELS; i++) begin : level

        localparam LEVEL_IN_SIZE = (VEC_DIM + ((1 << i) - 1)) >> i;     // Ceiling(VEC_DIM / 2^i)
        localparam LEVEL_OUT_SIZE = (LEVEL_IN_SIZE + 1) / 2;
        localparam LEVEL_IN_MAN_WIDTH = IN_WIDTH + i * EXT_BITS_PER_LAYER;
        localparam LEVEL_OUT_WIDTH = LEVEL_IN_MAN_WIDTH + IN_EXP_WIDTH + 1;

        fp_adder_tree_layer #(
            .OVERALL_INPUT_WIDTH (OUT_WIDTH*VEC_DIM),
            .LAYER_DIM (LEVEL_IN_SIZE),
            .IN_MAN_WIDTH (LEVEL_IN_MAN_WIDTH),
            .IN_EXP_WIDTH (IN_EXP_WIDTH)
        ) full_precision_add_layer (
            .data_in  (data[i]),                          // flattened LEVEL_IN_SIZE * LEVEL_IN_WIDTH
            .data_out (sum[i])                            // flattened LEVEL_OUT_SIZE * LEVEL_OUT_WIDTH
        );

        skid_buffer #(
            .DATA_WIDTH(LEVEL_OUT_SIZE * LEVEL_OUT_WIDTH)
        ) register_slice (
            .clk           (clk),
            .rst           (rst),
            .data_in       (sum[i]),
            .data_in_valid (valid[i]),
            .data_in_ready (ready[i]),
            .data_out      (data[i+1]),
            .data_out_valid(valid[i+1]),
            .data_out_ready(ready[i+1])
        );

      end

      for (genvar i = 0; i < VEC_DIM; i++) begin : gen_input_assign
        assign data[0][(i+1)*IN_WIDTH-1 : i*IN_WIDTH] = data_in[i];
      end

      assign valid[0] = data_in_valid;
      assign data_in_ready = ready[0];

      assign data_out = data[LEVELS][OUT_WIDTH-1:0];
      assign data_out_valid = valid[LEVELS];
      assign ready[LEVELS] = data_out_ready;

    end
  endgenerate


endmodule
