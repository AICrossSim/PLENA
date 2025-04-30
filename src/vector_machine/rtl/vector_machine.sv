`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Vector Machine Module
Timing      : Sequential, Takes 4 cycles to compute every vector operation
Description : This module is the first version of the vector machine based on FP data type.
Status      : Under Testing
*/


module vector_machine #(
    // MX-FP Data Format
    parameter   MXFP_MANT_WIDTH   = 8,
    parameter   MXFP_EXP_WIDTH    = 4,
    parameter   MXFP_SCALE_WIDTH = 8,

    // FP Data Format
    parameter   FP_EXP_WIDTH = 5,
    parameter   FP_MANT_WIDTH = 10,

    // Dimensions
    parameter   VLEN              = 8,
    parameter   BLOCK_DIM         = 4,
    localparam  BLOCK_NUM         = VLEN / BLOCK_DIM,

    // Precision Control
    parameter   VE_EXT_EXP_WIDTH   = 0,     // Extensions for vector elementwise compute unit. 
    parameter   VE_EXT_MANT_WIDTH  = 0,
    parameter   VR_EXT_EXP_WIDTH   = 0,     // Extensions for vector reduction compute unit.
    parameter   VR_EXT_MANT_WIDTH  = 0,

    // Addr
    parameter   VECTOR_ADDR_WIDTH  = 32,    // Vector write address

    // Pipeline Control
    parameter   VECTOR_PIPLINE_DEPTH = 2,   // Pipeline depth for the vector machine

    // Intermediate FP Control
    parameter   ROUND_FP_EN            = 0,
    parameter   ROUND_FP_EXP_WIDTH     = 4,
    parameter   ROUND_FP_MANT_WIDTH    = 3
    
) (
    input   logic clk,
    input   logic rst,

    // Control
    input   logic broadcast_fp2,
    input   V_ELEMENT_OP element_v_control,
    input   V_REDUCT_OP  reduct_v_control,
    input   logic [VECTOR_ADDR_WIDTH - 1 : 0] target_vector_waddr,

    // Vector a
    input   logic [BLOCK_NUM-1:0] [BLOCK_DIM-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]    v_a_element,
    input   logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                            v_a_scale,
    input   logic                   v_a_valid,
    output  logic                   v_a_ready,

    // Vector b
    input   logic [BLOCK_NUM-1:0] [BLOCK_DIM-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]    v_b_element,
    input   logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                            v_b_scale,
    input   logic                   v_b_valid,
    output  logic                   v_b_ready,

    // Scalar Value
    input   logic [FP_EXP_WIDTH + FP_MANT_WIDTH -1 : 0] s_in,
    input   logic                   s_in_valid,
    output  logic                   s_in_ready,

    output  logic [FP_EXP_WIDTH + FP_MANT_WIDTH - 1 : 0] s_out,
    output  logic                     s_out_valid,
    input   logic                     s_out_ready,


    // Output
    output  logic [VLEN-1:0]             [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]     v_out_element,
    output  logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                     v_out_scale,
    output  logic                                                                   v_out_valid,
    output  logic [VECTOR_ADDR_WIDTH - 1: 0]                                        v_waddr,
    input   logic                                                                   v_out_ready
    
);


logic [VECTOR_ADDR_WIDTH - 1:0] pipeline_waddr_track [VECTOR_PIPLINE_DEPTH];
assign v_waddr = pipeline_waddr_track[VECTOR_PIPLINE_DEPTH - 1];

// Vector Machine Control
V_ELEMENT_OP p1_element_v_control;
V_REDUCT_OP p1_reduct_v_control;
logic select_result; // 0 for reduction, 1 for elementwise compute

always_ff @(posedge clk or negedge rst) begin
    if (!rst) begin
        p1_element_v_control    <= STALL_V_ELEMENT;
        p1_reduct_v_control     <= STALL_V_REDUCT;
        for (int i = 0; i < VECTOR_PIPLINE_DEPTH; i = i + 1) begin
            pipeline_waddr_track[i] <= {VECTOR_ADDR_WIDTH{1'b0}};
        end
    end else begin
        p1_element_v_control    <= element_v_control;
        p1_reduct_v_control     <= reduct_v_control;
        pipeline_waddr_track[0] <= target_vector_waddr;
        for (int i = 1; i < VECTOR_PIPLINE_DEPTH; i = i + 1) begin
            pipeline_waddr_track[i] <= pipeline_waddr_track[i - 1];
        end
    end

    if (p1_element_v_control != STALL_V_ELEMENT) begin
        select_result <= 1'b1;
    end else if (p1_reduct_v_control != STALL_V_REDUCT) begin
        select_result <= 1'b0;
    end else begin
        select_result <= 1'b0;
    end

end


// MXFP to FP Conversion
logic [BLOCK_NUM-1:0] [BLOCK_DIM-1:0]  [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] converted_v_a;
logic [BLOCK_NUM-1:0] [BLOCK_DIM-1:0]  [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] converted_v_b;
logic [VLEN-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] prepared_v_a;
logic [VLEN-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] prepared_v_b;
logic [VLEN-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] unpacked_v_s;

logic prepared_v_a_ready, prepared_v_a_valid;
logic prepared_v_b_ready, prepared_v_b_valid;

// TODO : Not sure if this is correct
assign s_in_ready = v_b_ready;

generate;
    for (genvar i = 0; i < BLOCK_NUM; i = i + 1)begin
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
        .DATA_WIDTH(FP_EXP_WIDTH + FP_MANT_WIDTH + 1),
        .BROADCAST_DIM(VLEN)
    ) broadcaset_scalar (
        .in_data(s_in),
        .out_data(unpacked_v_s)
    );

endgenerate

skid_buffer #(
    .DATA_WIDTH(VLEN * (FP_EXP_WIDTH + FP_MANT_WIDTH + 1))
) v_a_buffer (
    .clk(clk),
    .rst(!rst),

    // Input
    .data_in(converted_v_a),
    .data_in_valid(v_a_valid),
    .data_in_ready(v_a_ready),

    // Output
    .data_out(prepared_v_a),
    .data_out_valid(prepared_v_a_valid),
    .data_out_ready(prepared_v_a_ready)
);

skid_buffer #(
    .DATA_WIDTH(VLEN * (FP_EXP_WIDTH + FP_MANT_WIDTH + 1))
) v_b_buffer (
    .clk(clk),
    .rst(!rst),

    // Input
    .data_in(broadcast_fp2 ? unpacked_v_s : converted_v_b ),
    .data_in_valid(v_b_valid),
    .data_in_ready(v_b_ready),

    // Output
    .data_out(prepared_v_b),
    .data_out_valid(prepared_v_b_valid),
    .data_out_ready(prepared_v_b_ready)
);



// Elementwise Compute Unit
logic element_v_in_a_valid, element_v_in_a_ready;
logic element_v_in_b_valid, element_v_in_b_ready;
logic element_v_out_valid, element_v_out_ready;
logic [VLEN-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] element_v_out;


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

    .operation(element_v_control),
    .v_out(element_v_out),
    .v_out_valid(element_v_out_valid),
    .v_out_ready(element_v_out_ready)

);


// Reduction Compute Unit
logic red_v_in_valid, red_v_in_ready;
logic red_v_out_valid, red_v_out_ready;
logic [VLEN-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] red_v_out;

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
    .operation(reduct_v_control),
    .v_out(red_v_out),
    .v_out_valid(red_v_out_valid),
    .v_out_ready(red_v_out_ready)
);


// Convert FP to MX-FP 2 cycles
logic [VLEN-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] result_v_out;
assign result_v_out = select_result ? element_v_out : red_v_out;
generate;
    for (genvar i = 0; i < BLOCK_NUM; i = i + 1)begin
        fp_2_mx_fp_block #(
            .BLOCK_DIM(BLOCK_DIM),
            .FP_MANT_WIDTH(FP_MANT_WIDTH),
            .FP_EXP_WIDTH(FP_EXP_WIDTH),
            .MX_FP_MANT_WIDTH(MXFP_MANT_WIDTH),
            .MX_FP_EXP_WIDTH(MXFP_EXP_WIDTH),
            .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH)
        ) fp_mxfp_conversion_unit (
            .clk(clk),
            .rst(rst),
            .data_in(result_v_out[i]),
            .data_in_valid(element_v_out_valid),
            .data_in_ready(element_v_out_ready),

            .element_data_out(v_out_element[i]),
            .scale_data_out(v_out_scale[i]),
            .mx_fp_data_out_valid(v_out_valid),
            .mx_fp_data_out_ready(v_out_ready)
        );
    end
endgenerate


endmodule