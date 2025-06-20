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
    input   M_OP    matrix_opcode,
    output logic    load_in_progress,
    input  logic    [ADDR_WIDTH-1:0]                                        addr_in,

    // Matix - row-major order
    input  logic [MLEN-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]          m_element,
    input  logic [BLOCK_NUM-1:0]            [MXFP_SCALE_WIDTH-1:0]          m_scale,
    input  logic                   m_valid,
    output logic                   m_ready,

    // Vector - row-major order
    input  logic [MLEN-1:0] [(V_FP_MANT_WIDTH + V_FP_EXP_WIDTH):0]          v_fp_in,
    input  logic                   v_valid,
    output logic                   v_ready,

    // Output
    input  logic result_waddr_update,
    output logic [MLEN-1:0] [V_FP_EXP_WIDTH + V_FP_MANT_WIDTH:0]    out_v_fp,
    output logic                                                    out_valid,
    input  logic                                                    out_ready,
    output logic [ADDR_WIDTH-1:0]                                   m_waddr,
    output logic                                                    m_wreq
);

    import pipeline_pkg::*;

    // -----------------------------
    // Data Flow Management
    // -----------------------------

    logic [ADDR_WIDTH-1:0] recorded_m_waddr;

    // Preparation Units 
    always_ff @(posedge clk) begin
        if (rst) begin
            recorded_m_waddr <= 'b0;
        end else begin
            // Set result waddr 
            if (result_waddr_update)begin
                recorded_m_waddr <= addr_in;
            end
        end
    end


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
        .data_in        (v_scale),
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

    // Convert MX-FP Data to FP Data
    logic [BLOCK_NUM-1:0][BLOCK_DIM * (V_FP_EXP_WIDTH + V_FP_MANT_WIDTH + 1 ) - 1 : 0]   converted_m_data_in;
    logic [MLEN-1:0] [V_FP_EXP_WIDTH + V_FP_MANT_WIDTH : 0]   converted_m_data_out;
    logic converted_m_valid, converted_m_ready;

    generate;
        for (genvar i = 0; i < BLOCK_NUM; i++) begin : gen_mxfp_2_fp_convert
            mx_fp_2_fp_block #(
                .BLOCK_DIM          (BLOCK_DIM),
                .MXFP_MANT_WIDTH    (MXFP_MANT_WIDTH),
                .MXFP_EXP_WIDTH     (MXFP_EXP_WIDTH),
                .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH),
                .FP_MANT_WIDTH      (V_FP_MANT_WIDTH),
                .FP_EXP_WIDTH       (V_FP_EXP_WIDTH)
            ) mx_fp_2_fp_convert (
                .element_in     (stored_m_element[(i+1)*BLOCK_DIM-1 : i*BLOCK_DIM]),
                .scale_in       (stored_m_scale[i]),
                .fp_out         (converted_m_data_in[i])
            );
        end
    endgenerate

    skid_buffer #(
        .DATA_WIDTH(MLEN * (V_FP_MANT_WIDTH + V_FP_EXP_WIDTH + 1))
    ) matrix_fp_data_buffer (
        .clk(clk),
        .rst(rst),
        .data_in        (converted_m_data_in),
        .data_in_valid  (stored_m_valid),
        .data_in_ready  (stored_m_ready),
        .data_out       (converted_m_data_out),
        .data_out_valid (converted_m_valid),
        .data_out_ready (converted_m_ready)
    );

    // Data from Vector SRAM Buffering
    logic [MLEN-1:0] [V_FP_EXP_WIDTH + V_FP_MANT_WIDTH : 0]   stored_v_data;
    logic stored_v_valid, stored_v_ready;

    skid_buffer #(
        .DATA_WIDTH(MLEN * (V_FP_MANT_WIDTH + V_FP_EXP_WIDTH + 1))
    ) vector_element_buffer (
        .clk(clk),
        .rst(rst),
        .data_in        (v_fp_in),
        .data_in_valid  (v_valid),
        .data_in_ready  (v_ready),
        .data_out       (stored_v_data),
        .data_out_valid (stored_v_valid),
        .data_out_ready (stored_v_ready)
    );

    // Result Buffering
    logic [MLEN-1:0] [M_FP_EXP_WIDTH + M_FP_MANT_WIDTH : 0]   result_v;
    logic result_in_valid, result_in_ready;

    // -----------------------------
    // Systolic Matrix Compute Unit
    // -----------------------------
    fp_systolic_mcu #(
        .FP_EXP_WIDTH       (V_FP_EXP_WIDTH),
        .FP_MANT_WIDTH      (V_FP_MANT_WIDTH),
        .PROD_EXT_EXP_WIDTH (PRODUCT_EXT_EXP_WIDTH),
        .PROD_EXT_MANT_WIDTH(PRODUCT_EXT_MANT_WIDTH),
        .ACC_FP_EXP_WIDTH   (M_FP_EXP_WIDTH),
        .ACC_FP_MANT_WIDTH  (M_FP_MANT_WIDTH),
        .M                  (BATCH_SIZE),
        .N                  (BATCH_SIZE),
        .K                  (MLEN)
    ) matrix_compute_unit (
        .clk                (clk),
        .rst                (rst),
        .control            (matrix_opcode),
        .v1_data            (converted_m_data_out),
        .v1_in_valid        (converted_m_valid),
        .v1_in_ready        (converted_m_ready),
        .v2_data            (stored_v_data),
        .v2_in_valid        (stored_v_valid),
        .v2_in_ready        (stored_v_ready),
        .v_result           (result_v),
        .v_result_valid     (result_in_valid),
        .v_result_ready     (result_in_ready),
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

    // Quantize into Required Precision for Storage
    generate;
        for (genvar i = 0; i < MLEN; i++) begin : gen_quantize
            fp_ieee_casting #(
                .IN_EXP_WIDTH   (M_FP_EXP_WIDTH),
                .IN_MANT_WIDTH  (M_FP_MANT_WIDTH),
                .OUT_EXP_WIDTH  (V_FP_EXP_WIDTH),
                .OUT_MANT_WIDTH (V_FP_MANT_WIDTH)
            ) cast_inst (
                .data_in      (stored_result_v[i]),
                .data_out     (quantized_result_v[i])
            );
        end
    endgenerate

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