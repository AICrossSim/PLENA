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

module double_precision_v_hbm_controller #(
    parameter int   HIGH_MXFP_EXP_WIDTH     = 4,
    parameter int   HIGH_MXFP_MANT_WIDTH    = 3,
    parameter int   LOW_MXFP_EXP_WIDTH      = 4,
    parameter int   LOW_MXFP_MANT_WIDTH     = 3,
    parameter int   MXFP_SCALE_WIDTH        = 16,
    parameter int   BLOCK_DIM               = 4,
    parameter int   DATA_DIM                = 8,
    localparam int  BLOCK_NUM               = DATA_DIM / BLOCK_DIM,
    localparam int  HIGH_ELE_WIDTH          = DATA_DIM * (HIGH_MXFP_EXP_WIDTH + HIGH_MXFP_MANT_WIDTH + 1),
    localparam int  LOW_ELE_WIDTH           = DATA_DIM * (LOW_MXFP_EXP_WIDTH + LOW_MXFP_MANT_WIDTH + 1),
    localparam int  SCALE_WIDTH             = BLOCK_NUM * MXFP_SCALE_WIDTH,
    parameter int   HBM_ADDR_WIDTH          = 32,
    parameter int   ON_CHIP_ADDR_WIDTH      = 32,
    parameter int   HBM_ELE_WIDTH           = 128,
    parameter int   HBM_SCALE_WIDTH         = 128,
    parameter int   SourceWidth             = 4, 
    parameter int   SinkWidth               = 4,   
    parameter int   LOAD_AMOUNT             = 4,
    parameter int   WRITE_AMOUNT            = 4
)(
    input   logic   clk,
    input   logic   rst,
    input   logic   stride_mode,            // 0: Default, 1: Strided.
    input   logic   precision_select,       // 0: High Precision, 1: Low Precision
    input   logic   [ON_CHIP_ADDR_WIDTH - 1 : 0]    stride_offset,
    input   logic   [ON_CHIP_ADDR_WIDTH - 1 : 0]    scale_offset,

    // HBM data prefetching
    output  logic   [HIGH_ELE_WIDTH - 1 : 0]        prefetch_high_precision_element,
    output  logic   [LOW_ELE_WIDTH - 1 : 0]         prefetch_low_precision_element,
    output  logic   [SCALE_WIDTH - 1 : 0]           prefetch_scale,
    output  logic                                   prefetch_data_valid,
    input   logic                                   prefetch_data_ready,
    input   logic                                   hbm_prefetch_en,
    input   logic   [HBM_ADDR_WIDTH - 1 : 0]        hbm_raddr,
    
    // HBM data writing
    input   logic                                   hbm_write_en,
    output  logic                                   hbm_write_ready,
    input   logic   [HIGH_ELE_WIDTH - 1 : 0]        write_high_precision_element,
    input   logic   [LOW_ELE_WIDTH - 1 : 0]         write_low_precision_element,
    input   logic   [SCALE_WIDTH - 1 : 0]           write_scale,
    input   logic   [HBM_ADDR_WIDTH - 1 : 0]        hbm_waddr,

    // TL Interface
    `TL_DECLARE_HOST_PORT(HBM_ELE_WIDTH,   HBM_ADDR_WIDTH, SourceWidth, SinkWidth, host_element),
    `TL_DECLARE_HOST_PORT(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, host_scale)
);

    localparam int HIGH_ELE_MASK_WIDTH      = HIGH_ELE_WIDTH / 8;
    localparam int LOW_ELE_MASK_WIDTH       = LOW_ELE_WIDTH / 8;
    localparam int SCALE_MASK_WIDTH         = SCALE_WIDTH / 8;

    localparam int HIGH_PRECISION_ELE_SCALE_ADR_RATIO   = $clog2(HIGH_ELE_WIDTH / SCALE_WIDTH);
    localparam int LOW_PRECISION_ELE_SCALE_ADR_RATIO    = $clog2(LOW_ELE_WIDTH  / SCALE_WIDTH);

    logic [HIGH_ELE_MASK_WIDTH - 1 : 0]     high_precision_hbm_ele_write_mask;
    logic [LOW_ELE_MASK_WIDTH - 1 : 0]      low_precision_hbm_ele_write_mask;
    logic [SCALE_MASK_WIDTH - 1 : 0]        hbm_scale_write_mask;
    logic [HBM_ADDR_WIDTH - 1 : 0]          hbm_raddr_for_ele;
    logic [HBM_ADDR_WIDTH - 1 : 0]          hbm_raddr_for_scale;
    logic [ON_CHIP_ADDR_WIDTH - 1 : 0]      stride_offset_for_ele, stride_offset_for_scale;
    logic [ON_CHIP_ADDR_WIDTH - 1 : 0]      offset_addr;
    logic high_precision_element_ready_to_write, low_precision_element_ready_to_write, scale_ready_to_write;
    logic hbm_high_precision_write_en, hbm_low_precision_write_en;
    logic hbm_high_precision_req_en, hbm_low_precision_req_en;
    
    logic prefetch_element_data_ready, prefetch_element_data_valid;
    logic prefetch_high_precision_data_valid, prefetch_low_precision_data_valid;
    logic loaded_high_precision_element_valid, loaded_low_precision_element_valid;
    logic loaded_high_precision_element_ready, loaded_low_precision_element_ready;
    logic loaded_scale_valid, loaded_scale_ready;
    logic prefetch_scale_data_valid, prefetch_scale_data_ready;

    logic   [HIGH_ELE_WIDTH - 1 : 0]        loaded_high_precision_element;
    logic   [LOW_ELE_WIDTH - 1 : 0]         loaded_low_precision_element;
    logic   [SCALE_WIDTH - 1 : 0]           loaded_scale;

    assign high_precision_hbm_ele_write_mask = {HIGH_ELE_MASK_WIDTH{1'b1}};
    assign low_precision_hbm_ele_write_mask = {LOW_ELE_MASK_WIDTH{1'b1}};

    // Address for element and scale
    always_comb begin
        if (hbm_write_en) begin
            if (precision_select) begin
                offset_addr             = hbm_waddr[ON_CHIP_ADDR_WIDTH - 1 : 0] >> LOW_PRECISION_ELE_SCALE_ADR_RATIO;
                stride_offset_for_scale = stride_offset >> LOW_PRECISION_ELE_SCALE_ADR_RATIO;
            end else begin
                offset_addr             = hbm_waddr[ON_CHIP_ADDR_WIDTH - 1 : 0] >> HIGH_PRECISION_ELE_SCALE_ADR_RATIO;
                stride_offset_for_scale = stride_offset >> HIGH_PRECISION_ELE_SCALE_ADR_RATIO;
            end
            
            hbm_raddr_for_ele       = hbm_waddr;
            hbm_raddr_for_scale     = hbm_waddr  + offset_addr + scale_offset;
            stride_offset_for_ele   = stride_offset;
            
        end else begin
            if (precision_select) begin
                offset_addr             = hbm_raddr[ON_CHIP_ADDR_WIDTH - 1 : 0] >> LOW_PRECISION_ELE_SCALE_ADR_RATIO;
                stride_offset_for_scale = stride_offset >> LOW_PRECISION_ELE_SCALE_ADR_RATIO;
            end else begin
                offset_addr             = hbm_raddr[ON_CHIP_ADDR_WIDTH - 1 : 0] >> HIGH_PRECISION_ELE_SCALE_ADR_RATIO;
                stride_offset_for_scale = stride_offset >> HIGH_PRECISION_ELE_SCALE_ADR_RATIO;
            end

            hbm_raddr_for_ele       = hbm_raddr;
            hbm_raddr_for_scale     = hbm_waddr + offset_addr + scale_offset;
            stride_offset_for_ele   = stride_offset;
        end

        hbm_high_precision_write_en     = !precision_select & hbm_write_en;
        hbm_high_precision_req_en       = !precision_select & hbm_prefetch_en;
        hbm_low_precision_write_en      = precision_select  & hbm_write_en;
        hbm_low_precision_req_en        = precision_select  & hbm_prefetch_en;
        prefetch_element_data_valid     = precision_select ? prefetch_low_precision_data_valid : prefetch_high_precision_data_valid;

    end

    // TODO: teporary solution for HBM write ready signal, if in the future need a buffer if the critical path happens here.
    assign hbm_write_ready = (precision_select ? low_precision_element_ready_to_write : high_precision_element_ready_to_write) && scale_ready_to_write;

    join2 #(
    ) join_prefetch_signal (
        .data_in_ready({prefetch_element_data_ready, prefetch_scale_data_ready}),
        .data_in_valid({prefetch_element_data_valid, prefetch_scale_data_valid}),
        .data_out_valid(prefetch_data_valid),
        .data_out_ready(prefetch_data_ready)
    );

    // -----------------------------
    // Low Precision and High Precision Selection
    // -----------------------------
    `TL_DECLARE(HBM_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, adapted_tl_element);
    `TL_DECLARE(LOW_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, low_precision_tl_element);
    `TL_DECLARE(HBM_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, adapted_low_precision_tl_element);
    `TL_DECLARE(HIGH_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, high_precision_tl_element);
    `TL_DECLARE(HBM_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, adapted_high_precision_tl_element);
    `TL_BIND_HOST_PORT(host_element, adapted_tl_element);

    tl_selector #(
        .DataWidth          (HBM_ELE_WIDTH),
        .AddrWidth          (HBM_ADDR_WIDTH),
        .SourceWidth        (SourceWidth),
        .SinkWidth          (SinkWidth)
    ) tl_selector_inst (
        .clk                    (clk),
        .rst                    (rst),
        .select                 (precision_select), // 0: High Precision, 1: Low Precision
        `TL_CONNECT_DEVICE_PORT (device_1, adapted_high_precision_tl_element),
        `TL_CONNECT_DEVICE_PORT (device_2, adapted_low_precision_tl_element),
        `TL_CONNECT_HOST_PORT   (host_out, adapted_tl_element)
    );

    // -----------------------------
    // Low Precision HBM element connection for TileLink
    // -----------------------------
    
    tl_master #(
        .DataWidth      (LOW_ELE_WIDTH),
        .AddrWidth      (HBM_ADDR_WIDTH),
        .SourceWidth    (SourceWidth),
        .SinkWidth      (SinkWidth),
        .LOAD_AMOUNT    (LOAD_AMOUNT),
        .WRITE_AMOUNT   (WRITE_AMOUNT),
        .ONCHIP_ADDR    (ON_CHIP_ADDR_WIDTH)
    ) low_precision_element_master (
        .clk(clk),
        .rst(rst),
        .stride_mode            (stride_mode),
        .stride_offset          (stride_offset_for_ele),
        .req_en                 (hbm_low_precision_req_en),
        .write_en               (hbm_low_precision_write_en),
        .addr                   (hbm_raddr_for_ele),
        .fetch_data             (loaded_low_precision_element),
        .fetch_data_ready       (loaded_low_precision_element_ready),
        .write_data             (write_low_precision_element),
        .write_mask             (low_precision_hbm_ele_write_mask),
        .fetch_data_valid       (loaded_low_precision_element_valid),
        .ready_to_write         (low_precision_element_ready_to_write),
        `TL_CONNECT_HOST_PORT   (host, low_precision_tl_element)
    );

    tl_adapter #(
        .HostDataWidth      (LOW_ELE_WIDTH),
        .DeviceDataWidth    (HBM_ELE_WIDTH),
        .AddrWidth          (HBM_ADDR_WIDTH),
        .SourceWidth        (SourceWidth),
        .SinkWidth          (SinkWidth),
        .HostFifo           (1'b0),
        .DeviceFifo         (1'b1)
    ) low_precision_adapter_for_element (
        .clk_i(clk),
        .rst_ni(!rst),
        // TileLink Interface
        `TL_CONNECT_DEVICE_PORT     (host,      low_precision_tl_element),
        `TL_CONNECT_HOST_PORT       (device,    adapted_low_precision_tl_element)
    );

    skid_buffer #(
        .DATA_WIDTH(LOW_ELE_WIDTH)
    ) low_precision_skid_buffer (
        .clk(clk),
        .rst(rst),
        .data_in_valid  (loaded_low_precision_element_valid),
        .data_in_ready  (loaded_low_precision_element_ready),
        .data_in        (loaded_low_precision_element),
        .data_out_valid (prefetch_low_precision_data_valid),
        .data_out_ready (prefetch_element_data_ready),
        .data_out       (prefetch_low_precision_element)
    );

    // -----------------------------
    // High Precision HBM element connection for TileLink
    // -----------------------------

    tl_master #(
        .DataWidth      (HIGH_ELE_WIDTH),
        .AddrWidth      (HBM_ADDR_WIDTH),
        .SourceWidth    (SourceWidth),
        .SinkWidth      (SinkWidth),
        .LOAD_AMOUNT    (LOAD_AMOUNT),
        .WRITE_AMOUNT   (WRITE_AMOUNT),
        .ONCHIP_ADDR    (ON_CHIP_ADDR_WIDTH)
    ) high_precision_element_master (
        .clk(clk),
        .rst(rst),
        .stride_mode            (stride_mode),
        .stride_offset          (stride_offset_for_ele),
        .req_en                 (hbm_high_precision_req_en),
        .write_en               (hbm_high_precision_write_en),
        .addr                   (hbm_raddr_for_ele),
        .fetch_data             (loaded_high_precision_element),
        .fetch_data_ready       (loaded_high_precision_element_ready),
        .write_data             (write_high_precision_element),
        .write_mask             (high_precision_hbm_ele_write_mask),
        .fetch_data_valid       (loaded_high_precision_element_valid),
        .ready_to_write         (high_precision_element_ready_to_write),
        `TL_CONNECT_HOST_PORT   (host, high_precision_tl_element)
    );

    tl_adapter #(
        .HostDataWidth      (HIGH_ELE_WIDTH),
        .DeviceDataWidth    (HBM_ELE_WIDTH),
        .AddrWidth          (HBM_ADDR_WIDTH),
        .SourceWidth        (SourceWidth),
        .SinkWidth          (SinkWidth),
        .HostFifo           (1'b0),
        .DeviceFifo         (1'b1)
    ) high_precision_adapter_for_element (
        .clk_i(clk),
        .rst_ni(!rst),
        // TileLink Interface
        `TL_CONNECT_DEVICE_PORT     (host,      high_precision_tl_element),
        `TL_CONNECT_HOST_PORT       (device,    adapted_high_precision_tl_element)
    );

    skid_buffer #(
        .DATA_WIDTH(HIGH_ELE_WIDTH)
    ) high_precision_skid_buffer (
        .clk(clk),
        .rst(rst),
        .data_in_valid  (loaded_high_precision_element_valid),
        .data_in_ready  (loaded_high_precision_element_ready),
        .data_in        (loaded_high_precision_element),
        .data_out_valid (prefetch_high_precision_data_valid),
        .data_out_ready (prefetch_element_data_ready),
        .data_out       (prefetch_high_precision_element)
    );


    // -----------------------------
    // HBM scale connection for TileLink (Assuming scale is the same for both precisions)
    // -----------------------------
    `TL_DECLARE(SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, tl_scale);
    `TL_DECLARE (HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, adapted_tl_scale);
    `TL_BIND_HOST_PORT(host_scale, adapted_tl_scale);

    tl_master #(
        .DataWidth      (SCALE_WIDTH),
        .AddrWidth      (HBM_ADDR_WIDTH),
        .SourceWidth    (SourceWidth),
        .SinkWidth      (SinkWidth),
        .LOAD_AMOUNT    (LOAD_AMOUNT),
        .WRITE_AMOUNT   (WRITE_AMOUNT),
        .ONCHIP_ADDR    (ON_CHIP_ADDR_WIDTH)
    ) scale_master (
        .clk(clk),
        .rst(rst),
        .stride_mode        (stride_mode),
        .stride_offset      (stride_offset_for_scale),
        .req_en             (hbm_prefetch_en),
        .write_en           (hbm_write_en),
        .addr               (hbm_raddr_for_scale),
        .fetch_data         (loaded_scale),
        .fetch_data_ready   (loaded_scale_ready),
        .fetch_data_valid   (loaded_scale_valid),
        .ready_to_write     (scale_ready_to_write),
        .write_data         (write_scale),
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

    skid_buffer #(
        .DATA_WIDTH(SCALE_WIDTH)
    ) scale_skid_buffer (
        .clk(clk),
        .rst(rst),
        .data_in_valid  (loaded_scale_valid),
        .data_in_ready  (loaded_scale_ready),
        .data_in        (loaded_scale),
        .data_out_valid (prefetch_scale_data_valid),
        .data_out_ready (prefetch_scale_data_ready),
        .data_out       (prefetch_scale)
    );


endmodule