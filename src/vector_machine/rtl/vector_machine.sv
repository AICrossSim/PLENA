`timescale 1ns / 1ps
`include "operation.svh"
/*
Module      : Vector Machine Module
Timing      : Sequential, Takes x cycles to compute the dot product
Description : This module is the first version of the vector machine based on FP data type.
Status      : Under Testing
*/


module vector_machine #(
    // MX-FP Data Format
    parameter   MXFP_MANT_WIDTH   = 8,
    parameter   MXFP_EXP_WIDTH    = 4,
    parameter   MX_FP_SCALE_WIDTH = 8,

    // FP Data Format
    parameter   FP_EXP_WIDTH = 5,
    parameter   FP_MANT_WIDTH = 10

    // Dimensions
    parameter   VLEN              = 8,
    parameter   BLOCK_DIM         = 4,
    localparam  BLOCK_NUM         = VLEN / BLOCK_DIM,

    // Precision Control
    parameter   VE_EXT_EXP_WIDTH   = 0, // Extensions for vector elementwise compute unit. 
    parameter   VE_EXT_MANT_WIDTH  = 0,
    parameter   VR_EXT_EXP_WIDTH   = 0, // Extensions for vector reduction compute unit.
    parameter   VR_EXT_MANT_WIDTH  = 0,


    // Intermediate FP Control
    parameter   ROUND_FP_EN            = 0,
    parameter   ROUND_FP_EXP_WIDTH     = 4,
    parameter   ROUND_FP_MANT_WIDTH    = 3, 
    
) (
    input   logic clk,
    input   logic rst,

    // Control
    input   logic select_b_from_scalar,
    input   CUSTOM_ISA opcode,

    // Vector a
    input   logic [BLOCK_NUM-1:0] [BLOCK_DIM-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]    v_a_element,
    input   logic [BLOCK_NUM-1:0]        [MX_FP_SCALE_WIDTH-1:0]                            v_a_scale,
    input   logic                   v_a_valid,
    output  logic                   v_a_ready,

    // Vector b
    input   logic [BLOCK_NUM-1:0] [BLOCK_DIM-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]    v_b_element,
    input   logic [BLOCK_NUM-1:0]        [MX_FP_SCALE_WIDTH-1:0]                            v_b_scale,
    input   logic                   v_b_valid,
    output  logic                   v_b_ready,

    // Scalar Value
    input   logic [FP_EXP_WIDTH + FP_MANT_WIDTH] s_in,
    input   logic                   s_in_valid,
    output  logic                   s_in_ready,

    output  logic [FP_EXP_WIDTH + FP_MANT_WIDTH] s_out,
    output  logic                     s_out_valid,
    input   logic                     s_out_ready


    // Output
    output  logic [VLEN-1:0]             [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      v_out_element,
    output  logic [BLOCK_NUM-1:0]        [MX_FP_SCALE_WIDTH-1:0]                     v_out_scale,
    output  logic                     v_out_valid,
    input   logic                     v_out_ready
    
);

// MXFP to FP Conversion
logic [BLOCK_NUM-1:0] [BLOCK_DIM-1:0]  [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] converted_v_a;
logic [BLOCK_NUM-1:0] [BLOCK_DIM-1:0]  [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] converted_v_b;
logic [VLEN-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] prepared_v_a;
logic [VLEN-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] prepared_v_b;
logic [VLEN-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] unpacked_v_s;

logic prepared_v_a_ready, prepared_v_a_valid;
logic prepared_v_b_ready, prepared_v_b_valid;


generate;

    for (genvar i = 0; j < BLOCK_NUM; i = i + 1)begin
        mx_fp_2_fp_block #(
            .BLOCK_DIM(BLOCK_DIM),
            .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
            .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
            .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
            .FP_MANT_WIDTH(FP_MANT_WIDTH),
            .FP_EXP_WIDTH(FP_EXP_WIDTH)
        ) mxfp_fp_conversion_unit_a (
            .element_in(v_a_element[i]),
            .scale_in(v_a_scale[i]),
            .fp_out(converted_v_a[i])
        );
    end

    for (genvar j = 0; j < BLOCK_DIM; j = j + 1)begin
        mx_fp_2_fp_block #(
            .BLOCK_DIM(BLOCK_DIM),
            .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
            .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
            .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
            .FP_MANT_WIDTH(FP_MANT_WIDTH),
            .FP_EXP_WIDTH(FP_EXP_WIDTH)
        ) mxfp_fp_conversion_unit_b (
            .element_in(v_b_element[j]),
            .scale_in(v_b_scale[j]),
            .fp_out(converted_v_b[j])
        );
    end

    broadcast #(
        .DATA_WIDTH(FP_EXP_WIDTH + FP_MANT_WIDTH + 1)
        .BROADCAST_DIM(VLEN)
    ) broadcaset_scalar (
        .in_data(s_in),
        .out_data(unpacked_v_s)
    );


