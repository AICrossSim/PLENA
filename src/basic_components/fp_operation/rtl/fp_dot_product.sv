`timescale 1ns / 1ps

/*
Module      : Floating Point Configurable Precision Dot Product Unit (With Sign)
Timing      : Sequential, Takes 2 cycles to compute the dot product
Description : Dot Product of two FP vectors.
Status      : Passed Simple Tests
*/

module fp_dot_product #(
    parameter   MANT_WIDTH = 4,
    parameter   EXP_WIDTH = 3,
    parameter   VEC_DIM     = 8,

    // Precision Control
    parameter   PRODUCT_EXT_EXP_WIDTH = 1,
    parameter   PRODUCT_EXT_MANT_WIDTH = 4,
    parameter   ADD_EXT_EXP_WIDTH = 1,
    parameter   ADD_EXT_MANT_WIDTH = 4,

    // Product width
    localparam  PRODUCT_MAN_WIDTH = MANT_WIDTH + PRODUCT_EXT_MANT_WIDTH, 
    localparam  PRODUCT_EXP_WIDTH = EXP_WIDTH + PRODUCT_EXT_EXP_WIDTH,

    // Adder width
    localparam  ADD_MAN_WIDTH = PRODUCT_MAN_WIDTH + ADD_EXT_MANT_WIDTH * $clog2(VEC_DIM),
    localparam  ADD_EXP_WIDTH = PRODUCT_EXP_WIDTH + ADD_EXT_EXP_WIDTH * $clog2(VEC_DIM)

    // parameter OUT_WIDTH = IN_WIDTH + WEIGHT_WIDTH + $clog2(IN_SIZE) * 
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
    output logic [(ADD_MAN_WIDTH + ADD_EXP_WIDTH) : 0] data_out,
    output                       data_out_valid,
    input                        data_out_ready

);

    logic [VEC_DIM-1:0] [(PRODUCT_MAN_WIDTH + PRODUCT_EXP_WIDTH) : 0] product_vec;
    logic                     pv_valid;
    logic                     pv_ready;

    fp_vector_mult #(
        .VEC_DIM(VEC_DIM),
        .MANT_WIDTH(MANT_WIDTH),
        .EXP_WIDTH(EXP_WIDTH),
        .EXT_MANT_WIDTH(PRODUCT_EXT_MANT_WIDTH),
        .EXT_EXP_WIDTH (PRODUCT_EXT_EXP_WIDTH)
    ) fp_vector_mult_inst (
        .clk(clk),
        .rst(rst),
        .data_a_in(data_a_in),
        .data_a_in_valid(data_a_in_valid),
        .data_a_in_ready(data_a_in_ready),
        .data_b_in(data_b_in),
        .data_b_in_valid(data_b_in_valid),
        .data_b_in_ready(data_b_in_ready),
        .data_out(product_vec),
        .data_out_valid(pv_valid),
        .data_out_ready(pv_ready)
    );

    // sum the products
    // sum = sum(product_vec)
    fp_adder_tree #(
        .VEC_DIM (VEC_DIM),
        .IN_EXP_WIDTH(PRODUCT_EXP_WIDTH),
        .IN_MAN_WIDTH(PRODUCT_MAN_WIDTH),
        .EXT_EXP_BITS_PER_LAYER(ADD_EXT_EXP_WIDTH),
        .EXT_MANT_WIDTH_PER_LAYER(ADD_EXT_MANT_WIDTH)
    ) fp_full_precision_add_tree (
        .clk(clk),
        .rst(rst),
        .data_in(product_vec),
        .data_in_valid(pv_valid),
        .data_in_ready(pv_ready),
        .data_out(data_out),
        .data_out_valid(data_out_valid),
        .data_out_ready(data_out_ready)
    );

endmodule
