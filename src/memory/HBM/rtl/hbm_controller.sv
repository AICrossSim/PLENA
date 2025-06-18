`timescale 1ns / 1ps

/*
Module      : HBM - DMA - TL Controller
Timing      : Sequential Logic
Status      : Under Development (Need to consider TileLink)
Description : This module is used to control the HBM memory and TileLink interface.
              Two Tilelink Channels, one for element and another for scale in MX format.
Status      : Under Development
*/

module hbm_controller #(
    parameter int MXFP_EXP_WIDTH     = 4,
    parameter int MXFP_MANT_WIDTH    = 3,
    parameter int MXFP_SCALE_WIDTH   = 16,
    parameter int BLOCK_DIM          = 4,

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
    parameter SCALE_DATA_OFFSET = 32'h80000000
)(
    input   logic clk,
    input   logic rst,

    // HBM data prefetching
    output  logic   [ELE_WIDTH - 1 : 0]             prefetch_element,
    output  logic   [SCALE_WIDTH - 1 : 0]           prefetch_scale,
    output  logic                                   prefetch_data_valid,
    input   logic                                   prefetch_element_data_ready,
    input   logic                                   prefetch_scale_data_ready,
    input   logic                                   hbm_prefetch_en,
    input   logic   [HBM_ADDR_WIDTH - 1 : 0]        hbm_addr, // Address for prefetching data
    
    // HBM data writing
    input   logic                                   hbm_write_en,
    input   logic                                   hbm_write_valid,
    output  logic                                   hbm_write_ready,
    input   logic   [ELE_WIDTH - 1 : 0]             hbm_write_element,
    input   logic   [SCALE_WIDTH - 1 : 0]           hbm_write_scale,

    // TL Interface
    `TL_DECLARE_HOST_PORT(HBM_ELE_WIDTH,   HBM_ADDR_WIDTH, SourceWidth, SinkWidth, host_element),
    `TL_DECLARE_HOST_PORT(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, host_scale)
);

    localparam int ELE_MASK_WIDTH   = ELE_WIDTH / 8;
    localparam int SCALE_MASK_WIDTH = SCALE_WIDTH / 8;

    localparam int ELE_SCALE_ADR_RATIO = $clog2((MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) * BLOCK_DIM / MXFP_SCALE_WIDTH);

    logic [ELE_MASK_WIDTH - 1 : 0]      hbm_ele_write_mask      = {ELE_MASK_WIDTH{1'b1}};
    logic [SCALE_MASK_WIDTH - 1 : 0]    hbm_scale_write_mask    = {SCALE_MASK_WIDTH{1'b1}};

    logic [HBM_ADDR_WIDTH - 1 : 0]      hbm_addr_for_ele;
    logic [HBM_ADDR_WIDTH - 1 : 0]      hbm_addr_for_scale;
    logic [ON_CHIP_ADDR_WIDTH - 1 : 0]  offset_addr;


    // Address for element and scale
    always_comb begin
        offset_addr = hbm_addr[ON_CHIP_ADDR_WIDTH - 1 : 0] >> ELE_SCALE_ADR_RATIO;
        hbm_addr_for_ele   = hbm_addr;
        hbm_addr_for_scale = offset_addr + SCALE_DATA_OFFSET;
    end


    // -----------------------------
    // HBM element connection for TileLink
    // -----------------------------
    `TL_DECLARE(ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, tl_element);
    `TL_DECLARE(HBM_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, adapted_tl_element);
    `TL_BIND_HOST_PORT(host_element, adapted_tl_element);

    // TL for element
    tl_master #(
        .DataWidth(ELE_WIDTH),
        .AddrWidth(HBM_ADDR_WIDTH),
        .SourceWidth(SourceWidth),
        .SinkWidth(SinkWidth),
        .LOAD_AMOUNT(LOAD_AMOUNT)
    ) element_master (
        .clk(clk),
        .rst(rst),
        // Control signals
        .req_en                 (hbm_prefetch_en),
        .write_en               (hbm_write_en),
        .addr                   (hbm_addr_for_ele),
        .fetch_data             (prefetch_element),
        .fetch_data_ready       (prefetch_element_data_ready),
        .write_data             (hbm_write_element),
        .write_mask             (hbm_ele_write_mask),
        .fetch_data_valid       (prefetch_data_valid),
        `TL_CONNECT_HOST_PORT   (host, tl_element)
    );

    tl_adapter #(
        .HostDataWidth(ELE_WIDTH),
        .DeviceDataWidth(HBM_ELE_WIDTH),
        .AddrWidth(HBM_ADDR_WIDTH),
        .SourceWidth(SourceWidth),
        .SinkWidth(SinkWidth),
        .HostFifo(1'b0),
        .DeviceFifo(1'b1)
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
        .DataWidth(SCALE_WIDTH),
        .AddrWidth(HBM_ADDR_WIDTH),
        .SourceWidth(SourceWidth),
        .SinkWidth(SinkWidth),
        .LOAD_AMOUNT(LOAD_AMOUNT)
    ) scale_master (
        .clk(clk),
        .rst(rst),
        .req_en             (hbm_prefetch_en),
        .write_en           (hbm_write_en),
        .addr               (hbm_addr_for_scale),
        .fetch_data         (prefetch_scale),
        .fetch_data_ready   (prefetch_scale_data_ready),
        .write_data         (hbm_write_scale),
        .write_mask         (hbm_scale_write_mask),
        `TL_CONNECT_HOST_PORT(host, tl_scale)
    );

    tl_adapter #(
        .HostDataWidth(SCALE_WIDTH),
        .DeviceDataWidth(HBM_SCALE_WIDTH),
        .AddrWidth(HBM_ADDR_WIDTH),
        .SourceWidth(SourceWidth),
        .SinkWidth(SinkWidth),
        .HostFifo(1'b0),
        .DeviceFifo(1'b1)
    ) adapter_for_scale (
        .clk_i(clk),
        .rst_ni(!rst),
        `TL_CONNECT_DEVICE_PORT     (host, tl_scale ),
        `TL_CONNECT_HOST_PORT       (device, adapted_tl_scale)
    );

endmodule