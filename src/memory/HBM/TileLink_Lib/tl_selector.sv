`timescale 1ns / 1ps
`include "tl_util.svh"
`include "tl_pkg.svh"
/*
Module      : TL_Selector
Timing      : Combinatorial Logic
Status      : Under Development (Need to consider TileLink)
Description : This module is used to select between two TileLink interfaces.
Status      : Under Development
*/


module tl_selector #(
    parameter int   DataWidth = 32,
    parameter int   AddrWidth = 32,
    parameter int   HBM_ELE_WIDTH = 128,
    parameter int   HBM_SCALE_WIDTH = 128,
    parameter int   HBM_ADDR_WIDTH = 32,
    parameter int   SourceWidth = 4, 
    parameter int   SinkWidth = 4
)(
    input logic clk,
    input logic rst,
    input logic select, // 0: Select device_1, 1: Select device_2
    `TL_DECLARE_DEVICE_PORT (DataWidth, AddrWidth, SourceWidth, SinkWidth, device_1),
    `TL_DECLARE_DEVICE_PORT (DataWidth, AddrWidth, SourceWidth, SinkWidth, device_2),
    `TL_DECLARE_HOST_PORT   (DataWidth, AddrWidth, SourceWidth, SinkWidth, host_out)
);

    `TL_DECLARE(DataWidth, AddrWidth, SourceWidth, SinkWidth, determined_host_out);

    // Out Select
    assign determined_host_out_a_valid_o = select ? device_2_a_valid_i : device_1_a_valid_i;
    assign determined_host_out_a_o       = select ? device_2_a_i : device_1_a_i;
    assign determined_host_out_b_ready_o = select ? device_2_b_ready_i : device_1_b_ready_i;

    assign determined_host_out_c_valid_o = select ? device_2_c_valid_i : device_1_c_valid_i;
    assign determined_host_out_c_o       = select ? device_2_c_i : device_1_c_i;
    assign determined_host_out_d_ready_o = select ? device_2_d_ready_i : device_1_d_ready_i;
    assign determined_host_out_e_valid_o = select ? device_2_e_valid_i : device_1_e_valid_i;
    assign determined_host_out_e_o       = select ? device_2_e_i : device_1_e_i;

    // Input Fill
    assign device_1_a_ready_o = !select && determined_host_out_a_ready_i;
    assign device_2_a_ready_o = select  && determined_host_out_a_ready_i;
    assign device_1_b_valid_o = !select && determined_host_out_b_valid_i;
    assign device_2_b_valid_o = select  && determined_host_out_b_valid_i;
    assign device_1_b_o       = !select  ? determined_host_out_b_i : '0;
    assign device_2_b_o       = select   ? determined_host_out_b_i : '0;
    assign device_1_c_ready_o = !select && determined_host_out_c_ready_i;
    assign device_2_c_ready_o = select  && determined_host_out_c_ready_i;
    assign device_1_d_valid_o = !select && determined_host_out_d_valid_i;
    assign device_2_d_valid_o = select  && determined_host_out_d_valid_i;
    assign device_1_d_o       = !select  ? determined_host_out_d_i : '0;
    assign device_2_d_o       = select   ? determined_host_out_d_i : '0;
    assign device_1_e_ready_o = !select && determined_host_out_e_ready_i;
    assign device_2_e_ready_o = select  && determined_host_out_e_ready_i;

// Introduce 1 clk delay
    tl_fifo_sync #(
        .SourceWidth   (SourceWidth),
        .SinkWidth     (SinkWidth),
        .AddrWidth     (AddrWidth),
        .DataWidth     (DataWidth)
    ) tl_fifo_sync_inst (
        .clk_i(clk),
        .rst_ni(rst),
        `TL_BIND_DEVICE_PORT(host, determined_host_out),
        `TL_BIND_HOST_PORT  (device, host_out)
    );

endmodule