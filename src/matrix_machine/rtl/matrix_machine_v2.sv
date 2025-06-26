`timescale 1ns / 1ps
`include "operation.svh"
`include "configuration.svh"
`include "precision.svh"

/*
Module      : Matrix Machine Module V2
Timing      : Sequential, Takes x cycles to compute the dot product
Description : This module is the newer version of the matrix machine, supporting both GEMM and GEMV operations.
Status      : Passed Simple Tests
*/


module matrix_machine_v2 import precision_pkg::*; import configuration_pkg::*; #(
    localparam  BLOCK_NUM       = MLEN / BLOCK_DIM,
    localparam  ADDR_WIDTH      = ON_CHIP_ADDR_WIDTH
) (
    input   logic   clk,
    input   logic   rst,

    // Execution Control
    input  OP_BUNDLE    exe_stage_op,
    output logic        load_in_progress,
    output logic        stall_for_addr,

    // Matix - row-major order
    input  logic [MLEN-1:0] [(LOW_MXFP_MANT_WIDTH + LOW_MXFP_EXP_WIDTH):0]          m_element,
    input  logic [BLOCK_NUM-1:0]            [MXFP_SCALE_WIDTH-1:0]                  m_scale,
    input  logic                   m_valid,
    output logic                   m_ready,

    // Vector - row-major order
    input  logic [MLEN-1:0] [(HIGH_MXFP_MANT_WIDTH + HIGH_MXFP_EXP_WIDTH):0]        v_element,
    input  logic [BLOCK_NUM-1:0]            [MXFP_SCALE_WIDTH-1:0]                  v_scale,
    input  logic                   v_valid,
    output logic                   v_ready,

    // Output
    output logic [MLEN-1:0] [V_FP_EXP_WIDTH + V_FP_MANT_WIDTH:0]    out_v_fp,
    output logic                                                    out_valid,
    input  logic                                                    out_ready,
    output logic [ADDR_WIDTH-1:0]                                   m_waddr,
    output logic                                                    m_wreq
);

    import pipeline_pkg::*;
    logic [ADDR_WIDTH-1:0] recorded_m_waddr;

    // -----------------------------
    // Control Signals
    // -----------------------------

    M_OP    matrix_opcode; 
    logic    [ADDR_WIDTH-1:0]  addr_in;
    logic    result_waddr_update;

    assign matrix_opcode        = exe_stage_op.m_op;
    assign addr_in              = exe_stage_op.addr_2;
    assign result_waddr_update  = exe_stage_op.result_waddr_update;

    // -----------------------------
    // Address Management
    // -----------------------------
    // Storing the address written back to the vector SRAM

    always_ff @(posedge clk) begin
        if (rst) begin
            recorded_m_waddr <= 'b0;
        end else begin
            // Set result waddr 
            if (matrix_opcode == MM_WO)begin
                recorded_m_waddr <= addr_in;
            end
        end
    end

    // Load Accumulation Address
    logic [ADDR_WIDTH-1:0] acc_addr;
    logic acc_addr_valid, acc_addr_ready;
    fifo #(
        .DATA_WIDTH(ADDR_WIDTH),
        .FIFO_DEPTH(MATRIX_ACC_ADR_DEPTH)
    ) m_acc_addr_fifo (
        .clk(clk),
        .rst(rst),
        .data_in        (exe_stage_op.addr_2),
        .data_in_valid  (exe_stage_op.result_waddr_update),
        .data_in_ready  (stall_for_addr),
        .data_out       (acc_addr),
        .data_out_valid (acc_addr_valid),
        .data_out_ready (acc_addr_ready)
    );

    // -----------------------------
    // Data Preparation
    // -----------------------------

    // Data from Matrix SRAM Buffering
    logic [MLEN-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]     stored_m_element;
    logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]         stored_m_scale;
    logic stored_m_in_ele_ready, stored_m_in_scale_ready;
    logic stored_m_in_ele_valid, stored_m_in_scale_valid;
    logic stored_m_ele_ready, stored_m_scale_ready;
    logic stored_m_ele_valid, stored_m_scale_valid;

    split_n #(
        .N(2)
    ) m_split_i (
        .data_in_valid (m_valid),
        .data_in_ready (m_ready),
        .data_out_valid({stored_m_in_ele_valid, stored_m_in_scale_valid}),
        .data_out_ready({stored_m_in_ele_ready, stored_m_in_scale_ready})
    );

    skid_buffer #(
        .DATA_WIDTH(MLEN * (MXFP_MANT_WIDTH + MXFP_EXP_WIDTH+1))
    ) matrix_element_buffer (
        .clk(clk),
        .rst(rst),
        .data_in        (m_element),
        .data_in_valid  (stored_m_in_ele_valid),
        .data_in_ready  (stored_m_in_ele_ready),
        .data_out       (stored_m_element),
        .data_out_valid (stored_m_ele_valid),
        .data_out_ready (stored_m_ele_ready)
    );

    skid_buffer #(
        .DATA_WIDTH(BLOCK_NUM * MXFP_SCALE_WIDTH)
    ) matrix_scale_buffer (
        .clk(clk),
        .rst(rst),
        .data_in        (m_scale),
        .data_in_valid  (stored_m_in_scale_valid),
        .data_in_ready  (stored_m_in_scale_ready),
        .data_out       (stored_m_scale),
        .data_out_valid (stored_m_scale_valid),
        .data_out_ready (stored_m_scale_ready)
    );

    join_n #(
        .NUM_HANDSHAKES (2)
    ) join_m_element (
        .data_in_valid({stored_m_ele_valid, stored_m_scale_valid}),
        .data_in_ready({stored_m_ele_ready, stored_m_scale_ready}),
        .data_out_valid(stored_m_valid),
        .data_out_ready(stored_m_ready)
    );


    // Data from Vector SRAM Buffering
    // logic [MLEN-1:0] [V_FP_EXP_WIDTH + V_FP_MANT_WIDTH : 0]   stored_v_data;
    // logic stored_v_valid, stored_v_ready;

    // skid_buffer #(
    //     .DATA_WIDTH(MLEN * (V_FP_MANT_WIDTH + V_FP_EXP_WIDTH + 1))
    // ) vector_element_buffer (
    //     .clk(clk),
    //     .rst(rst),
    //     .data_in        (v_fp_in),
    //     .data_in_valid  (v_valid),
    //     .data_in_ready  (v_ready),
    //     .data_out       (stored_v_data),
    //     .data_out_valid (stored_v_valid),
    //     .data_out_ready (stored_v_ready)
    // );

    // Data from Matrix SRAM Buffering
    logic [MLEN-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]     stored_v_element;
    logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]         stored_v_scale;
    logic stored_v_in_ele_ready, stored_v_in_scale_ready;
    logic stored_v_in_ele_valid, stored_v_in_scale_valid;
    logic stored_v_ele_ready, stored_v_scale_ready;
    logic stored_v_ele_valid, stored_v_scale_valid;

    split_n #(
        .N(2)
    ) v_split_i (
        .data_in_valid (v_valid),
        .data_in_ready (v_ready),
        .data_out_valid({stored_v_in_ele_valid, stored_v_in_scale_valid}),
        .data_out_ready({stored_v_in_ele_ready, stored_v_in_scale_ready})
    );

    skid_buffer #(
        .DATA_WIDTH(MLEN * (MXFP_MANT_WIDTH + MXFP_EXP_WIDTH+1))
    ) vector_element_buffer (
        .clk(clk),
        .rst(rst),
        .data_in        (v_element),
        .data_in_valid  (stored_v_in_ele_valid),
        .data_in_ready  (stored_v_in_ele_ready),
        .data_out       (stored_v_element),
        .data_out_valid (stored_v_ele_valid),
        .data_out_ready (stored_v_ele_ready)
    );

    skid_buffer #(
        .DATA_WIDTH(BLOCK_NUM * MXFP_SCALE_WIDTH)
    ) vector_scale_buffer (
        .clk(clk),
        .rst(rst),
        .data_in        (v_scale),
        .data_in_valid  (stored_v_in_scale_valid),
        .data_in_ready  (stored_v_in_scale_ready),
        .data_out       (stored_v_scale),
        .data_out_valid (stored_v_scale_valid),
        .data_out_ready (stored_v_scale_ready)
    );

    join_n #(
        .NUM_HANDSHAKES (2)
    ) join_v_element (
        .data_in_valid({stored_v_ele_valid, stored_v_scale_valid}),
        .data_in_ready({stored_v_ele_ready, stored_v_scale_ready}),
        .data_out_valid(stored_v_valid),
        .data_out_ready(stored_v_ready)
    );





    // Result Buffering
    logic [MLEN-1:0] [M_FP_EXP_WIDTH + M_FP_MANT_WIDTH : 0]   result_v;
    logic result_in_valid, result_in_ready;

    // -----------------------------
    // Systolic Matrix Compute Unit
    // -----------------------------
    mxfp_systolic_mcu #(
        .MXFP_T_EXP_WIDTH   (MXFP_T_EXP_WIDTH),
        .MXFP_T_MANT_WIDTH  (MXFP_T_MANT_WIDTH),
        .MXFP_L_EXP_WIDTH   (MXFP_L_EXP_WIDTH),
        .MXFP_L_MANT_WIDTH  (MXFP_L_MANT_WIDTH),
        .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH),
        .BLOCK_DIM          (BLOCK_DIM),
        .ACC_FP_EXP_WIDTH   (M_FP_EXP_WIDTH),
        .ACC_FP_MANT_WIDTH  (M_FP_MANT_WIDTH),
        .M                  (BATCH_SIZE),
        .K                  (MLEN),
        .N                  (BATCH_SIZE)
    ) matrix_compute_unit (
        .clk                (clk),
        .rst                (rst),
        .control            (matrix_opcode),
        .acc_waddr          (acc_adder),
        .acc_waddr_valid    (acc_addr_valid),
        .acc_waddr_ready    (acc_addr_ready),
        .v1_data            (converted_m_data_out),
        .v1_in_valid        (converted_m_valid),
        .v1_in_ready        (converted_m_ready),
        .v2_data            (stored_v_data),
        .v2_in_valid        (stored_v_valid),
        .v2_in_ready        (stored_v_ready),
        .v_result           (result_v),
        .v_result_valid     (result_in_valid),
        // .v_result_ready     (result_in_ready),
        .load_in_progress   (load_in_progress)
    );

    logic delayed_result_in_valid;
    assign m_wreq   = result_in_valid & ~delayed_result_in_valid;
    assign m_waddr  = recorded_m_waddr;

    always_ff @(posedge clk) begin
        if (rst) begin
            delayed_result_in_valid <= 1'b0;
        end else begin
            delayed_result_in_valid <= result_in_valid;
        end
    end

    logic [MLEN-1:0] [M_FP_EXP_WIDTH + M_FP_MANT_WIDTH : 0]     stored_result_v;
    logic [MLEN-1:0] [V_FP_EXP_WIDTH + V_FP_MANT_WIDTH : 0]     quantized_result_v;
    logic stored_result_valid, stored_result_ready;

    skid_buffer #(
        .DATA_WIDTH (MLEN * (M_FP_EXP_WIDTH + M_FP_MANT_WIDTH + 1))
    ) result_buffer (
        .clk(clk),
        .rst(rst),
        .data_in            (result_v),
        .data_in_valid      (result_in_valid),
        .data_in_ready      (result_in_ready),
        .data_out           (stored_result_v),
        .data_out_valid     (stored_result_valid),
        .data_out_ready     (stored_result_ready)
    );

    skid_buffer #(
        .DATA_WIDTH     (MLEN * (V_FP_EXP_WIDTH + V_FP_MANT_WIDTH + 1))
    ) quantized_result_buffer (
        .clk(clk),
        .rst(rst),
        .data_in        (quantized_result_v),
        .data_in_valid  (stored_result_valid),
        .data_in_ready  (stored_result_ready),
        .data_out       (out_v_fp),
        .data_out_valid (out_valid),
        .data_out_ready (out_ready)
    );

endmodule