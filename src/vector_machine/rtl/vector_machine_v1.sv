`timescale 1ns / 1ps
`include "operation.svh"
`include "configuration.svh"
`include "precision.svh"

/*
Module      : Vector Machine Module V1
Timing      : Sequential
Description : This module is the first version of the vector machine based on FP data type.
            : It accepts data in MX-FP format and converts it to FP format for computation, converting back to MX-FP format for output.
Status      : Passed Logical Tests
*/


module vector_machine_v1 import precision_pkg::*; import configuration_pkg::*; #(
    localparam  BLOCK_NUM           = VLEN / BLOCK_DIM,
    localparam   ADDR_WIDTH         = ON_CHIP_ADDR_WIDTH,    // Vector write address
    parameter FP_EXP_WIDTH         = 8,
    parameter FP_MANT_WIDTH        = 7,
    parameter MXFP_MANT_WIDTH       = HIGH_MXFP_MANT_WIDTH,
    parameter MXFP_EXP_WIDTH        = HIGH_MXFP_EXP_WIDTH
) (
    input   logic clk,
    input   logic rst,

    // Control
    input   logic           broadcast_fp2,
    input   V_ELEMENT_OP    element_v_control,
    input   V_REDUCT_OP     reduct_v_control,
    output  logic           in_preparation_stage,

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
    input   logic [FP_OPERAND_WIDTH - 1 : 0]        s_wtarget,


    // Output
    input   logic [ADDR_WIDTH - 1 : 0] result_waddr,
    input   logic result_waddr_update,

    output  logic [VLEN-1:0]             [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]     v_out_element,
    output  logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                     v_out_scale,
    output  logic                                                                   v_out_valid,
    input   logic                                                                   v_out_ready,

    output  logic [ADDR_WIDTH - 1: 0]                                               v_waddr,   
    output  logic                                                                   v_wreq,

    output  logic [FP_EXP_WIDTH + FP_MANT_WIDTH - 1 : 0]                            s_out,
    output  logic                                                                   s_out_valid,
    input   logic                                                                   s_out_ready,
    output  logic  [FP_OPERAND_WIDTH - 1 : 0]                                       s_out_rd
    
);

import pipeline_pkg::*;

typedef struct {
    logic [ADDR_WIDTH-1:0]             waddr;
    V_ELEMENT_OP                       ele_op;
    V_REDUCT_OP                        red_op;
} RECORDED_INFO_TYPE;

RECORDED_INFO_TYPE pipeline_compute_track [0:VECTOR_LONGEST_OPERATE_CYCLES-1];

// Vector Machine Control
logic recorded_broadcast_en;
V_ELEMENT_OP recorded_element_v_control;
V_REDUCT_OP  recorded_reduct_v_control;
logic [FP_OPERAND_WIDTH - 1:0] recorded_s_wtarget;
logic [ADDR_WIDTH - 1:0] recorded_result_waddr;

// Loaded Vector Control Flow
logic v_port_a_valid, v_port_a_ready;
logic v_port_b_valid, v_port_b_ready;


// Data Preparation Stage
logic complete_element_prepare, complete_reduct_prepare;
logic next_preparation_stage;

logic [BLOCK_NUM-1:0] [BLOCK_DIM-1:0]  [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] converted_v_a;
logic [BLOCK_NUM-1:0] [BLOCK_DIM-1:0]  [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] converted_v_b;
logic [VLEN-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] prepared_v_a;
logic [VLEN-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] prepared_v_b;
logic [VLEN-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] unpacked_v_s;

logic red_v_in_a_valid, red_v_in_a_ready;
logic red_v_in_b_valid, red_v_in_b_ready;
logic red_v_in_valid, red_v_in_ready;
logic red_v_out_valid, red_v_out_ready;
logic s_acc_in_valid, s_acc_in_ready;
logic [FP_EXP_WIDTH + FP_MANT_WIDTH : 0] s_acc_in;
logic [VLEN-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] red_v_out;

logic element_v_in_a_valid, element_v_in_a_ready;
logic element_v_in_b_valid, element_v_in_b_ready;
logic element_v_out_valid, element_v_out_ready;
logic [VLEN-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] element_v_out;

logic [BLOCK_NUM-1:0] [BLOCK_DIM-1:0] [(FP_EXP_WIDTH + FP_MANT_WIDTH) : 0] result_v_out;
logic compute_result_valid, compute_result_ready;
logic [BLOCK_NUM-1:0] fp_mxfp_in_valid, fp_mxfp_in_ready;
logic [BLOCK_NUM-1:0] fp_mxfp_out_valid, fp_mxfp_out_ready;
logic [BLOCK_NUM-1:0] [BLOCK_DIM-1:0] [(MXFP_EXP_WIDTH + MXFP_MANT_WIDTH) : 0] mx_fp_element;
logic [BLOCK_NUM-1:0] [MXFP_SCALE_WIDTH-1:0] mx_fp_scale;

