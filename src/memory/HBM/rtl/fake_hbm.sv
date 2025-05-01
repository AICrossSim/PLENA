`timescale 1ns / 1ps
`include "operation.svh"
`include "tl_util.svh"

/*
Module      : Fake TileLink interface HBM, used for simulation.
Status      : Under Development
*/


module fake_hbm #(
    parameter int ADDR_WIDTH = 32,
    parameter int DATA_WIDTH = 64,
    parameter int BEAT_BYTES = 8,
    parameter int BEAT_SIZE = $clog2(BEAT_BYTES),
    parameter int ID_WIDTH = 8,
    parameter int QUEUE_DEPTH = 16
)(
    input logic clk,
    input logic rst,

    // TileLink Interface
    `TL_DECLARE_DEVICE_PORT(DataWidth, AddrWidth, SourceWidth, 1, host),

    // Memory Interface
    output logic [ADDR_WIDTH - 1 : 0] mem_addr,
    output logic [DATA_WIDTH - 1 : 0] mem_data_out,
    output logic mem_valid,
    input logic mem_ready
);



endmodule