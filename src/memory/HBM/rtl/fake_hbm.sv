`timescale 1ns / 1ps
`include "tl_util.svh"

/*
Module      : Fake TileLink interface HBM, used for simulation.
Status      : Under Development
*/


module fake_hbm #(
    parameter int ADDR_WIDTH        = 32,
    parameter int DATA_WIDTH        = 64,
    parameter int BRAM_ADDR_WIDTH   = 20,
    parameter int SourceWidth      = 1,
    parameter int SinkWidth        = 1,
    parameter int ID_WIDTH          = 8,
    parameter     MemInitFile       = ""

)(
    input logic clk,
    input logic rst,

    // TileLink Interface
    `TL_DECLARE_DEVICE_PORT(DATA_WIDTH, ADDR_WIDTH, SourceWidth, SinkWidth, host)

);

logic [ADDR_WIDTH-1:0] bram_addr;
logic [DATA_WIDTH-1:0] bram_wdata;
logic [DATA_WIDTH/8-1:0] bram_wmask;
logic [DATA_WIDTH-1:0] bram_rdata;
logic bram_en;
logic bram_we;


tl_adapter_bram #(
    .AddrWidth(ADDR_WIDTH),
    .DataWidth(DATA_WIDTH),
    .SourceWidth(SourceWidth),
    .BramAddrWidth(BRAM_ADDR_WIDTH)
) tl_adapter (
    .clk_i(clk),
    .rst_ni(rst),

    // TileLink Interface
    `TL_CONNECT_DEVICE_PORT(host, host),

    // Memory Interface
    .bram_en_o(bram_en),
    .bram_we_o(bram_we),
    .bram_addr_o(bram_addr),
    .bram_wmask_o(bram_wmask),
    .bram_wdata_o(bram_wdata),
    .bram_rdata_i(bram_rdata)
);

bram #(
    .DATA_WIDTH(DATA_WIDTH),
    .ADDR_WIDTH(BRAM_ADDR_WIDTH),
    .INIT_FILE(MemInitFile)
) bram_inst (
    .clk(clk),
    .bram_en_o(bram_en),
    .bram_addr_o(bram_addr),
    .bram_wdata_o(bram_wdata),
    .bram_wmask_o(bram_wmask),
    .bram_rdata_i(bram_rdata)
);




endmodule