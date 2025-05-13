`timescale 1ns / 1ps
`include "operation.svh"
`include "configuration.svh"

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
    parameter   ADDR_WIDTH  = 32,    // Vector write address

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
    

    // Vector a
    input   logic [BLOCK_NUM-1:0] [BLOCK_DIM-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]    v_a_element,
    input   logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                             v_a_scale,
    input   logic                   v_a_valid,
    output  logic                   v_a_ready,

    // Vector b
    input   logic [BLOCK_NUM-1:0] [BLOCK_DIM-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]    v_b_element,
    input   logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                             v_b_scale,
    input   logic                   v_b_valid,
    output  logic                   v_b_ready,

    // Scalar Value
    input   logic [FP_EXP_WIDTH + FP_MANT_WIDTH -1 : 0] s_in,
    input   logic                   s_in_valid,
    output  logic                   s_in_ready,

    output  logic [FP_EXP_WIDTH + FP_MANT_WIDTH - 1 : 0] s_out,
    output  logic                   s_out_valid,
    input   logic                   s_out_ready,


    // Output
    input   logic [ADDR_WIDTH - 1 : 0] result_waddr,
    input  logic result_waddr_update,

    output  logic [VLEN-1:0]             [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]     v_out_element,
    output  logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                     v_out_scale,
    output  logic                                                                   v_out_valid,
    input   logic                                                                   v_out_ready,

    output  logic [ADDR_WIDTH - 1: 0]                                               v_waddr,   
    output  logic                                                                   v_wreq
    
);

import pipeline_pkg::*;

typedef struct {
    logic [ADDR_WIDTH-1:0]             waddr;
    V_ELEMENT_OP                       ele_op;
    V_REDUCT_OP                        red_op;
} RECORDED_INFO_TYPE;

RECORDED_INFO_TYPE pipeline_compute_track [0:VECTOR_MAX_CYCLES-1];

// Vector Machine Control
logic result_waddr_ready;
logic recorded_broadcast_en;
logic [ADDR_WIDTH-1:0] recorded_v_waddr;

always_ff @(posedge clk or negedge rst) begin
    if (rst) begin
        for (int i = 0; i < VECTOR_MAX_CYCLES; i++) begin
            pipeline_compute_track[i] <= '{
                waddr  : '0,
                ele_op : STALL_V_ELEMENT,
                red_op : STALL_V_REDUCT
            };
        end
        recorded_broadcast_en <= 1'b0;
    end else begin
        // Set result waddr
        result_waddr_ready <= result_waddr_update; // The waddr is ready to be accessed in the next cycle after the result_waddr_update is activated.
        
        if (result_waddr_ready)begin
            recorded_v_waddr <= result_waddr;
        end

        if (element_v_control != STALL_V_ELEMENT) begin
            pipeline_compute_track[0] <= '{
                waddr  : result_waddr,
                ele_op : element_v_control,
                red_op : STALL_V_REDUCT
            };
            recorded_broadcast_en <= broadcast_fp2;
        end else if (reduct_v_control != STALL_V_REDUCT) begin
            pipeline_compute_track[0] <= '{
                waddr  : result_waddr,
                ele_op : STALL_V_ELEMENT,
                red_op : reduct_v_control
            };
            recorded_broadcast_en <= 1'b0;
        end else begin
            pipeline_compute_track[0] <= '{
                waddr  : result_waddr,
                ele_op : STALL_V_ELEMENT,
                red_op : STALL_V_REDUCT
            };
            recorded_broadcast_en <= 1'b0;
        end 

        // Shift the pipeline
        for (int i = 0; i < VECTOR_MAX_CYCLES - 1; i++) begin
            pipeline_compute_track[i + 1] <= pipeline_compute_track[i];
        end

    end

end


// MXFP to FP Conversion
logic [BLOCK_NUM-1:0] [BLOCK_DIM-1:0]  [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] converted_v_a;
logic [BLOCK_NUM-1:0] [BLOCK_DIM-1:0]  [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] converted_v_b;
logic [VLEN-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] prepared_v_a;
logic [VLEN-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] prepared_v_b;
logic [VLEN-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] unpacked_v_s;

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
    .rst(rst),

    // Input
    .data_in(converted_v_a),
    .data_in_valid(v_a_valid),
    .data_in_ready(v_a_ready),

    // Output
    .data_out(prepared_v_a),
    .data_out_valid(element_v_in_a_valid),
    .data_out_ready(element_v_in_a_ready)
);

skid_buffer #(
    .DATA_WIDTH(VLEN * (FP_EXP_WIDTH + FP_MANT_WIDTH + 1))
) v_b_buffer (
    .clk(clk),
    .rst(rst),

    // Input
    .data_in(broadcast_fp2 ? unpacked_v_s : converted_v_b ),
    .data_in_valid(v_b_valid),
    .data_in_ready(v_b_ready),

    // Output
    .data_out(prepared_v_b),
    .data_out_valid(element_v_in_b_valid),
    .data_out_ready(element_v_in_b_ready)
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

    .operation(pipeline_compute_track[2].ele_op),
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
    .operation(pipeline_compute_track[2].red_op),
    .v_out(red_v_out),
    .v_out_valid(red_v_out_valid),
    .v_out_ready(red_v_out_ready)
);

/*  Result Selection
    Note: Different vector operations can end and trigger write to the memory at different cycles,
    Here we assume all the vector operations on flight does not have data dependency and can be directly write to memory once it is completed.
    The pipeline control unit will in charge of removing possible data dependency by inserting stall cycles.
    It does not require to wait for the vector operations assigned before it to finish.
*/
logic [ADDR_WIDTH-1:0] stored_result_waddr;
assign element_v_out_ready = compute_result_ready;
always_comb begin
    if (
        pipeline_compute_track[VECTOR_BASIC_CYCLES - 1].ele_op == ADD_V_ELEMENT ||
        pipeline_compute_track[VECTOR_BASIC_CYCLES - 1].ele_op == SUB_V_ELEMENT ||
        pipeline_compute_track[VECTOR_BASIC_CYCLES - 1].ele_op == MUL_V_ELEMENT
    ) begin
        result_v_out            = element_v_out;
        compute_result_valid    = element_v_out_valid;
        stored_result_waddr     = pipeline_compute_track[VECTOR_BASIC_CYCLES-1].waddr;
    end else begin
        result_v_out            = 'b0;
        compute_result_valid    = 1'b0;
        stored_result_waddr     = 'b0;
    end
    // TODO add other non linear function stalled cycles.
    
end

always_comb begin
    if (rst) begin
        v_wreq      = 1'b0;
    end else begin
        if (compute_result_valid)begin
            v_wreq  = 1'b1;
            v_waddr = stored_result_waddr;
        end else begin
            v_wreq  = 1'b0;
            v_waddr = 'b0;
        end
    end
end

// Convert FP to MX-FP 2 cycles
logic [BLOCK_NUM-1:0] [BLOCK_DIM-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] result_v_out;
logic compute_result_valid, compute_result_ready;
logic [BLOCK_NUM-1:0] fp_mxfp_in_valid, fp_mxfp_in_ready;
logic [BLOCK_NUM-1:0] fp_mxfp_out_valid, fp_mxfp_out_ready;
logic [BLOCK_NUM-1:0] [BLOCK_DIM-1:0] [(MXFP_EXP_WIDTH + MXFP_MANT_WIDTH) : 0] mx_fp_element;
logic [BLOCK_NUM-1:0] [MXFP_SCALE_WIDTH-1:0] mx_fp_scale;

generate;
    split_n #(
        .N(BLOCK_NUM)
    ) v_split_i (
        .data_in_valid (compute_result_valid),
        .data_in_ready (compute_result_ready),
        .data_out_valid(fp_mxfp_in_valid),
        .data_out_ready(fp_mxfp_in_ready)
    );
    
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
            .data_in                (result_v_out[i]),
            .data_in_valid          (fp_mxfp_in_valid[i]),
            .data_in_ready          (fp_mxfp_in_ready[i]),
            .element_data_out       (mx_fp_element[i]),
            .scale_data_out         (mx_fp_scale[i]),
            .mx_fp_data_out_valid   (fp_mxfp_out_valid[i]),
            .mx_fp_data_out_ready   (fp_mxfp_out_ready[i])
        );
    end

    join_n #(
        .NUM_HANDSHAKES (BLOCK_NUM)
    ) join_v_element (
        .data_in_valid(fp_mxfp_out_valid),
        .data_in_ready(fp_mxfp_out_ready),
        .data_out_valid(v_out_valid),
        .data_out_ready(v_out_ready)
    );
endgenerate

assign v_out_element    = mx_fp_element;
assign v_out_scale      = mx_fp_scale;

endmodule