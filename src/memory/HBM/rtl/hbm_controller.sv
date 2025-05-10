`timescale 1ns / 1ps
`include "operation.svh"
`include "tl_util.svh"

/*
Module      : HBM - DMA - TL Controller
Timing      : Sequential Logic
Status      : Under Development (Need to consider TileLink)
Description : This module is used to control the HBM memory and TileLink interface.
              Two Tilelink Channels, one for element and another for scale in MX format.
Status      : Under Development
*/

module hbm_controller #(
    parameter   MXFP_EXP_WIDTH      = 4,
    parameter   MXFP_MANT_WIDTH     = 3,
    parameter   MXFP_SCALE_WIDTH    = 8,
    parameter   BLOCK_DIM           = 4,
    parameter   ADDR_WIDTH          = 32,
    parameter   MLEN                = 8,
    parameter   VLEN                = 8,
    parameter   Parallel_Rd_Dim     = 4,

    parameter   ADR_OPERAND_WIDTH   = 5,
    localparam  M_BLOCK_NUM         = MLEN / BLOCK_DIM,

    // HBM Config and TL settings
    parameter   HBM_ADDR_WIDTH          = 64,
    parameter   HBM_ADDR_REG_NUM        = 4,

    parameter int unsigned SourceWidth  = 1,
    parameter int unsigned SinkWidth    = 1,

    localparam int ELE_WIDTH    =   MLEN * MLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1),
    localparam int SCALE_WIDTH  =   MLEN * M_BLOCK_NUM * MXFP_SCALE_WIDTH,

    parameter int HBM_ELE_WIDTH = 128,
    parameter int HBM_SCALE_WIDTH = 128,
    parameter SCALE_DATA_OFFSET = 32'h80000000,

    localparam MATRIX_LOAD_ITERATION = MLEN / Parallel_Rd_Dim,
    localparam MATRIX_COUNTER_WIDTH = $clog2(MATRIX_LOAD_ITERATION)
)(
    input   logic clk,
    input   logic rst,

    // HBM addr mapping
    input   logic   set_addr_reg_en,
    input   logic   [ADDR_WIDTH - 1 : 0]            hbm_offset_addr,
    input   logic   [ADDR_WIDTH - 1 : 0]            addr_in_a,
    input   logic   [ADDR_WIDTH - 1 : 0]            addr_in_b,
    input   logic   [ADR_OPERAND_WIDTH - 1 : 0]     addr_reg_write_operand,
    input   logic   [ADR_OPERAND_WIDTH - 1 : 0]     addr_reg_read_operand,

    // HBM data prefetching
    output  logic   [ELE_WIDTH - 1 : 0]             prefetch_element,
    output  logic   [SCALE_WIDTH - 1 : 0]           prefetch_scale,
    output  logic                                   prefetch_data_valid,
    input   logic                                   hbm_prefetch_en,

    output  logic   [HBM_ADDR_WIDTH - 1 : 0]        addr_to_prefetch,
    output  logic   [HBM_ADDR_WIDTH - 1 : 0]        addr_for_prefetched_data,
    // TODO : consider to move this part to upper level
    input   logic                                   continuous_prefetch_m_en,
    input   logic   [MATRIX_COUNTER_WIDTH - 1 : 0]  m_sram_continuous_prefetch_counter,


    // HBM data writing
    input   logic                                   hbm_write_en,
    input   logic                                   hbm_write_valid,
    output  logic                                   hbm_write_ready,
    input   logic   [ELE_WIDTH - 1 : 0]             hbm_write_element,
    input   logic   [SCALE_WIDTH - 1 : 0]           hbm_write_scale,

    // Check Existence
    input   logic                                   hbm_prefetch_content_exist,

    // TL Interface
    `TL_DECLARE_HOST_PORT(HBM_ELE_WIDTH,   HBM_ADDR_WIDTH, SourceWidth, SinkWidth, host_element),
    `TL_DECLARE_HOST_PORT(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, host_scale)
);

    localparam BYTES_PER_ROW =  (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) * MLEN * Parallel_Rd_Dim / 8;
    initial begin
        assert (MLEN == VLEN) else $fatal("MLEN and VLEN should be equal for hbm controller");
    end

    logic start_prefetch;
    logic [HBM_ADDR_WIDTH - 1 : 0] hbm_addr_out;
    logic ready_for_prefetch;
    logic delayed_continuous_prefetch_m_en;

    always_ff @(posedge clk) begin
        if (rst) begin
            start_prefetch              <= 1'b0;
            ready_for_prefetch          <= 1'b0;
            addr_to_prefetch            <= 'b0;
            addr_for_prefetched_data    <= 'b0;
            delayed_continuous_prefetch_m_en <= 1'b0;
        end else begin
            delayed_continuous_prefetch_m_en <= continuous_prefetch_m_en;
            addr_to_prefetch    <= delayed_continuous_prefetch_m_en ? addr_for_prefetched_data + m_sram_continuous_prefetch_counter * BYTES_PER_ROW : hbm_addr_out;
            ready_for_prefetch  <= hbm_prefetch_en;

            if(ready_for_prefetch && !hbm_prefetch_content_exist) begin
                addr_for_prefetched_data <= addr_to_prefetch;
                start_prefetch <= 1'b1;
            end else begin
                start_prefetch <= 1'b0;
            end
        end
    end

    // Mapping inputted Addr to HBM address
    address_mapper #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .ADR_OPERAND_WIDTH(ADR_OPERAND_WIDTH),
        .HBM_ADDR_WIDTH(HBM_ADDR_WIDTH),
        .HBM_ADDR_REG_NUM(HBM_ADDR_REG_NUM)
    ) address_mapper_inst (
        .clk(clk),
        .rst(rst),
        .mapp_addr_en   (hbm_write_en || hbm_prefetch_en),
        .set_addr_en    (set_addr_reg_en),
        .addr_offset     (addr_for_prefetched_data),
        .addr_in_a      (addr_in_a),
        .addr_in_b      (addr_in_b),
        .read_operand   (addr_reg_read_operand),
        .write_operand  (addr_reg_write_operand),
        .hbm_addr_out   (hbm_addr_out)
    );

    `TL_DECLARE(ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, tl_element);
    `TL_DECLARE(HBM_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, adapted_tl_element);
    `TL_BIND_HOST_PORT(host_element, adapted_tl_element);

    // TL for element
    tl_master #(
        .DataWidth(ELE_WIDTH),
        .AddrWidth(HBM_ADDR_WIDTH),
        .SourceWidth(SourceWidth),
        .SinkWidth(SinkWidth)
    ) element_master (
        .clk(clk),
        .rst(rst),
        // Control signals
        .req_en(start_prefetch),
        .write_en(write_en),
        .fetch_addr(hbm_addr_out),
        .fetch_data(prefetch_element),
        .write_data(hbm_write_element),
        .fetch_data_valid(prefetch_data_valid),

        `TL_CONNECT_HOST_PORT(host, tl_element)
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
        `TL_CONNECT_DEVICE_PORT(host, tl_element),
        `TL_CONNECT_HOST_PORT(device, adapted_tl_element)
    );

    

    // TL for scale
    `TL_DECLARE(SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, tl_scale);
    `TL_DECLARE(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, adapted_tl_scale);
    `TL_BIND_HOST_PORT(host_scale, adapted_tl_scale);

    // Converting to TileLink
    tl_master #(
        .DataWidth(SCALE_WIDTH),
        .AddrWidth(HBM_ADDR_WIDTH),
        .SourceWidth(SourceWidth),
        .SinkWidth(SinkWidth)
    ) scale_master (
        .clk(clk),
        .rst(rst),

        // Control signals
        .req_en(hbm_prefetch_en),
        .write_en(write_en),
        .fetch_addr(addr_for_prefetched_data + SCALE_DATA_OFFSET),
        .fetch_data(prefetch_scale),
        .write_data(hbm_write_scale),
        `TL_CONNECT_HOST_PORT(host, tl_scale)
    );

    tl_adapter #(
        .HostDataWidth(SCALE_WIDTH),
        .DeviceDataWidth(HBM_SCALE_WIDTH),
        .AddrWidth(HBM_ADDR_WIDTH),
        .SourceWidth(SourceWidth),
        .SinkWidth(SinkWidth),
        .HostFifo(1),
        .DeviceFifo(1)
    ) adapter_for_scale (
        .clk_i(clk),
        .rst_ni(!rst),
        // TileLink Interface
        `TL_CONNECT_DEVICE_PORT(host, tl_scale ),
        `TL_CONNECT_HOST_PORT(device, adapted_tl_scale)
    );

endmodule