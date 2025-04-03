`timescale 1ns / 1ps

/*
Module      : MX-FP Adder Tree
Description : This module is used to summing a vector of MX-FP data, this vector is composed of blocks of MX-FP data sharing the same scaling.
Timing      :
Input
        e1  | 
        e2  |
        e3  | -fp_adder_tree-> (e1234, s1)
        e4  |                               \
                                                mx_fp_unit_adder_tree -> (result_element, result_scale)
        e5  |                               /
        e6  | -fp_adder_tree-> (e5678, s2)
        e7  |
        e8  |
Status      : Passed Simple Tests
*/

module mx_fp_adder_tree #(
    // MX-FP Data Format
    parameter MXFP_EXP_WIDTH = 4,
    parameter MXFP_MANT_WIDTH = 3,
    parameter MXFP_SCALE_WIDTH = 8,
    
    // Precision Control
    parameter EXT_MANT_WIDTH_PER_LAYER = 1,
    parameter EXT_EXP_BITS_PER_LAYER = 1,

    // Dimension
    parameter COMP_DIM  = 8,
    parameter BLOCK_DIM = 4,
    localparam BLOCK_NUM        = COMP_DIM / BLOCK_DIM,
    localparam FP_ADD_LEVELS    = $clog2(BLOCK_DIM),
    localparam MXFP_LEVELS      = $clog2(COMP_DIM / BLOCK_DIM),

    // Output Width
    localparam OUTPUT_ELEMENT_MANT_WIDTH = FP_ADD_LEVELS * EXT_MANT_WIDTH_PER_LAYER + MXFP_MANT_WIDTH,
    localparam OUTPUT_ELEMENT_EXP_WIDTH  = FP_ADD_LEVELS * EXT_EXP_BITS_PER_LAYER + MXFP_EXP_WIDTH,
    localparam OUT_ELEMENT_WIDTH = OUTPUT_ELEMENT_MANT_WIDTH + OUTPUT_ELEMENT_EXP_WIDTH + 1
    
) (
    input  logic                 clk,
    input  logic                 rst,
    input  logic [BLOCK_NUM-1:0][BLOCK_DIM-1:0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] element_data_in,
    input  logic [BLOCK_NUM-1:0][MXFP_SCALE_WIDTH - 1 : 0] scale_data_in,
    input  logic                 data_in_valid,
    output logic                 data_in_ready,
    output logic [OUT_ELEMENT_WIDTH - 1 : 0] element_data_out,
    output logic [MXFP_SCALE_WIDTH - 1 : 0] scale_data_out,
    output logic                 data_out_valid,
    input  logic                 data_out_ready
);

    initial begin
        assert (COMP_DIM % BLOCK_DIM == 0) else $error("COMP_DIM must be divisible by BLOCK_DIM");
    end

    // Blockwise Adder Tree
    logic [BLOCK_NUM-1:0][OUT_ELEMENT_WIDTH - 1 : 0]    block_element_data_out;
    logic [BLOCK_NUM-1:0][MXFP_SCALE_WIDTH - 1 : 0]     block_scale_data_out;
    logic [BLOCK_NUM-1:0]                               block_data_out_valid;
    logic [BLOCK_NUM-1:0]                               block_data_in_ready;
    logic block_data_valid;
    logic block_data_ready;

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
                .data_in_valid(data_in_valid),
                .data_in_ready(data_in_ready),
                .data_out(block_element_data_out[i]),
                .data_out_valid(block_data_out_valid[i]),
                .data_out_ready(block_data_in_ready[i])
            );
        end
    endgenerate

    join_n #(
        .num (BLOCK_NUM)
    ) join_block_adder_tree (
        .clk(clk),
        .rst(rst),
        .data_in_valid(block_data_out_valid),
        .data_in_ready(block_data_in_ready),
        .data_out_valid(block_data_valid),
        .data_out_ready(block_data_ready)
    );


    // MX-FP Adder Tree
    mx_fp_unit_adder_tree #(
        .VEC_DIM (BLOCK_NUM),
        .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
        .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
        .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
        .EXT_MANT_WIDTH_PER_LAYER(EXT_MANT_WIDTH_PER_LAYER),
        .EXT_EXP_BITS_PER_LAYER(EXT_EXP_BITS_PER_LAYER)
    ) mx_fp_unit_adder_tree (
        .clk(clk),
        .rst(rst),
        .element_data_in(block_element_data_out),
        .scale_data_in(scale_data_in),
        .data_in_valid(block_data_valid),
        .data_in_ready(block_data_ready),
        .element_data_out(element_data_out),
        .scale_data_out(scale_data_out),
        .data_out_valid(data_out_valid),
        .data_out_ready(data_out_ready)
    );


endmodule