`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : HBM Data Scheduler
Timing      : Combinatorial
Description : This module is used to schedule the data prefetched from HBM to Matrix SRAM and Scratchpad SRAM.
            : It also shdules the write process from the two SRAMs to HBM.
Status      : Under Development
*/

module hbm_data_scheduler #(
    parameter   MXFP_EXP_WIDTH      = 4,
    parameter   MXFP_MANT_WIDTH     = 3,
    parameter   MXFP_SCALE_WIDTH    = 8,
    parameter   BLOCK_DIM           = 4,
    parameter   ADDR_WIDTH          = 32,
    parameter   MLEN                = 8,
    parameter   VLEN                = 8,
    parameter   Parallel_Rd_Dim     = 4,

    localparam int M_BLOCK_NUM      = MLEN / BLOCK_DIM,
    localparam int V_BLOCK_NUM      = VLEN / BLOCK_DIM,
    localparam int ELE_WIDTH        = Parallel_Rd_Dim * MLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1),
    localparam int SCALE_WIDTH      = Parallel_Rd_Dim * M_BLOCK_NUM * MXFP_SCALE_WIDTH
    localparam int V_ELE_WIDTH      = VLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1),
    localparam int V_SCALE_WIDTH    = V_BLOCK_NUM * MXFP_SCALE_WIDTH

)(
    input logic clk,
    input logic rst,

    // HBM 
    input   logic   [ELE_WIDTH - 1 : 0]             prefetch_element,
    input   logic   [SCALE_WIDTH - 1 : 0]           prefetch_scale,
    input   logic                                   prefetch_data_valid,
    output  logic                                   prefetch_data_ready,
    input   logic   [ADDR_WIDTH - 1 : 0]            prefetch_waddr,

    // HBM data writing
    output   logic                                  hbm_write_en,
    output   logic                                  hbm_write_valid,
    input    logic                                  hbm_write_ready,
    output   logic   [ELE_WIDTH - 1 : 0]            hbm_write_element,
    output   logic   [SCALE_WIDTH - 1 : 0]          hbm_write_scale,

    // Matrix SRAM
    output   logic   [ELE_WIDTH - 1 : 0]            prefetch_m_element,
    output   logic   [SCALE_WIDTH - 1 : 0]          prefetch_m_scale,
    output   logic                                  prefetch_m_data_valid,

    input    logic   [V_ELE_WIDTH- 1 : 0]           m_out_element,
    input    logic   [V_SCALE_WIDTH- 1 : 0]         m_out_scale,
    input    logic                                  m_out_data_wen,

    // Scratchpad SRAM
    output   logic   [V_ELE_WIDTH- 1 : 0]           prefetch_v_element,
    output   logic   [V_SCALE_WIDTH- 1 : 0]         prefetch_v_scale,
    output   logic                                  prefetch_v_data_valid,

    input    logic   [ELE_WIDTH - 1 : 0]            v_out_element,
    input    logic   [SCALE_WIDTH - 1 : 0]          v_out_scale,
    input    logic                                  v_out_data_wen,

    // Control signals
    output   logic                                  hbm_write_en,
    output   logic                                  hbm_write_valid,
    input    logic                                  hbm_write_ready
);

//TODO

endmodule