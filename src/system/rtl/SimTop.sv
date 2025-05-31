`timescale 1ns / 1ps
`include "tl_util.svh"
`include "global_define.vh"
`include "configuration.svh"
`include "tl_pkg.svh"

/*
Module      : Sim Top Module
*/

module SimTop#(
    parameter   INSTRUCTION_LENGTH = 32,
    parameter string    FAKE_HBM_ELEMENT_INIT_FILE    = "",
    parameter string    FAKE_HBM_SCALE_INIT_FILE      = "",
    parameter string    FP_MEM_INIT_FILE              = "",
    parameter string    FIXED_MEM_INIT_FILE           = ""
) (
    input logic clk,
    input logic rst,

    input   logic [INSTRUCTION_LENGTH - 1 : 0] instruction,
    input   logic instruction_valid,
    output  logic instruction_ready
);

import simulation_pkg::*;

`TL_DECLARE(HBM_ELE_WIDTH,  HBM_ADDR_WIDTH, SourceWidth, SinkWidth, element_link);
`TL_DECLARE(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, scale_link);

// Processor
coprocessor #(
    .FP_MEM_INIT_FILE(FP_MEM_INIT_FILE),
    .FIXED_MEM_INIT_FILE(FIXED_MEM_INIT_FILE)
) dut (
    .clk(clk),
    .rst(rst),
    .instruction(instruction),
    .instruction_valid(instruction_valid),
    .instruction_ready(instruction_ready),
    `TL_CONNECT_HOST_PORT(out_element,  element_link),
    `TL_CONNECT_HOST_PORT(out_scale,    scale_link)
);

fake_hbm #(
    .ADDR_WIDTH         (HBM_ADDR_WIDTH),
    .DATA_WIDTH         (HBM_ELE_WIDTH),
    .BRAM_ADDR_WIDTH    (FAKE_HBM_ADDR_WIDTH),
    .SourceWidth        (SourceWidth),
    .SinkWidth          (SinkWidth),
    .MemInitFile        (FAKE_HBM_ELEMENT_INIT_FILE)
) fake_hbm_element (
    .clk(clk),
    .rst(rst),
    `TL_CONNECT_DEVICE_PORT(host, element_link)
);


fake_hbm #(
    .ADDR_WIDTH         (HBM_ADDR_WIDTH),
    .DATA_WIDTH         (HBM_SCALE_WIDTH),
    .BRAM_ADDR_WIDTH    (FAKE_HBM_ADDR_WIDTH),
    .SourceWidth        (SourceWidth),
    .SinkWidth          (SinkWidth),
    .MemInitFile        (FAKE_HBM_SCALE_INIT_FILE)
) fake_hbm_scale (
    .clk(clk),
    .rst(rst),
    `TL_CONNECT_DEVICE_PORT(host, scale_link)
);



endmodule