always_ff @(posedge clk) begin
    if (rst) begin
        for (int i = 0; i < VECTOR_LONGEST_OPERATE_CYCLES; i++) begin
            pipeline_compute_track[i] <= '{
                waddr  : '0,
                ele_op : STALL_V_ELEMENT,
                red_op : STALL_V_REDUCT
            };
        end
        recorded_broadcast_en <= 1'b0;
        in_preparation_stage  <= 1'b0;
    end else begin
        // Set result waddr

        if (result_waddr_update) begin
            recorded_result_waddr <= result_waddr;
        end

        if (!in_preparation_stage & (element_v_control != STALL_V_ELEMENT || reduct_v_control != STALL_V_REDUCT)) begin
            recorded_element_v_control  <= element_v_control;
            recorded_reduct_v_control   <= reduct_v_control;
            recorded_broadcast_en       <= broadcast_fp2;
            recorded_s_wtarget          <= s_wtarget;
        end

        if ((recorded_element_v_control != STALL_V_ELEMENT) & complete_element_prepare) begin
            pipeline_compute_track[0] <= '{
                waddr  : recorded_result_waddr,
                ele_op : recorded_element_v_control,
                red_op : recorded_reduct_v_control
            };
        end else if ((recorded_reduct_v_control != STALL_V_REDUCT) & complete_reduct_prepare) begin
            pipeline_compute_track[0] <= '{
                waddr  : {{(ADDR_WIDTH - FP_OPERAND_WIDTH){1'b0}} , recorded_s_wtarget},
                ele_op : recorded_element_v_control,
                red_op : recorded_reduct_v_control
            };    
        end else begin
            pipeline_compute_track[0] <= '{
                waddr  : 'b0,
                ele_op : STALL_V_ELEMENT,
                red_op : STALL_V_REDUCT
            };
        end

        // Shift the pipeline
        for (int i = 0; i < VECTOR_LONGEST_OPERATE_CYCLES - 1; i++) begin
            pipeline_compute_track[i + 1] <= pipeline_compute_track[i];
        end

        in_preparation_stage <= next_preparation_stage;

    end
end

always_comb begin
    if (rst) begin
        next_preparation_stage = 1'b0;
        complete_element_prepare = 1'b0;
        complete_reduct_prepare = 1'b0;
    end else begin
        if (!in_preparation_stage & (element_v_control != STALL_V_ELEMENT || reduct_v_control != STALL_V_REDUCT)) begin
            next_preparation_stage = 1'b1;
        end else if (complete_element_prepare || complete_reduct_prepare) begin
            next_preparation_stage = 1'b0;
        end else if (in_preparation_stage) begin
            next_preparation_stage = 1'b1;
        end

        if (((recorded_element_v_control != STALL_V_ELEMENT) & !recorded_broadcast_en & v_port_a_valid & v_port_b_valid) || ((recorded_element_v_control != STALL_V_ELEMENT) & recorded_broadcast_en & v_port_a_valid)) begin
            complete_element_prepare    = 1'b1;
            complete_reduct_prepare     = 1'b0;
        end else if (recorded_element_v_control == LD_V_ELEMENT & recorded_broadcast_en & v_port_b_valid) begin
            complete_element_prepare    = 1'b1;
            complete_reduct_prepare     = 1'b0;
        end else if ((recorded_reduct_v_control != STALL_V_REDUCT) & v_port_a_valid & v_port_b_valid & s_acc_in_valid) begin
            complete_element_prepare    = 1'b0;
            complete_reduct_prepare     = 1'b1;
        end else begin
            complete_element_prepare    = 1'b0;
            complete_reduct_prepare     = 1'b0;
        end
    end
end

// MXFP to FP Conversion
assign s_in_ready = v_b_ready;
generate;
    for (genvar i = 0; i < BLOCK_NUM; i = i + 1)begin
        mx_fp_2_fp_block #(
            .BLOCK_DIM          (BLOCK_DIM),
            .MXFP_MANT_WIDTH    (MXFP_MANT_WIDTH),
            .MXFP_EXP_WIDTH     (MXFP_EXP_WIDTH),
            .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH),
            .FP_MANT_WIDTH      (FP_MANT_WIDTH),
            .FP_EXP_WIDTH       (FP_EXP_WIDTH)
        ) mxfp_fp_conversion_unit_a (
            .element_in(v_a_element[i]),
            .scale_in(v_a_scale[i]),
            .fp_out(converted_v_a[i])
        );
    end

    for (genvar j = 0; j < BLOCK_NUM; j = j + 1)begin
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

// Vector Port A Storage
skid_buffer #(
    .DATA_WIDTH(VLEN * (FP_EXP_WIDTH + FP_MANT_WIDTH + 1))
) v_a_buffer (
    .clk(clk),
    .rst(rst),

    // Input
    .data_in        (converted_v_a),
    .data_in_valid  (v_a_valid),
    .data_in_ready  (v_a_ready),

    // Output
    .data_out       (prepared_v_a),
    .data_out_valid (v_port_a_valid),
    .data_out_ready (v_port_a_ready)
);

