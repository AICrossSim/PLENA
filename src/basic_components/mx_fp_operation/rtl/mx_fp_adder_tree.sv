`timescale 1ns / 1ps

/*
Module      : MX-FP (convert to fp for intermediate computation) Adder Tree， outputs FP data.
Timing      : Sequential.
Description : This module is used to summing a vector of MX-FP data, this vector is composed of blocks of MX-FP data sharing the same scaling.
Input
        e1  | 
        e2  |
        e3  | -fp_adder_tree-> (e1234, s1)
        e4  |                               \
                                                convert to fp -> fp_adder_tree -> fp
        e5  |                               /
        e6  | -fp_adder_tree-> (e5678, s2)
        e7  |
        e8  |
Status      : Passed Simple Tests
*/

module mx_fp_adder_tree_fp_out #(
    // MX-FP Data Format
    parameter MXFP_EXP_WIDTH = 4,
    parameter MXFP_MANT_WIDTH = 3,
    parameter MXFP_SCALE_WIDTH = 8,
    
    // Precision Control
    parameter BLOCK_EXT_MANT_WIDTH_PER_LAYER = 1,
    parameter BLOCK_EXT_EXP_BITS_PER_LAYER = 1,

    parameter FP_EXT_MANT_WIDTH_PER_LAYER = 1,
    parameter FP_EXT_EXP_BITS_PER_LAYER = 1,

    // Dimension
    parameter   COMP_DIM  = 8,
    parameter   BLOCK_DIM = 4,
    localparam  BLOCK_NUM        = COMP_DIM / BLOCK_DIM,
    localparam  BLOCK_ADD_LEVELS    = $clog2(BLOCK_DIM),
    localparam  FP_ADD_LEVELS    = $clog2(BLOCK_NUM),

    // Output Width
    localparam OUTPUT_FP_MANT_WIDTH = BLOCK_ADD_LEVELS * BLOCK_EXT_MANT_WIDTH_PER_LAYER + FP_ADD_LEVELS * FP_EXT_MANT_WIDTH_PER_LAYER + MXFP_MANT_WIDTH,
    localparam OUTPUT_FP_EXP_WIDTH  = BLOCK_ADD_LEVELS * BLOCK_EXT_EXP_BITS_PER_LAYER  + FP_ADD_LEVELS * FP_EXT_EXP_BITS_PER_LAYER + MXFP_EXP_WIDTH,
    localparam OUT_FP_WIDTH = OUTPUT_FP_MANT_WIDTH + OUTPUT_FP_EXP_WIDTH + 1
    
) (
    input  logic                 clk,
    input  logic                 rst,
    input  logic [BLOCK_NUM-1:0][BLOCK_DIM-1:0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] element_data_in,
    input  logic [BLOCK_NUM-1:0][MXFP_SCALE_WIDTH - 1 : 0] scale_data_in,
    input  logic                 data_in_valid,
    output logic                 data_in_ready,
    output logic [OUT_FP_WIDTH - 1 : 0] fp_out,
    output logic                 data_out_valid,
    input  logic                 data_out_ready
);

    initial begin
        assert (COMP_DIM % BLOCK_DIM == 0) else $error("COMP_DIM must be divisible by BLOCK_DIM");
    end

    localparam BOUT_ELEMENT_WIDTH = BLOCK_ADD_LEVELS * (BLOCK_EXT_MANT_WIDTH_PER_LAYER + BLOCK_EXT_EXP_BITS_PER_LAYER) + MXFP_MANT_WIDTH + MXFP_EXP_WIDTH;
    // TODO: not decided yet, perhaps make it configurable?
    localparam FP_EXP_WIDTH = BLOCK_ADD_LEVELS * (BLOCK_EXT_EXP_BITS_PER_LAYER) + MXFP_EXP_WIDTH;
    localparam FP_MANT_WIDTH = BLOCK_ADD_LEVELS * (BLOCK_EXT_MANT_WIDTH_PER_LAYER) + MXFP_MANT_WIDTH;

    // Blockwise Adder Tree
    logic [BLOCK_NUM-1:0][BOUT_ELEMENT_WIDTH - 1 : 0]       block_element_data_out;
    logic [BLOCK_ADD_LEVELS-1:0][BLOCK_NUM-1:0][MXFP_SCALE_WIDTH - 1 : 0]         stored_block_scale_data;

    logic [BLOCK_NUM-1:0]                       block_data_in_valid, block_data_out_valid;
    logic [BLOCK_NUM-1:0]                       block_data_in_ready, block_data_out_ready;
    logic scale_storage_in_valid, scale_storage_in_ready;
    logic scale_storage_out_valid, scale_storage_out_ready;
    logic blockwise_addition_valid, blockwise_addition_ready;
    

    generate;
        for (genvar i = 0; i < BLOCK_NUM; i++) begin : block_adder_tree
            fp_adder_tree #(
                .VEC_DIM (BLOCK_DIM),
                .IN_EXP_WIDTH(MXFP_EXP_WIDTH),
                .IN_MAN_WIDTH(MXFP_MANT_WIDTH),
                .EXT_EXP_BITS_PER_LAYER(EXT_EXP_BITS_PER_LAYER),
                .EXT_MANT_WIDTH_PER_LAYER(EXT_MANT_WIDTH_PER_LAYER)
            ) fp_full_precision_add_tree (
                .clk(clk),
                .rst(rst),
                .data_in(element_data_in[i]),
                .data_in_valid(block_data_in_valid),
                .data_in_ready(block_data_in_ready[i]),
                .data_out(block_element_data_out[i]),
                .data_out_valid(block_data_out_valid[i]),
                .data_out_ready(block_data_out_ready[i])
            );
        end

        split_n #(
            .N(BLOCK_NUM + 1)
        ) split_block_signal(
            .data_in_valid(data_in_valid),
            .data_in_ready(data_in_ready),
            .data_out_valid({block_data_in_valid, scale_storage_in_valid}),
            .data_out_ready({block_data_in_ready, scale_storage_in_ready})
        );

        // Store the scale data
        fifo #(
            .DATA_WIDTH(BLOCK_NUM * MXFP_SCALE_WIDTH),
            .DEPTH(BLOCK_ADD_LEVELS)
        ) temp_store_scale (
            .clk           (clk),
            .rst           (!rst),                        // Inverted reset
            .data_in       (scale_data_in),                      // flattened LEVEL_OUT_DIM * SCALE_WIDTH
            .data_in_valid (scale_storage_in_valid),
            .data_in_ready (scale_storage_in_ready),
            .data_out      (stored_block_scale_data),
            .data_out_valid(scale_storage_out_ready),
            .data_out_ready(scale_storage_out_ready)
        );

    endgenerate

    join_n #(
        .num (BLOCK_NUM + 1)
    ) join_block_adder_tree (
        .clk(clk),
        .rst(rst),
        .data_in_valid({block_data_out_valid, scale_storage_valid}),
        .data_in_ready({block_data_out_ready, scale_storage_ready}),
        .data_out_valid(blockwise_addition_valid),
        .data_out_ready(blockwise_addition_ready)
    );



    // Convert to FP
    logic [BLOCK_NUM-1:0][FP_EXP_WIDTH + FP_MANT_WIDTH : 0] converted_fp_out;
    generate;
        for (genvar i = 0; i < BLOCK_NUM; i++) begin : mxfp_2_fp
            mx_fp_2_fp_unary #(
                .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH + BLOCK_ADD_LEVELS * BLOCK_EXT_EXP_BITS_PER_LAYER),
                .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH + BLOCK_ADD_LEVELS * BLOCK_EXT_MANT_WIDTH_PER_LAYER),
                .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
                .FP_EXP_WIDTH(FP_EXP_WIDTH),
                .FP_MANT_WIDTH(FP_MANT_WIDTH)
            ) mx_fp_2_fp_unary (
                .element_data_in(block_element_data_out[i]),
                .scale_data_in(scale_dstored_block_scale_dataata_in[i]),
                .fp_out(converted_fp_out)
            );
        end
    endgenerate


    // FP Adder Tree
    fp_adder_tree #(
        .VEC_DIM (BLOCK_NUM),
        .IN_EXP_WIDTH(FP_EXP_WIDTH),
        .IN_MAN_WIDTH(FP_MANT_WIDTH),
        .EXT_EXP_BITS_PER_LAYER(FP_EXT_EXP_BITS_PER_LAYER),
        .EXT_MANT_WIDTH_PER_LAYER(FP_EXT_MANT_WIDTH_PER_LAYER)
    ) fp_inter_block_adder_tree (
        .clk(clk),
        .rst(rst),
        .data_in(converted_fp_out),
        .data_in_valid(blockwise_addition_valid),
        .data_in_ready(blockwise_addition_ready),
        .data_out(fp_out),
        .data_out_valid(data_out_valid),
        .data_out_ready(data_out_ready)
    );

endmodule