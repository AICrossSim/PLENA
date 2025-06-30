`timescale 1ns / 1ps
`include "tl_util.svh"
`include "tl_pkg.svh"
`include "configuration.svh"
`include "operation.svh"
/*
Module      : HBM System
Description : 
            : This module is the top level HBM system .
            : It contains the HBM controller, HBM arbiter, and the HBM interface.
            : It controls the read and write process from the HBM, and control the data distribution to matrix SRAM and vector SRAM.
            : It should suppot prefetching data from HBM for the two ports at the same time so that we could drain the HBM bandwidth.
*/

module hbm_sys import precision_pkg::*; import configuration_pkg::*; #(
    localparam int V_BLOCKNUM       = VLEN / BLOCK_DIM,
    localparam int M_BLOCKNUM       = MLEN / BLOCK_DIM,
    localparam int ADDR_WIDTH       = ON_CHIP_ADDR_WIDTH
) (
    input   logic clk,
    input   logic rst,

    // Control
    input   OP_BUNDLE exe_stage_op,

    // Data to Matrix SRAM
    input   logic prefetch_m_ready,
    output  logic prefetch_m_valid,
    output  logic [MLEN -1:0] [(LOW_MXFP_MANT_WIDTH + LOW_MXFP_EXP_WIDTH):0]            prefetch_m_element,
    output  logic [M_BLOCKNUM -1:0] [MXFP_SCALE_WIDTH-1:0]                              prefetch_m_scale,

    // Data to Vector SRAM
    input   logic prefetch_v_ready,
    output  logic prefetch_v_valid,
    output  logic [VLEN-1:0] [(HIGH_MXFP_MANT_WIDTH + HIGH_MXFP_EXP_WIDTH):0]           prefetch_v_element,
    output  logic [V_BLOCKNUM-1:0] [MXFP_SCALE_WIDTH-1:0]                               prefetch_v_scale,

    // Write Back to HBM
    input   logic                                 hbm_write_v_en,
    output  logic                                 hbm_write_v_ready,
    input   logic   [VLEN-1:0] [(HIGH_MXFP_MANT_WIDTH + HIGH_MXFP_EXP_WIDTH):0]    hbm_write_v_element,
    input   logic   [V_BLOCKNUM-1:0] [MXFP_SCALE_WIDTH-1:0]                        hbm_write_v_scale,

    // Status Tracking
    output logic prefetch_m_in_progress,
    output logic prefetch_v_in_progress,

    // Matrix SRAM TL Interface
    `TL_DECLARE_HOST_PORT(HBM_ELE_WIDTH,   HBM_ADDR_WIDTH, SourceWidth, SinkWidth, host_m_element),
    `TL_DECLARE_HOST_PORT(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, host_m_scale),
    // Vector SRAM TL Interface
    `TL_DECLARE_HOST_PORT(HBM_ELE_WIDTH,   HBM_ADDR_WIDTH, SourceWidth, SinkWidth, host_v_element),
    `TL_DECLARE_HOST_PORT(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, host_v_scale)
);

    // -----------------------------
    // HBM System Control
    // -----------------------------
    logic v_hbm_prefetch_en, m_hbm_prefetch_en;
    // One clk delayed for address mapping
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            v_hbm_prefetch_en <= 1'b0;
            m_hbm_prefetch_en <= 1'b0;
        end else begin
            v_hbm_prefetch_en <= (exe_stage_op.h_op == PREFETCH_V);
            m_hbm_prefetch_en <= (exe_stage_op.h_op == PREFETCH_M);
        end
    end

    // -----------------------------
    // HBM Status Tracking
    // -----------------------------
    always_ff @(posedge clk) begin
        if (rst) begin
            prefetch_m_in_progress <= 1'b0;
            prefetch_v_in_progress <= 1'b0;
        end else begin
            if (exe_stage_op.h_op == PREFETCH_V) begin
                prefetch_v_in_progress <= 1'b1;
            end else if (prefetch_v_valid && prefetch_v_ready) begin
                prefetch_v_in_progress <= 1'b0;
            end
            if (exe_stage_op.h_op == PREFETCH_M) begin
                prefetch_m_in_progress <= 1'b1;
            end else if (prefetch_m_valid && prefetch_m_ready) begin
                prefetch_m_in_progress <= 1'b0;
            end
        end
    end


    // -----------------------------
    // HBM Address Mapping
    // -----------------------------
    logic [HBM_ADDR_WIDTH - 1 : 0] hbm_addr_out, recorded_hbm_waddr_out;
    address_mapper #(
        .ADDR_WIDTH         (ADDR_WIDTH),
        .ADR_OPERAND_WIDTH  (ADR_OPERAND_WIDTH),
        .HBM_ADDR_WIDTH     (HBM_ADDR_WIDTH),
        .HBM_ADDR_REG_NUM   (HBM_ADDR_REG_NUM)
    ) address_mapper_inst (
        .clk(clk),
        .rst(rst),
        .mapp_addr_en   (exe_stage_op.h_op != STALL_H),
        .set_addr_en    (exe_stage_op.c_op == SET_ADDR_REG),
        .addr_in_a      (exe_stage_op.addr_1),
        .addr_in_b      (exe_stage_op.addr_2),
        .addr_offset    (exe_stage_op.addr_1),
        .read_operand   (exe_stage_op.fixed_rs2),
        .write_operand  (exe_stage_op.fixed_rd),
        .hbm_addr_out   (hbm_addr_out)
    );
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            recorded_hbm_waddr_out <= {HBM_ADDR_WIDTH{1'b0}};
        end else if (exe_stage_op.h_op == STORE_V) begin
            recorded_hbm_waddr_out <= hbm_addr_out;
        end
    end


    // -----------------------------
    // HBM Prefetching for Matrix SRAM
    // -----------------------------
    
    // Prefetching Control
    logic [MLEN * (LOW_MXFP_EXP_WIDTH + LOW_MXFP_MANT_WIDTH + 1) - 1 : 0] m_hbm_element_out;
    logic [M_BLOCKNUM * MXFP_SCALE_WIDTH - 1 : 0] m_hbm_scale_out;
    logic m_hbm_prefetch_valid;

    // Buffering Control
    logic prefetch_m_element_ready, prefetch_m_scale_ready;
    `TL_DECLARE(HBM_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth,  m_tl_element);
    `TL_DECLARE(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth,m_tl_scale);
    `TL_BIND_HOST_PORT(host_m_element, m_tl_element);
    `TL_BIND_HOST_PORT(host_m_scale, m_tl_scale);

    hbm_controller #(
        .MXFP_EXP_WIDTH         (LOW_MXFP_EXP_WIDTH),
        .MXFP_MANT_WIDTH        (LOW_MXFP_MANT_WIDTH),
        .MXFP_SCALE_WIDTH       (MXFP_SCALE_WIDTH),
        .LOWEST_MXFP_EXP_WIDTH  (LOW_MXFP_EXP_WIDTH),
        .LOWEST_MXFP_MANT_WIDTH (LOW_MXFP_MANT_WIDTH),
        .BLOCK_DIM              (BLOCK_DIM),
        .DATA_DIM               (MLEN),
        .HBM_ADDR_WIDTH         (HBM_ADDR_WIDTH),
        .ON_CHIP_ADDR_WIDTH     (ADDR_WIDTH),
        .HBM_ELE_WIDTH          (HBM_ELE_WIDTH),
        .HBM_SCALE_WIDTH        (HBM_SCALE_WIDTH),
        .SourceWidth            (SourceWidth),
        .SinkWidth              (SinkWidth),
        .LOAD_AMOUNT            (HBM_M_Prefetch_Amount)
    ) matrix_hbm_controller_init (
        .clk(clk),
        .rst(rst),
        .prefetch_element                   (m_hbm_element_out),
        .prefetch_scale                     (m_hbm_scale_out),
        .prefetch_data_valid                (m_hbm_prefetch_valid),
        .prefetch_element_data_ready        (prefetch_m_element_ready),
        .prefetch_scale_data_ready          (prefetch_m_scale_ready),
        .hbm_prefetch_en                    (m_hbm_prefetch_en),
        .hbm_raddr                          (hbm_addr_out),
        `TL_CONNECT_HOST_PORT(host_element, m_tl_element),
        `TL_CONNECT_HOST_PORT(host_scale, m_tl_scale)
    );

    logic stored_prefetch_m_element_valid, stored_prefetch_m_element_ready;
    logic stored_prefetch_m_scale_valid, stored_prefetch_m_scale_ready;

    skid_buffer #(
        .DATA_WIDTH(MLEN * (LOW_MXFP_EXP_WIDTH + LOW_MXFP_MANT_WIDTH + 1))
    ) matrix_sram_prefetch_buffer (
        .clk(clk),
        .rst(rst),
        .data_in(m_hbm_element_out),
        .data_in_valid(m_hbm_prefetch_valid),
        .data_in_ready(prefetch_m_element_ready),
        .data_out(prefetch_m_element),
        .data_out_valid(stored_prefetch_m_element_valid),
        .data_out_ready(stored_prefetch_m_element_ready)
    );

    skid_buffer #(
        .DATA_WIDTH(M_BLOCKNUM * MXFP_SCALE_WIDTH)
    ) matrix_sram_prefetch_scale_buffer (
        .clk(clk),
        .rst(rst),
        .data_in(m_hbm_scale_out),
        .data_in_valid(m_hbm_prefetch_valid),
        .data_in_ready(prefetch_m_scale_ready),
        .data_out(prefetch_m_scale),
        .data_out_valid(stored_prefetch_m_scale_valid),
        .data_out_ready(stored_prefetch_m_scale_ready)
    );

    join2 #(
    ) join_matrix_prefetch (
        .data_in_ready({stored_prefetch_m_element_ready, stored_prefetch_m_scale_ready}),
        .data_in_valid({stored_prefetch_m_element_valid, stored_prefetch_m_scale_valid}),
        .data_out_valid(prefetch_m_valid),
        .data_out_ready(prefetch_m_ready)
    );


    // -----------------------------
    // HBM Prefetching for Vector SRAM
    // -----------------------------

    // HBM Control Signal between Arbiter and Controller

    // Prefetching Control
    logic [VLEN * (HIGH_MXFP_EXP_WIDTH + HIGH_MXFP_MANT_WIDTH + 1) - 1 : 0] v_hbm_element_out;
    logic [V_BLOCKNUM * MXFP_SCALE_WIDTH - 1 : 0] v_hbm_scale_out;
    logic v_hbm_prefetch_valid;

    // Buffering Control
    logic prefetch_v_element_ready, prefetch_v_scale_ready;
    `TL_DECLARE(HBM_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth,  v_tl_element);
    `TL_DECLARE(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth,v_tl_scale);
    `TL_BIND_HOST_PORT(host_v_element, v_tl_element);
    `TL_BIND_HOST_PORT(host_v_scale, v_tl_scale);

    hbm_controller #(
        .MXFP_EXP_WIDTH         (HIGH_MXFP_EXP_WIDTH),
        .MXFP_MANT_WIDTH        (HIGH_MXFP_MANT_WIDTH),
        .MXFP_SCALE_WIDTH       (MXFP_SCALE_WIDTH),
        .LOWEST_MXFP_EXP_WIDTH  (LOW_MXFP_EXP_WIDTH),
        .LOWEST_MXFP_MANT_WIDTH (LOW_MXFP_MANT_WIDTH),
        .BLOCK_DIM              (BLOCK_DIM),
        .DATA_DIM               (VLEN),
        .HBM_ADDR_WIDTH         (HBM_ADDR_WIDTH),
        .HBM_ELE_WIDTH          (HBM_ELE_WIDTH),
        .HBM_SCALE_WIDTH        (HBM_SCALE_WIDTH),
        .SourceWidth            (SourceWidth),
        .SinkWidth              (SinkWidth),
        .LOAD_AMOUNT            (HBM_V_Prefetch_Amount),
        .WRITE_AMOUNT           (HBM_V_Writeback_Amount)
    ) vector_hbm_controller_init (
        .clk(clk),
        .rst(rst),
        .prefetch_element                   (v_hbm_element_out),
        .prefetch_scale                     (v_hbm_scale_out),
        .prefetch_data_valid                (v_hbm_prefetch_valid),
        .prefetch_element_data_ready        (prefetch_v_element_ready),
        .prefetch_scale_data_ready          (prefetch_v_scale_ready),
        .hbm_prefetch_en                    (v_hbm_prefetch_en),
        .hbm_raddr                          (hbm_addr_out),
        .hbm_write_en                       (hbm_write_v_en),
        .hbm_write_ready                    (hbm_write_v_ready),
        .hbm_write_element                  (hbm_write_v_element),
        .hbm_write_scale                    (hbm_write_v_scale),
        .hbm_waddr                          (recorded_hbm_waddr_out),
        `TL_CONNECT_HOST_PORT(host_element, v_tl_element),
        `TL_CONNECT_HOST_PORT(host_scale, v_tl_scale)
    );

    logic stored_prefetch_v_element_valid, stored_prefetch_v_element_ready;
    logic stored_prefetch_v_scale_valid, stored_prefetch_v_scale_ready;

    skid_buffer #(
        .DATA_WIDTH(VLEN * (HIGH_MXFP_EXP_WIDTH + HIGH_MXFP_MANT_WIDTH + 1))
    ) vector_sram_prefetch_ele_buffer (
        .clk(clk),
        .rst(rst),
        .data_in(v_hbm_element_out),
        .data_in_valid(v_hbm_prefetch_valid),
        .data_in_ready(prefetch_v_element_ready),
        .data_out(prefetch_v_element),
        .data_out_valid(stored_prefetch_v_element_valid),
        .data_out_ready(stored_prefetch_v_element_ready)
    );
    skid_buffer #(
        .DATA_WIDTH(V_BLOCKNUM * MXFP_SCALE_WIDTH)
    ) vector_sram_prefetch_scale_buffer (
        .clk(clk),
        .rst(rst),
        .data_in(v_hbm_scale_out),
        .data_in_valid(v_hbm_prefetch_valid),
        .data_in_ready(prefetch_v_scale_ready),
        .data_out(prefetch_v_scale),
        .data_out_valid(stored_prefetch_v_scale_valid),
        .data_out_ready(stored_prefetch_v_scale_ready)
    );

    join2 #(
    ) join_vector_prefetch (
        .data_in_ready({stored_prefetch_v_element_ready, stored_prefetch_v_scale_ready}),
        .data_in_valid({stored_prefetch_v_element_valid, stored_prefetch_v_scale_valid}),
        .data_out_valid(prefetch_v_valid),
        .data_out_ready(prefetch_v_ready)
    );

endmodule