// Vector Port B Storage
skid_buffer #(
    .DATA_WIDTH(VLEN * (FP_EXP_WIDTH + FP_MANT_WIDTH + 1))
) v_b_buffer (
    .clk(clk),
    .rst(rst),

    // Input
    .data_in        (recorded_broadcast_en ? unpacked_v_s : converted_v_b ),
    .data_in_valid  (recorded_broadcast_en ? s_in_valid : v_b_valid),
    .data_in_ready  (v_b_ready),

    // Output
    .data_out       (prepared_v_b),
    .data_out_valid (v_port_b_valid),
    .data_out_ready (v_port_b_ready)
);

// Scalar Port Storage (Solely used for Reduction Operation)
skid_buffer #(
    .DATA_WIDTH(FP_EXP_WIDTH + FP_MANT_WIDTH + 1)
) s_in_buffer (
    .clk(clk),
    .rst(rst),

    // Input
    .data_in        (s_in),
    .data_in_valid  (recorded_reduct_v_control != STALL_V_REDUCT ? s_in_valid : 1'b0),
    .data_in_ready  (), // Not used

    // Output
    .data_out       (s_acc_in),
    .data_out_valid (s_acc_in_valid),
    .data_out_ready (s_acc_in_ready)
);
 


// Assuming the recorded_reduct_v_control and recorded_element_v_control can not have operation at the same time.
always_comb begin
    if (recorded_element_v_control != STALL_V_ELEMENT & recorded_element_v_control != LD_V_ELEMENT) begin
        element_v_in_a_valid = v_port_a_valid;
        element_v_in_b_valid = v_port_b_valid;
        red_v_in_a_valid     = 1'b0;
        red_v_in_b_valid     = 1'b0;
        v_port_a_ready       = element_v_in_a_ready;
        v_port_b_ready       = element_v_in_b_ready;
    end else if (recorded_reduct_v_control != STALL_V_REDUCT) begin
        element_v_in_a_valid = 1'b0;
        element_v_in_b_valid = 1'b0;
        red_v_in_a_valid     = v_port_a_valid;
        red_v_in_b_valid     = v_port_b_valid;        
        v_port_a_ready       = red_v_in_a_ready;
        v_port_b_ready       = red_v_in_b_ready;
    end else begin
        element_v_in_a_valid = 1'b0;
        element_v_in_b_valid = 1'b0;
        red_v_in_a_valid     = 1'b0;
        red_v_in_b_valid     = 1'b0;
        v_port_a_ready       = 1'b1;
        v_port_b_ready       = 1'b1;
    end
end

//----------------------------//
// Elementwise Compute Unit
//----------------------------//

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

    .operation(recorded_element_v_control),
    .v_out(element_v_out),
    .v_out_valid(element_v_out_valid),
    .v_out_ready(element_v_out_ready)
);


/*  Elementwise Result Selection
    Note: Different vector operations can end and trigger write to the memory at different cycles,
    Here we assume all the vector operations on flight does not have data dependency and can be directly write to memory once it is completed.
    The pipeline control unit will in charge of removing possible data dependency by inserting stall cycles.
    It does not require to wait for the vector operations assigned before it to finish.
    TODO: add other non linear function result selection here.
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
    end else if (pipeline_compute_track[0].ele_op == LD_V_ELEMENT) begin
        result_v_out            = prepared_v_b;
        compute_result_valid    = v_port_b_valid;
        stored_result_waddr     = pipeline_compute_track[0].waddr;
    end else begin
        result_v_out            = 'b0;
        compute_result_valid    = 1'b0;
        stored_result_waddr     = 'b0;
    end

    
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
            .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
            .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
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

//----------------------------//
// Reduction Compute Unit
//----------------------------//

join_n #(
    .NUM_HANDSHAKES (3)
) join_reduction (
    .data_in_valid({red_v_in_a_valid, red_v_in_b_valid, s_acc_in_valid}),
    .data_in_ready({red_v_in_a_ready, red_v_in_b_ready, s_acc_in_ready}),
    .data_out_valid(red_v_in_valid),
    .data_out_ready(red_v_in_ready)
);

fp_reduction_compute_unit #(
    .EXP_WIDTH(FP_EXP_WIDTH),
    .MANT_WIDTH(FP_MANT_WIDTH),
    .VLEN(VLEN)
) reduction_unit (
    .clk(clk),
    .rst(rst),
    .v_in({prepared_v_a, prepared_v_b, s_acc_in}),
    .v_in_valid(red_v_in_valid),
    .v_in_ready(red_v_in_ready),
    .operation(recorded_reduct_v_control),
    .v_out(s_out),
    .v_out_valid(s_out_valid),
    .v_out_ready(s_out_ready)
);

assign s_out_rd = pipeline_compute_track[VECTOR_REDUCT_CYCLES-1].red_op != STALL_V_REDUCT ? pipeline_compute_track[VECTOR_REDUCT_CYCLES-1].waddr[FP_OPERAND_WIDTH -1:0] : 'b0;

endmodule