endgenerate

skid_buffer #(
    .DATAWIDTH(VLEN * (FP_EXP_WIDTH + FP_MANT_WIDTH + 1))
) v_a_buffer (
    .clk(clk),
    .rst(!rst),

    // Input
    .in_data(converted_v_a),
    .in_valid(v_a_valid),
    .in_ready(v_a_ready),

    // Output
    .out_data(prepared_v_a),
    .out_valid(prepared_v_a_valid),
    .out_ready(prepared_v_a_ready)
);

skid_buffer #(
    .DATAWIDTH(VLEN * (FP_EXP_WIDTH + FP_MANT_WIDTH + 1))
) v_b_buffer (
    .clk(clk),
    .rst(!rst),

    // Input
    .in_data(select_b_from_scalar ? unpacked_v_s : converted_v_b ),
    .in_valid(v_b_valid),
    .in_ready(v_b_ready),

    // Output
    .out_data(prepared_v_b),
    .out_valid(prepared_v_b_valid),
    .out_ready(prepared_v_b_ready)
);

logic element_v_in_a_valid, element_v_in_a_ready;
logic element_v_in_b_valid, element_v_in_b_ready;
logic element_v_out_valid, element_v_out_ready;
logic [VLEN-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] element_v_out;
ELEMENT_V_OPERAND element_opcode;


fp_elementwise_compute_unit #(
    .EXP_WIDTH(FP_EXP_WIDTH),
    .MANT_WIDTH(FP_MANT_WIDTH),
    .VLEN(VLEN)
) element_unit (
    .clk(clk),
    .rst(rst),
    .v_in_a(prepared_v_a),
    .v_in_a_valid(element_v_in_a_valid),
    .v_in_a_ready(element_v_in_a_ready),

    .v_in_b(prepared_v_b),
    .v_in_b_valid(element_v_in_b_valid),
    .v_in_b_ready(element_v_in_b_ready),

    .operation(element_opcode),
    .v_out(element_v_out),
    .v_out_valid(element_v_out_valid),
    .v_out_ready(element_v_out_ready)

);

logic red_v_in_valid, red_v_in_ready;
logic red_v_out_valid, red_v_out_ready;
logic [VLEN-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] red_v_out;
RED_V_OPERAND   red_opcode;


fp_reduction_compute_unit #(
    .EXP_WIDTH(FP_EXP_WIDTH),
    .MANT_WIDTH(FP_MANT_WIDTH),
    .VLEN(VLEN)
) reduction_unit (
    .clk(clk),
    .rst(rst),
    .v_in({prepared_v_a, prepared_v_b}),
    .v_in_valid(red_v_in_valid),
    .v_in_ready(red_v_in_ready),
    .operation(red_opcode),
    .v_out(red_v_out),
    .v_out_valid(red_v_out_valid),
    .v_out_ready(red_v_out_ready)
);


endmodule