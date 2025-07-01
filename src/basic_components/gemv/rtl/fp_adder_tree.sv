`timescale 1ns / 1ps

/*
Module      : Floating Point Adder Tree
Description : This module contains hierarchical adder tree for floating point numbers.
Timing      : $clog(LEVEL) cycles to produce the results, as each level consume a cycle.
Input   d1  |   d12  |  d1234  Output
        d2  |   d34  |  x
        d3  |   x    |  x
        d4  |   x    |  x
Status      : Passed Simple Tests
*/

module fp_adder_tree #(
    parameter VEC_DIM       = 4,
    parameter IN_EXP_WIDTH  = 3,
    parameter IN_MAN_WIDTH  = 4,
    
    // Precision Control
    parameter EXT_MANT_WIDTH_PER_LAYER = 0,
    parameter EXT_EXP_BITS_PER_LAYER = 0,
    
    localparam LEVELS = $clog2(VEC_DIM),

    localparam OVERALL_MANT_EXT_BITS = LEVELS * EXT_MANT_WIDTH_PER_LAYER, 
    localparam OUT_MAN_WIDTH = OVERALL_MANT_EXT_BITS + IN_MAN_WIDTH,    

    localparam OVERALL_EXP_EXT_BITS = LEVELS * EXT_EXP_BITS_PER_LAYER,
    localparam OUT_EXP_WIDTH  = OVERALL_EXP_EXT_BITS + IN_EXP_WIDTH,

    localparam IN_WIDTH       = IN_MAN_WIDTH + IN_EXP_WIDTH + 1,
    localparam OUT_WIDTH      = OUT_MAN_WIDTH + OUT_EXP_WIDTH + 1
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

  initial begin
    assert (VEC_DIM > 0);
  end

  generate
    if (LEVELS == 0) begin : gen_skip_adder_tree

      assign data_out = {{OVERALL_MANT_EXT_BITS{1'b0}}, data_in[0]};
      assign data_out_valid = data_in_valid;
      assign data_in_ready = data_out_ready;

    end else begin : gen_adder_tree

      // data_storage & sum wires are oversized on purpose for vivado.
      logic [OUT_WIDTH*VEC_DIM-1:0] data_storage [LEVELS:0];  // TODO: Need to be optimized, memory inefficient
      logic [OUT_WIDTH*VEC_DIM-1:0] sum  [LEVELS-1:0];
      logic valid[VEC_DIM-1:0];
      logic ready[VEC_DIM-1:0];

      // Generate adder for each layer
      for (genvar i = 0; i < LEVELS; i++) begin : level

        localparam LEVEL_IN_DIM = (VEC_DIM + ((1 << i) - 1)) >> i;     // Ceiling(VEC_DIM / 2^i)
        localparam LEVEL_IN_MAN_WIDTH   = IN_MAN_WIDTH + i * EXT_MANT_WIDTH_PER_LAYER;
        localparam LEVEL_IN_EXP_WIDTH   = IN_EXP_WIDTH + i * EXT_EXP_BITS_PER_LAYER;
        
        localparam LEVEL_OUT_DIM = (LEVEL_IN_DIM + 1) / 2;
        localparam LEVEL_OUT_MAN_WIDTH  = IN_MAN_WIDTH + (i + 1) * EXT_MANT_WIDTH_PER_LAYER;
        localparam LEVEL_OUT_EXP_WIDTH  = IN_EXP_WIDTH + (i + 1) * EXT_EXP_BITS_PER_LAYER;
        localparam LEVEL_OUT_WIDTH = LEVEL_OUT_MAN_WIDTH + LEVEL_OUT_EXP_WIDTH + 1;

        fp_adder_tree_layer #(
            .OVERALL_INPUT_WIDTH  (OUT_WIDTH*VEC_DIM),
            .LAYER_DIM            (LEVEL_IN_DIM),
            .IN_MAN_WIDTH         (LEVEL_IN_MAN_WIDTH),
            .IN_EXP_WIDTH         (LEVEL_IN_EXP_WIDTH),
            .EXT_MANT_WIDTH        (EXT_MANT_WIDTH_PER_LAYER),
            .EXT_EXP_WIDTH         (EXT_EXP_BITS_PER_LAYER)
        ) full_precision_add_layer (
            .data_in              (data_storage[i]),                          // flattened LEVEL_IN_DIM * LEVEL_IN_WIDTH
            .data_out             (sum[i])                                    // flattened LEVEL_OUT_DIM * LEVEL_OUT_WIDTH
        );

        skid_buffer #(
            .DATA_WIDTH(LEVEL_OUT_DIM * LEVEL_OUT_WIDTH)
        ) register_slice (
            .clk           (clk),
            .rst           (rst),                        // Inverted reset
            .data_in       (sum[i][LEVEL_OUT_DIM * LEVEL_OUT_WIDTH - 1 : 0]),                      // flattened LEVEL_OUT_DIM * LEVEL_OUT_WIDTH
            .data_in_valid (valid[i]),
            .data_in_ready (ready[i]),
            .data_out      (data_storage[i+1][LEVEL_OUT_DIM * LEVEL_OUT_WIDTH - 1 : 0]),
            .data_out_valid(valid[i+1]),
            .data_out_ready(ready[i+1])
        );
      end


      assign data_storage[0]= data_in;


      assign valid[0] = data_in_valid;
      assign data_in_ready = ready[0];

      assign data_out = data_storage[LEVELS][OUT_WIDTH-1:0];
      assign data_out_valid = valid[LEVELS];
      assign ready[LEVELS] = data_out_ready;

    end
  endgenerate


endmodule
