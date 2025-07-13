`timescale 1ns / 1ps
`include "tl_util.svh"
`include "tl_pkg.svh"
/*
Module      : HBM - DMA - TL Controller
Timing      : Sequential Logic
Status      : Under Development (Need to consider TileLink)
Description : This module is used to control the HBM memory and TileLink interface.
              Two Tilelink Channels, one for element and another for scale in MX format.
Status      : Under Development
*/

module hbm_controller #(
    parameter int   MXFP_EXP_WIDTH     = 4,
    parameter int   MXFP_MANT_WIDTH    = 3,
    parameter int   MXFP_SCALE_WIDTH   = 16,
    parameter int   BLOCK_DIM          = 4,
    parameter int   DATA_DIM          = 8,
    localparam      BLOCK_NUM       = DATA_DIM / BLOCK_DIM,
    localparam int  ELE_WIDTH    =   DATA_DIM * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1),
    localparam int  SCALE_WIDTH  =   BLOCK_NUM * MXFP_SCALE_WIDTH,
    parameter int   HBM_ADDR_WIDTH = 32,
    parameter int   ON_CHIP_ADDR_WIDTH = 32,
    parameter int   HBM_ELE_WIDTH = 128,
    parameter int   HBM_SCALE_WIDTH = 128,
    parameter int   SourceWidth = 4, 
    parameter int   SinkWidth = 4,   
    parameter int   LOAD_AMOUNT = 4,
    parameter int   WRITE_AMOUNT = 4
)(
    input   logic clk,
    input   logic rst,
    input   logic stride_mode, // 0: Default, 1: Strided.
    input   logic   [ON_CHIP_ADDR_WIDTH - 1 : 0]    stride_offset,
    input   logic   [ON_CHIP_ADDR_WIDTH - 1 : 0]    scale_offset,

    // HBM data prefetching
    output  logic   [ELE_WIDTH - 1 : 0]             prefetch_element,
    output  logic   [SCALE_WIDTH - 1 : 0]           prefetch_scale,
    output  logic                                   prefetch_data_valid,

    input   logic                                   prefetch_element_data_ready,
    input   logic                                   prefetch_scale_data_ready,
    input   logic                                   hbm_prefetch_en,
    input   logic   [HBM_ADDR_WIDTH - 1 : 0]        hbm_raddr,
    
    // HBM data writing
    input   logic                                   hbm_write_en,
    output  logic                                   hbm_write_ready,
    input   logic   [ELE_WIDTH - 1 : 0]             hbm_write_element,
    input   logic   [SCALE_WIDTH - 1 : 0]           hbm_write_scale,
    input   logic   [HBM_ADDR_WIDTH - 1 : 0]        hbm_waddr,

    // TL Interface
    `TL_DECLARE_HOST_PORT(HBM_ELE_WIDTH,   HBM_ADDR_WIDTH, SourceWidth, SinkWidth, host_element),
    `TL_DECLARE_HOST_PORT(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, host_scale)
);

    localparam int ELE_MASK_WIDTH   = ELE_WIDTH / 8;
    localparam int SCALE_MASK_WIDTH = SCALE_WIDTH / 8;
    localparam int ELE_SCALE_ADR_RATIO = $clog2(ELE_WIDTH / SCALE_WIDTH);

    logic [ELE_MASK_WIDTH - 1 : 0]      hbm_ele_write_mask      = {ELE_MASK_WIDTH{1'b1}};
    logic [SCALE_MASK_WIDTH - 1 : 0]    hbm_scale_write_mask    = {SCALE_MASK_WIDTH{1'b1}};
    logic [HBM_ADDR_WIDTH - 1 : 0]      hbm_raddr_for_ele;
    logic [HBM_ADDR_WIDTH - 1 : 0]      hbm_raddr_for_scale;
    logic [ON_CHIP_ADDR_WIDTH - 1 : 0]  stride_offset_for_ele, stride_offset_for_scale;
    logic [ON_CHIP_ADDR_WIDTH - 1 : 0]  offset_addr;
    logic ele_ready_to_write, scale_ready_to_write;


    // Address for element and scale
    always_comb begin
        if (hbm_write_en) begin
            offset_addr = hbm_waddr[ON_CHIP_ADDR_WIDTH - 1 : 0] >> ELE_SCALE_ADR_RATIO;
            hbm_raddr_for_ele       = hbm_waddr;
            hbm_raddr_for_scale     = hbm_waddr + offset_addr + scale_offset;
            stride_offset_for_ele   = stride_offset;
            stride_offset_for_scale = stride_offset >> ELE_SCALE_ADR_RATIO;
        end else begin
            offset_addr = hbm_raddr[ON_CHIP_ADDR_WIDTH - 1 : 0] >> ELE_SCALE_ADR_RATIO;
            hbm_raddr_for_ele       = hbm_raddr;
            hbm_raddr_for_scale     = hbm_waddr + offset_addr + scale_offset;
            stride_offset_for_ele   = stride_offset;
            stride_offset_for_scale = stride_offset >> ELE_SCALE_ADR_RATIO;
        end

    end

    // TODO: teporary solution for HBM write ready signal, if in the future need a buffer if the critical path happens here.
    assign hbm_write_ready = ele_ready_to_write && scale_ready_to_write;

    // -----------------------------
    // HBM element connection for TileLink
    // -----------------------------
    `TL_DECLARE(ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, tl_element);
    `TL_DECLARE(HBM_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, adapted_tl_element);
    `TL_BIND_HOST_PORT(host_element, adapted_tl_element);

    // TL for element
    tl_master #(
        .DataWidth      (ELE_WIDTH),
        .AddrWidth      (HBM_ADDR_WIDTH),
        .SourceWidth    (SourceWidth),
        .SinkWidth      (SinkWidth),
        .LOAD_AMOUNT    (LOAD_AMOUNT),
        .WRITE_AMOUNT   (WRITE_AMOUNT),
        .ONCHIP_ADDR    (ON_CHIP_ADDR_WIDTH)
    ) element_master (
        .clk(clk),
        .rst(rst),
        .stride_mode            (stride_mode),
        .stride_offset          (stride_offset_for_ele),
        .req_en                 (hbm_prefetch_en),
        .write_en               (hbm_write_en),
        .addr                   (hbm_raddr_for_ele),
        .fetch_data             (prefetch_element),
        .fetch_data_ready       (prefetch_element_data_ready),
        .write_data             (hbm_write_element),
        .write_mask             (hbm_ele_write_mask),
        .fetch_data_valid       (prefetch_data_valid),
        .ready_to_write         (ele_ready_to_write),
        `TL_CONNECT_HOST_PORT   (host, tl_element)
    );

    tl_adapter #(
        .HostDataWidth      (ELE_WIDTH),
        .DeviceDataWidth    (HBM_ELE_WIDTH),
        .AddrWidth          (HBM_ADDR_WIDTH),
        .SourceWidth        (SourceWidth),
        .SinkWidth          (SinkWidth),
        .HostFifo           (1'b0),
        .DeviceFifo         (1'b1)
    ) adapter_for_element (
        .clk_i(clk),
        .rst_ni(!rst),
        // TileLink Interface
        `TL_CONNECT_DEVICE_PORT     (host, tl_element),
        `TL_CONNECT_HOST_PORT       (device, adapted_tl_element)
    );

    // -----------------------------
    // HBM scale connection for TileLink
    // -----------------------------
    `TL_DECLARE(SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, tl_scale);
    `TL_DECLARE(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, adapted_tl_scale);
    `TL_BIND_HOST_PORT(host_scale, adapted_tl_scale);

    tl_master #(
        .DataWidth      (SCALE_WIDTH),
        .AddrWidth      (HBM_ADDR_WIDTH),
        .SourceWidth    (SourceWidth),
        .SinkWidth      (SinkWidth),
        .LOAD_AMOUNT    (LOAD_AMOUNT),
        .WRITE_AMOUNT   (WRITE_AMOUNT)
    ) scale_master (
        .clk(clk),
        .rst(rst),
        .stride_mode        (stride_mode),
        .stride_offset      (stride_offset_for_scale),
        .req_en             (hbm_prefetch_en),
        .write_en           (hbm_write_en),
        .addr               (hbm_raddr_for_scale),
        .fetch_data         (prefetch_scale),
        .fetch_data_ready   (prefetch_scale_data_ready),
        .ready_to_write     (scale_ready_to_write),
        .write_data         (hbm_write_scale),
        .write_mask         (hbm_scale_write_mask),
        `TL_CONNECT_HOST_PORT(host, tl_scale)
    );

    tl_adapter #(
        .HostDataWidth      (SCALE_WIDTH),
        .DeviceDataWidth    (HBM_SCALE_WIDTH),
        .AddrWidth          (HBM_ADDR_WIDTH),
        .SourceWidth        (SourceWidth),
        .SinkWidth          (SinkWidth),
        .HostFifo           (1'b0),
        .DeviceFifo         (1'b1)
    ) adapter_for_scale (
        .clk_i(clk),
        .rst_ni(!rst),
        `TL_CONNECT_DEVICE_PORT     (host, tl_scale),
        `TL_CONNECT_HOST_PORT       (device, adapted_tl_scale)
    );

endmodule