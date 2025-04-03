`timescale 1ns / 1ps

/*
Module      : MX-FP Configurable Precision Dot Product Unit (With Sign)
Timing      : Sequential, Takes 2 cycles to compute the dot product
Description : Dot Product of two FP vectors.
Status      : Under Testing
*/

module mx_fp_dot_product #(
    // MX-FP Data Format
    parameter MXFP_EXP_WIDTH    = 4,
    parameter MXFP_MANT_WIDTH   = 3,
    parameter MXFP_SCALE_WIDTH  = 8,

    // Dimension
    parameter COMP_DIM  = 8,
    parameter BLOCK_DIM = 4,

    // Precision Control
    parameter   PRODUCT_EXT_EXP_WIDTH   = 1,
    parameter   PRODUCT_EXT_MANT_WIDTH  = 4,
    parameter   ADD_EXT_EXP_WIDTH       = 1,
    parameter   ADD_EXT_MANT_WIDTH      = 4,

    // Product width
    localparam  PRODUCT_MAN_WIDTH = MXFP_MANT_WIDTH + PRODUCT_EXT_MANT_WIDTH, 
    localparam  PRODUCT_EXP_WIDTH = MXFP_EXP_WIDTH + PRODUCT_EXT_EXP_WIDTH,

    // Adder width
    localparam  ADD_MAN_WIDTH = PRODUCT_MAN_WIDTH + ADD_EXT_MANT_WIDTH * $clog2(BLOCK_DIM),
    localparam  ADD_EXP_WIDTH = PRODUCT_EXP_WIDTH + ADD_EXT_EXP_WIDTH * $clog2(BLOCK_DIM),

    localparam BLOCK_NUM        = COMP_DIM / BLOCK_DIM,

) (
    input clk,
    input rst,

    // input port A
    input  logic [COMP_DIM-1:0]     [(MXFP_MANT_WIDTH + PRODUCT_EXT_MANT_WIDTH):0]  element_a_in,
    input  logic [BLOCK_NUM-1:0]    [MXFP_SCALE_WIDTH - 1 : 0]                      scale_a_in,
    input                       data_a_in_valid,
    output                      data_a_in_ready,

    // input port B
    input  logic [COMP_DIM-1:0]     [(MXFP_MANT_WIDTH + PRODUCT_EXT_MANT_WIDTH):0]  element_b_in,
    input  logic [BLOCK_NUM-1:0]    [MXFP_SCALE_WIDTH - 1 : 0]                      scale_b_in,
    input                       data_b_in_valid,
    output                      data_b_in_ready,

    // output port
    output logic [(ADD_MAN_WIDTH + ADD_EXP_WIDTH) : 0]  element_out,
    output logic [(MXFP_SCALE_WIDTH - 1) : 0]           scale_out,
    output                       data_out_valid,
    input                        data_out_ready
);

    logic [COMP_DIM-1:0] [(PRODUCT_MAN_WIDTH + PRODUCT_EXP_WIDTH) : 0] element_product_vec;
    logic                     pv_valid;
    logic                     pv_ready;

    // element-wise mx-fp vector multiplication
    fp_vector_mult #(
        .VEC_DIM(COMP_DIM),
        .MANT_WIDTH(MXFP_MANT_WIDTH),
        .EXP_WIDTH(MXFP_EXP_WIDTH),
        .EXT_MANT_WIDTH(PRODUCT_EXT_MANT_WIDTH),
        .EXT_EXP_WIDTH (PRODUCT_EXT_EXP_WIDTH)
    ) fp_vector_mult_inst (
        .clk(clk),
        .rst(rst),
        .data_a_in(element_a_in),
        .data_a_in_valid(data_a_in_valid),
        .data_a_in_ready(data_a_in_ready),
        .data_b_in(element_b_in),
        .data_b_in_valid(data_b_in_valid),
        .data_b_in_ready(data_b_in_ready),
        .element_out(element_product_vec),
        .data_out_valid(pv_valid),
        .data_out_ready(pv_ready)
    );

    // scale addition, assuming the element-wise multiplication is done in the same cycle
    logic [BLOCK_NUM-1:0]    [MXFP_SCALE_WIDTH - 1 : 0] scale_product_vec;

    always @(posedge clk) begin
        for (int i = 0; i < BLOCK_NUM; i++) begin
            scale_product_vec[i] <= scale_a_in[i] + scale_b_in[i];
        end
    end

    // mx-fp adder tree
    mx_fp_adder_tree #(
        .MXFP_EXP_WIDTH(PRODUCT_EXP_WIDTH),
        .MXFP_MANT_WIDTH(PRODUCT_MAN_WIDTH),
        .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
        .EXT_MANT_WIDTH_PER_LAYER(ADD_EXT_MANT_WIDTH),
        .EXT_EXP_BITS_PER_LAYER(ADD_EXT_EXP_WIDTH),
        .COMP_DIM(COMP_DIM),
        .BLOCK_DIM(BLOCK_DIM)
    ) adder_tree (
        .clk(clk),
        .rst(rst),
        .element_data_in(element_product_vec),
        .scale_data_in(scale_product_vec), 
        .data_in_valid(pv_valid),
        .data_in_ready(pv_ready),
        .element_data_out(element_out),
        .scale_data_out(scale_out),
        .data_out_valid(data_out_valid),
        .data_out_ready(data_out_ready)
    );

endmodule
