`timescale 1ns / 1ps

/*
Module      : MX-FP Configurable Precision Adder Tree
Description : This module contains hierarchical adder tree for MX-FP numbers.
Timing      : $clog(LEVEL) cycles to produce the results, as each level consume a cycle.
Input   e1s1  |   e12s12  |  e1234s1234  Output
        e2s2  |   e34s34  |  x
        e3s3  |      x    |  x
        e4s4  |      x    |  x
Status      : Passed Simple Tests
*/

module mx_fp_unit_adder_tree #(
    parameter VEC_DIM       = 4,
    parameter MXFP_EXP_WIDTH = 4,
    parameter MXFP_MANT_WIDTH = 3,
    parameter MXFP_SCALE_WIDTH = 8,
    
    // Precision Control
    parameter EXT_MANT_WIDTH_PER_LAYER = 1,
    parameter EXT_EXP_BITS_PER_LAYER = 1,
    
    localparam LEVELS = $clog2(VEC_DIM),

    localparam OVERALL_MANT_EXT_BITS = LEVELS * EXT_MANT_WIDTH_PER_LAYER, 
    localparam OUT_MAN_WIDTH = OVERALL_MANT_EXT_BITS + MXFP_MANT_WIDTH,    

    localparam OVERALL_EXP_EXT_BITS = LEVELS * EXT_EXP_BITS_PER_LAYER,
    localparam OUT_EXP_WIDTH  = OVERALL_EXP_EXT_BITS + MXFP_EXP_WIDTH,

    localparam INPUT_ELEMENT_WIDTH       = MXFP_MANT_WIDTH + MXFP_EXP_WIDTH + 1,
    localparam OUTPUT_ELEMENT_WIDTH      = OUT_MAN_WIDTH + OUT_EXP_WIDTH + 1
) (
    /* verilator lint_off UNUSEDSIGNAL */
    input  logic                 clk,
    input  logic                 rst,
    /* verilator lint_on UNUSEDSIGNAL */
    input  logic [VEC_DIM-1:0] [INPUT_ELEMENT_WIDTH - 1 : 0]    element_data_in,
    input  logic [VEC_DIM-1:0] [MXFP_SCALE_WIDTH - 1 : 0]       scale_data_in,
    input  logic                 data_in_valid,
    output logic                 data_in_ready,
    output logic [OUTPUT_ELEMENT_WIDTH - 1 : 0]     element_data_out,
    output logic [MXFP_SCALE_WIDTH - 1 : 0]         scale_data_out,
    output logic                 data_out_valid,
    input  logic                 data_out_ready
);

  initial begin
    assert (VEC_DIM > 0);
  end

  generate
    if (LEVELS == 0) begin : gen_skip_adder_tree
        assign element_data_out = element_data_in[0];
        assign scale_data_out = scale_data_in[0];
        assign data_out_valid = data_in_valid;
        assign data_in_ready = data_out_ready;

    end else begin : gen_adder_tree

        // element_data_storage & sum wires are oversized on purpose for vivado.
        logic [OUTPUT_ELEMENT_WIDTH*VEC_DIM-1:0]    element_data_storage    [LEVELS:0];  // TODO: Need to be optimized, memory inefficient
        logic [MXFP_SCALE_WIDTH*VEC_DIM-1:0]        scale_data_storage      [LEVELS:0];  // TODO: Need to be optimized, memory inefficient
        logic [OUTPUT_ELEMENT_WIDTH*VEC_DIM-1:0]    element_sum             [LEVELS-1:0];
        logic [MXFP_SCALE_WIDTH*VEC_DIM-1:0]        scale_sum               [LEVELS-1:0];
        
        logic valid         [VEC_DIM-1:0];
        logic element_ready [VEC_DIM-1:0];
        logic scale_ready   [VEC_DIM-1:0];

        // Generate adder for each layer
        for (genvar i = 0; i < LEVELS; i++) begin : level
            // Parameters for controlling the precision of the element part data.
            localparam LEVEL_IN_DIM = (VEC_DIM + ((1 << i) - 1)) >> i;     // Ceiling(VEC_DIM / 2^i)
            localparam LEVEL_IN_MAN_WIDTH   = MXFP_MANT_WIDTH   + i * EXT_MANT_WIDTH_PER_LAYER;
            localparam LEVEL_IN_EXP_WIDTH   = MXFP_EXP_WIDTH    + i * EXT_EXP_BITS_PER_LAYER;
            
            localparam LEVEL_OUT_DIM        = (LEVEL_IN_DIM + 1) / 2;
            localparam LEVEL_OUT_MAN_WIDTH  = MXFP_MANT_WIDTH + (i + 1) * EXT_MANT_WIDTH_PER_LAYER;
            localparam LEVEL_OUT_EXP_WIDTH  = MXFP_EXP_WIDTH + (i + 1) * EXT_EXP_BITS_PER_LAYER;
            localparam LEVEL_OUT_WIDTH      = LEVEL_OUT_MAN_WIDTH + LEVEL_OUT_EXP_WIDTH + 1;

            mx_fp_unit_adder_tree_layer #(
                .ELEMENT_ARRAY_WIDTH  (OUTPUT_ELEMENT_WIDTH*VEC_DIM),
                .SCALE_ARRAY_WIDTH    (MXFP_SCALE_WIDTH*VEC_DIM),
                .LAYER_DIM            (LEVEL_IN_DIM),
                .MXFP_MANT_WIDTH      (LEVEL_IN_MAN_WIDTH),
                .MXFP_EXP_WIDTH       (LEVEL_IN_EXP_WIDTH),
                .MXFP_SCALE_WIDTH     (MXFP_SCALE_WIDTH),
                .EXT_MANT_WIDTH       (EXT_MANT_WIDTH_PER_LAYER),
                .EXT_EXP_WIDTH        (EXT_EXP_BITS_PER_LAYER)
            ) adder_layer (
                .element_data_in              (element_data_storage[i]),            // flattened LEVEL_IN_DIM * LEVEL_IN_WIDTH
                .scale_data_in                (scale_data_storage[i]),              // flattened LEVEL_IN_DIM * SCALE_WIDTH
                .element_data_out             (element_sum[i]),                     // flattened LEVEL_OUT_DIM * LEVEL_OUT_WIDTH
                .scale_data_out               (scale_sum[i])                        // flattened LEVEL_OUT_DIM * SCALE_WIDTH
            );

            skid_buffer #(
                .DATA_WIDTH(LEVEL_OUT_DIM * LEVEL_OUT_WIDTH)
            ) temp_store_element (
                .clk           (clk),
                .rst           (!rst),                        // Inverted reset
                .element_data_in       (element_sum[i]),      // flattened LEVEL_OUT_DIM * LEVEL_OUT_WIDTH
                .data_in_valid (valid[i]),
                .data_in_ready (element_ready[i]),
                .data_out      (element_data_storage[i+1]),
                .data_out_valid(valid[i+1]),
                .data_out_ready(element_ready[i+1])
            );

            skid_buffer #(
                .DATA_WIDTH(LEVEL_OUT_DIM * MXFP_SCALE_WIDTH)
            ) temp_store_scale (
                .clk           (clk),
                .rst           (!rst),                        // Inverted reset
                .data_in       (scale_sum[i]),                      // flattened LEVEL_OUT_DIM * SCALE_WIDTH
                .data_in_valid (valid[i]),
                .data_in_ready (scale_ready[i]),
                .data_out      (scale_data_storage[i+1]),
                .data_out_valid(valid[i+1]),
                .data_out_ready(scale_ready[i+1])
            );
        end

        for (genvar i = 0; i < VEC_DIM; i++) begin : gen_input_assign
            assign element_data_storage [0][(i+1)*INPUT_ELEMENT_WIDTH-1 : i*INPUT_ELEMENT_WIDTH] = element_data_in[i];
            assign scale_data_storage   [0][(i+1)*MXFP_SCALE_WIDTH-1 : i*MXFP_SCALE_WIDTH] = scale_data_in[i];
        end

        assign valid[0] = data_in_valid;
        assign data_in_ready = element_ready[0] & scale_ready[0];

        assign data_out = element_data_storage[LEVELS][OUTPUT_ELEMENT_WIDTH-1:0];
        assign data_out_valid = valid[LEVELS];
        assign element_ready[LEVELS] = data_out_ready;

        assign scale_data_out = scale_data_storage[LEVELS][MXFP_SCALE_WIDTH-1:0];
        assign scale_ready[LEVELS] = data_out_ready;

    end
  endgenerate


endmodule
