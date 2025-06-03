`timescale 1ns / 1ps

/*
Module      : HBM Sys
Description : 
            : This module is the top level HBM system .
            : It contains the HBM controller, HBM arbiter, and the HBM interface.
            : It controls the read and write process from the HBM, and control the data distribution to matrix SRAM and vector SRAM.
            : For the currect ISA design, every M prefetch process will constitute fetching a whole size of matrix sram from HBM to the memory.
            : For V prefetch, it will fetch specific amount of vector data from HBM to the memory.
*/


module hbm_sys import precision_pkg::*; #(
    parameter   OPERAND_WIDTH           = 5,
    parameter   VLEN                    = 8,       
    parameter   MLEN                    = 8,
    parameter   Parallel_Rd_Dim         = 4,       // Number of inputs per cycle
    localparam MATRIX_LOAD_ITERATION = MLEN / Parallel_Rd_Dim,
    localparam MATRIX_COUNTER_WIDTH = $clog2(MATRIX_LOAD_ITERATION),
    localparam BLOCK_NUM = VLEN / BLOCK_DIM
) (
    input   logic clk,
    input   logic rst,

    // Control
    input OP_BUNDLE assigned_op_bundle,

    // Data to Matrix SRAM
    input   logic m_prefetch_ready,
    output  logic [MLEN * Matrix_Parallel_Rd_Dim-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      prefetch_m_element,
    output  logic [MLEN * Matrix_Parallel_Rd_Dim-1:0] [MXFP_SCALE_WIDTH-1:0]                      prefetch_m_scale,

    // Data to Vector SRAM
    input   logic v_prefetch_ready,
    output  logic [VLEN-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      prefetch_v_element,
    output  logic [VLEN-1:0] [MXFP_SCALE_WIDTH-1:0]                      prefetch_v_scale,
    
    // TL Declaration
    `TL_DECLARE(HBM_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, element);
    `TL_BIND_HOST_PORT(out_element, element);

    `TL_DECLARE(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, scale);
    `TL_BIND_HOST_PORT(out_scale, scale);

);



// HBM Control


    logic [MLEN * MLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) - 1 : 0] hbm_element_out;
    logic [MLEN * BLOCK_NUM * MXFP_SCALE_WIDTH - 1 : 0] hbm_scale_out;
    logic hbm_prefetch_valid, hbm_prefetch_en;
    logic [HBM_ADDR_WIDTH - 1 : 0] addr_to_prefetch, addr_for_prefetched_data;

    logic hbm_write_en;
    logic [Matrix_Parallel_Rd_Dim * MLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) - 1 : 0] hbm_element_in;
    logic [Matrix_Parallel_Rd_Dim * BLOCK_NUM * MXFP_SCALE_WIDTH - 1 : 0] hbm_scale_in;
    logic hbm_write_valid, hbm_write_ready;

    hbm_arbiter #(
        .MXFP_EXP_WIDTH     (MXFP_EXP_WIDTH),
        .MXFP_MANT_WIDTH    (MXFP_MANT_WIDTH),
        .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH),
        .BLOCK_DIM          (BLOCK_DIM),
        .ADDR_WIDTH         (FIXED_DATA_WIDTH),
        .MLEN               (MLEN),    
        .VLEN               (VLEN),
        .Parallel_Rd_Dim    (Matrix_Parallel_Rd_Dim)
    ) hbm_arbiter_init (
        .clk(clk),
        .rst(rst),

        // HBM Prefetching
        .prefetch_element       (hbm_element_out),
        .prefetch_scale         (hbm_scale_out),
        .prefetch_data_valid    (hbm_prefetch_valid),
        .hbm_prefetch_en        (hbm_prefetch_en),
        .addr_to_prefetch       (addr_to_prefetch),
        .addr_for_prefetched_data (addr_for_prefetched_data),

        // HBM Write
        .hbm_write_en           (hbm_write_en),
        .hbm_write_ready        (hbm_write_ready),
        .hbm_write_valid        (hbm_write_valid),
        .hbm_write_element      (hbm_element_in),
        .hbm_write_scale        (hbm_scale_in),

        // Matrix SRAM
        // Write to Matrix SRAM
        .prefetch_m_ready       (m_sram_wen),
        .prefetch_m_element     (prefetch_m_element),
        .prefetch_m_scale       (prefetch_m_scale),

        // Vector SRAM
        // Write to Vector SRAM
        .prefetch_v_ready       (s_sram_wen_b),
        .prefetch_v_element     (v_element_port_b_in),
        .prefetch_v_scale       (v_scale_port_b_in),

        // Read from Vector SRAM
        .v_out_element          (v_element_port_b_out),
        .v_out_scale            (v_scale_port_b_out),
        .v_out_data_wen         (hbm_ready_to_write), // Left for store vector into HBM

        // HBM Operation
        .h_op                       (assigned_op_bundle.h_op),
        .continuous_prefetch_m_en   (continuous_prefetch_m_en),
        .hbm_m_prefetch_complete    (hbm_m_prefetch_complete),
        .hbm_v_prefetch_complete    (hbm_v_prefetch_complete),
        .hbm_arbiter_busy           (hbm_in_used)
    );

    hbm_controller #(
        .Parallel_Rd_Dim(Matrix_Parallel_Rd_Dim),
        .SourceWidth(SourceWidth),
        .SinkWidth(SinkWidth),
        .HBM_ELE_WIDTH(HBM_ELE_WIDTH),
        .HBM_SCALE_WIDTH(HBM_SCALE_WIDTH)
    ) hbm_controller_init (
        .clk(clk),
        .rst(rst),

        // Address Register
        .set_addr_reg_en                    (assigned_op_bundle.c_op == SET_ADDR_REG),
        .addr_in_a                          (fixed_out_1),
        .addr_in_b                          (fixed_out_2),
        // Address Register Index
        .addr_reg_write_operand             (s_rd),
        .addr_reg_read_operand              (s_rs2),

        // Prefetching
        .prefetch_element                   (hbm_element_out),
        .prefetch_scale                     (hbm_scale_out),
        .prefetch_data_valid                (hbm_prefetch_valid),
        .hbm_prefetch_en                    (hbm_prefetch_en),
        .addr_to_prefetch                   (addr_to_prefetch),
        .addr_for_prefetched_data           (addr_for_prefetched_data),
        .continuous_prefetch_m_en           (continuous_prefetch_m_en),
        .m_sram_continuous_prefetch_counter (m_sram_continuous_prefetch_counter),

        // HBM Write
        .hbm_write_en                       (hbm_write_en),
        .hbm_write_valid                    (hbm_write_valid),
        .hbm_write_ready                    (hbm_write_ready),
        .hbm_write_element                  (hbm_element_in),
        .hbm_write_scale                    (hbm_scale_in),
        .hbm_prefetch_content_exist         (hbm_m_prefetch_complete || hbm_v_prefetch_complete),

        // HBM Interface
        `TL_CONNECT_HOST_PORT(host_element, element),
        `TL_CONNECT_HOST_PORT(host_scale, scale)

    );


endmodule