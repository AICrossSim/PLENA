`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Vector Reduction Computation Module
Timing      : Sequential, Takes x cycles to compute the dot product
Description : This module includes vector reduction computations
            : 1. SUM, 2. MAX
            : As we are targeting for high dim vector reduction, which need to be decomposed into a series of instructions, we maximally utilize the instruction and read port width of the sram by considering sources together.

Status      : Under Development
*/


module fp_reduction_compute_unit #(
    // FP Data Format
    parameter EXP_WIDTH    = 4,
    parameter MANT_WIDTH   = 3,

    // Dimensions
    parameter VLEN      = 8,
    localparam VEC_DIM   = VLEN * 2,
    localparam LEVELS = $clog2(VEC_DIM),

    // Precision Control, for the vector core, currently focus solely on fixed data type width, left for future work.
    parameter ACC_EXT_EXP_WIDTH   = 0,
    parameter ACC_EXT_MANT_WIDTH  = 0,

    localparam OVERALL_MANT_EXT_BITS = LEVELS * ACC_EXT_MANT_WIDTH, 
    localparam OUT_MAN_WIDTH = OVERALL_MANT_EXT_BITS + MANT_WIDTH,    

    localparam OVERALL_EXP_EXT_BITS = LEVELS * ACC_EXT_EXP_WIDTH,
    localparam OUT_EXP_WIDTH  = OVERALL_EXP_EXT_BITS + EXP_WIDTH,

    localparam IN_WIDTH       = MANT_WIDTH + EXP_WIDTH + 1,
    localparam OUT_WIDTH      = OUT_MAN_WIDTH + OUT_EXP_WIDTH + 1

) (
    input logic clk,
    input logic rst,

    // Input vector

    input logic [VEC_DIM - 1:0] [MANT_WIDTH + EXP_WIDTH : 0] v_in,
    input logic v_in_valid,
    output logic v_in_ready,

    // Control
    input V_REDUCT_OP operation,

    // Output Vector
    output logic [VLEN - 1:0] [MANT_WIDTH + EXP_WIDTH : 0] v_out,
    output logic v_out_valid,
    input logic v_out_ready
);


//   initial begin
//     assert (VEC_DIM > 0);
//   end

  generate
      logic [OUT_WIDTH*VEC_DIM-1:0] data_storage [LEVELS:0];  // TODO: Need to be optimized, memory inefficient
      logic [OUT_WIDTH*VEC_DIM-1:0] sum  [LEVELS-1:0];
      logic valid[VEC_DIM-1:0];
      logic ready[VEC_DIM-1:0];

      // Generate adder for each layer
      for (genvar i = 0; i < LEVELS; i++) begin : level

        localparam LEVEL_IN_DIM = (VEC_DIM + ((1 << i) - 1)) >> i;     // Ceiling(VEC_DIM / 2^i)
        localparam LEVEL_IN_MAN_WIDTH   = MANT_WIDTH + i * ACC_EXT_MANT_WIDTH;
        localparam LEVEL_IN_EXP_WIDTH   = EXP_WIDTH + i * ACC_EXT_EXP_WIDTH;
        
        localparam LEVEL_OUT_DIM = (LEVEL_IN_DIM + 1) / 2;
        localparam LEVEL_OUT_MAN_WIDTH  = MANT_WIDTH + (i + 1) * ACC_EXT_MANT_WIDTH;
        localparam LEVEL_OUT_EXP_WIDTH  = EXP_WIDTH + (i + 1) * ACC_EXT_EXP_WIDTH;
        localparam LEVEL_OUT_WIDTH = LEVEL_OUT_MAN_WIDTH + LEVEL_OUT_EXP_WIDTH + 1;

        vector_reduce_layer #(
            .OVERALL_INPUT_WIDTH  (OUT_WIDTH*VEC_DIM),
            .LAYER_DIM(LEVEL_IN_DIM),
            .IN_MAN_WIDTH(LEVEL_IN_MAN_WIDTH),
            .IN_EXP_WIDTH(LEVEL_IN_EXP_WIDTH),
            .EXT_MANT_WIDTH(ACC_EXT_MANT_WIDTH),
            .EXT_EXP_WIDTH(ACC_EXT_EXP_WIDTH)
        ) vector_layer (
            .operation(operation),
            .data_in(data_storage[i]),
            .data_out(sum[i])
        );

        skid_buffer #(
            .DATA_WIDTH(LEVEL_OUT_DIM * LEVEL_OUT_WIDTH)
        ) register_slice (
            .clk           (clk),
            .rst           (!rst),                        // Inverted reset
            .data_in       (sum[i]),                      // flattened LEVEL_OUT_DIM * LEVEL_OUT_WIDTH
            .data_in_valid (valid[i]),
            .data_in_ready (ready[i]),
            .data_out      (data_storage[i+1]),
            .data_out_valid(valid[i+1]),
            .data_out_ready(ready[i+1])
        );
      end

      assign data_storage[0]= v_in;

      assign valid[0] = v_in_valid;
      assign v_in_ready = ready[0];

      assign v_out = data_storage[LEVELS][OUT_WIDTH-1:0];
      assign v_out_valid = valid[LEVELS];
      assign ready[LEVELS] = v_out_ready;

  endgenerate



endmodule