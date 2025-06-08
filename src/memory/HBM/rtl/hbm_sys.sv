`timescale 1ns / 1ps

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
    input   logic [FIXED_OPERAND_WIDTH - 1 : 0] addr_reg_write_operand,
    input   logic [FIXED_OPERAND_WIDTH - 1 : 0] addr_reg_read_operand,

    // Data to Matrix SRAM
    input   logic prefetch_m_ready,
    output  logic prefetch_m_valid,
    output  logic [MLEN -1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      prefetch_m_element,
    output  logic [M_BLOCKNUM -1:0] [MXFP_SCALE_WIDTH-1:0]                prefetch_m_scale,

    // Data to Vector SRAM
    input   logic prefetch_v_ready,
    output  logic prefetch_v_valid,
    output  logic [VLEN-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      prefetch_v_element,
    output  logic [V_BLOCKNUM-1:0] [MXFP_SCALE_WIDTH-1:0]                prefetch_v_scale,

    // Write Back to HBM
    input   logic                                 hbm_write_v_en,
    output  logic                                 hbm_write_v_ready,
    input   logic                                 hbm_write_v_valid,
    input  logic   [VLEN-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]    hbm_write_v_element,
    input  logic   [V_BLOCKNUM-1:0] [MXFP_SCALE_WIDTH-1:0]              hbm_write_v_scale,


    // Matrix SRAM TL Interface
    `TL_DECLARE_HOST_PORT(HBM_ELE_WIDTH,   HBM_ADDR_WIDTH, SourceWidth, SinkWidth, host_m_element),
    `TL_DECLARE_HOST_PORT(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, host_m_scale),
    // Vector SRAM TL Interface
    `TL_DECLARE_HOST_PORT(HBM_ELE_WIDTH,   HBM_ADDR_WIDTH, SourceWidth, SinkWidth, host_v_element),
    `TL_DECLARE_HOST_PORT(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, host_v_scale)
);
    // -----------------------------
    // HBM Address Mapping
    // -----------------------------
    logic [HBM_ADDR_WIDTH - 1 : 0] hbm_addr_out;
    address_mapper #(
        .ADDR_WIDTH         (ADDR_WIDTH),
        .ADR_OPERAND_WIDTH  (ADR_OPERAND_WIDTH),
        .HBM_ADDR_WIDTH     (HBM_ADDR_WIDTH),
        .HBM_ADDR_REG_NUM   (HBM_ADDR_REG_NUM)
    ) address_mapper_inst (
        .clk(clk),
        .rst(rst),
        .mapp_addr_en   (hbm_write_en || hbm_prefetch_en),
        .set_addr_en    (exe_stage_op.c_op == SET_ADDR_REG),
        .addr_in_a      (exe_stage_op.addr_1),
        .addr_in_b      (exe_stage_op.addr_2),
        .addr_offset    (exe_stage_op.addr_1),
        .read_operand   (addr_reg_read_operand),
        .write_operand  (addr_reg_write_operand),
        .hbm_addr_out   (hbm_addr_out)
    );


    // -----------------------------
    // HBM Prefetching for Matrix SRAM
    // -----------------------------
    
    // Prefetching Control
    logic [MLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) - 1 : 0] m_hbm_element_out;
    logic [MLEN * M_BLOCKNUM * MXFP_SCALE_WIDTH - 1 : 0] m_hbm_scale_out;
    logic m_hbm_prefetch_valid, m_hbm_prefetch_en;

    // Write Control, Temporarily not used, only enable write for vector hbm controller
    // logic m_hbm_write_en;
    // logic [MLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) - 1 : 0] m_hbm_element_in;
    // logic [BLOCK_NUM * MXFP_SCALE_WIDTH - 1 : 0] m_hbm_scale_in;
    // logic m_hbm_write_valid, m_hbm_write_ready;
    
    // Buffering Control
    logic prefetch_m_element_ready, prefetch_m_scale_ready;
    `TL_DECLARE(HBM_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth,  m_tl_element);
    `TL_DECLARE(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth,m_tl_scale);
    `TL_BIND_HOST_PORT(host_m_element, m_tl_element);
    `TL_BIND_HOST_PORT(host_m_scale, m_tl_scale);

    hbm_controller #(
        .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
        .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
        .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
        .BLOCK_DIM(BLOCK_DIM),
        .DATA_DIM(MLEN),
        .HBM_ADDR_WIDTH(HBM_ADDR_WIDTH),
        .HBM_ELE_WIDTH(HBM_ELE_WIDTH),
        .HBM_SCALE_WIDTH(HBM_SCALE_WIDTH),
        .SourceWidth(SourceWidth),
        .SinkWidth(SinkWidth)
    ) matrix_hbm_controller_init (
        .clk(clk),
        .rst(rst),
        .prefetch_element                   (m_hbm_element_out),
        .prefetch_scale                     (m_hbm_scale_out),
        .prefetch_data_valid                (m_hbm_prefetch_valid),
        .prefetch_element_data_ready        (prefetch_m_element_ready),
        .prefetch_scale_data_ready          (prefetch_m_scale_ready),
        .hbm_prefetch_en                    (m_hbm_prefetch_en),
        .hbm_write_en                       (),
        .hbm_write_valid                    (),
        .hbm_write_ready                    (),
        .hbm_write_element                  (),
        .hbm_write_scale                    (),
        `TL_CONNECT_HOST_PORT(host_element, m_tl_element),
        `TL_CONNECT_HOST_PORT(host_scale, m_tl_scale)
    );

    logic stored_prefetch_m_element_valid, stored_prefetch_m_element_ready;
    logic stored_prefetch_m_scale_valid, stored_prefetch_m_scale_ready;

    skid_buffer #(
        .DATA_WIDTH(MLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1))
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
    logic [VLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) - 1 : 0] v_hbm_element_out;
    logic [VLEN * V_BLOCKNUM * MXFP_SCALE_WIDTH - 1 : 0] v_hbm_scale_out;
    logic v_hbm_prefetch_valid, v_hbm_prefetch_en;

    // Buffering Control
    logic prefetch_v_element_ready, prefetch_v_scale_ready;
    `TL_DECLARE(HBM_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth,  v_tl_element);
    `TL_DECLARE(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth,v_tl_scale);
    `TL_BIND_HOST_PORT(host_v_element, v_tl_element);
    `TL_BIND_HOST_PORT(host_v_scale, v_tl_scale);

    hbm_controller #(
        .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
        .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
        .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
        .BLOCK_DIM(BLOCK_DIM),
        .DATA_DIM(VLEN),
        .HBM_ADDR_WIDTH(HBM_ADDR_WIDTH),
        .HBM_ELE_WIDTH(HBM_ELE_WIDTH),
        .HBM_SCALE_WIDTH(HBM_SCALE_WIDTH),
        .SourceWidth(SourceWidth),
        .SinkWidth(SinkWidth)
    ) vector_hbm_controller_init (
        .clk(clk),
        .rst(rst),
        .prefetch_element                   (v_hbm_element_out),
        .prefetch_scale                     (v_hbm_scale_out),
        .prefetch_data_valid                (v_hbm_prefetch_valid),
        .prefetch_element_data_ready        (prefetch_v_element_ready),
        .prefetch_scale_data_ready          (prefetch_v_scale_ready),
        .hbm_prefetch_en                    (v_hbm_prefetch_en),
        .hbm_write_en                       (hbm_write_v_en),
        .hbm_write_valid                    (hbm_write_v_valid),
        .hbm_write_ready                    (hbm_write_v_ready),
        .hbm_write_element                  (hbm_write_v_element),
        .hbm_write_scale                    (hbm_write_v_scale),
        `TL_CONNECT_HOST_PORT(host_element, v_tl_element),
        `TL_CONNECT_HOST_PORT(host_scale, v_tl_scale)
    );

    logic stored_prefetch_v_element_valid, stored_prefetch_v_element_ready;
    logic stored_prefetch_v_scale_valid, stored_prefetch_v_scale_ready;

    skid_buffer #(
        .DATA_WIDTH(VLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1))
    ) vector_sram_prefetch_buffer (
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