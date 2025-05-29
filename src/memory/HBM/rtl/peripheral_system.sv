`timescale 1ns / 1ps
`include "tl_util.svh"
`include "tl_pkg.svh"

/*
Module      : Peripheral System (Testng Purpose)
Description : This module is used to test the collaboration of the HBM controller and TileLink master
Status      : Under Development (Need to consider TileLink)
*/


module peripheral_system #(
    parameter ADDR_WIDTH = 32,
    parameter DATA_WIDTH = 64,
    parameter BRAM_ADDR_WIDTH           = 32,
    parameter int unsigned SourceWidth  = 1,
    parameter int unsigned SinkWidth    = 1,
    parameter string INIT_FILE  = "/home/george/Coprocessor_for_Llama/src/memory/HBM/test/simple_benchmark.txt"
)(
    input logic clk,
    input logic rst,

    output  logic [DATA_WIDTH-1:0]  fetch_data,
    input   logic [ADDR_WIDTH-1:0]  fetch_addr,
    input   logic                   fetch_en,
    input   logic                   write_en,
    input   logic [DATA_WIDTH-1:0]  write_data
);

`TL_DECLARE(DATA_WIDTH, ADDR_WIDTH, SourceWidth, SinkWidth, mem);

tl_master #(
    .DataWidth(DATA_WIDTH),
    .AddrWidth(ADDR_WIDTH),
    .SourceWidth(SourceWidth),
    .SinkWidth(SinkWidth)
) tl_master_init (
    .clk(clk),
    .rst(rst),

    // Control signals
    .req_en(fetch_en),
    .fetch_addr(fetch_addr),
    .fetch_data(fetch_data),

    .write_en(write_en),
    .write_data(write_data),

    `TL_CONNECT_HOST_PORT(host, mem)
);


fake_hbm #(
    .ADDR_WIDTH(ADDR_WIDTH),
    .DATA_WIDTH(DATA_WIDTH),
    .BRAM_ADDR_WIDTH(BRAM_ADDR_WIDTH),
    .SourceWidth(SourceWidth),
    .SinkWidth(SinkWidth),
    .MemInitFile(INIT_FILE)
) fake_hbm (
    .clk(clk),
    .rst(rst),

    `TL_CONNECT_DEVICE_PORT(host, mem)
);




endmodule