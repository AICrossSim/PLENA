`timescale 1ns / 1ps
`include "tl_util.svh"
`include "global_define.vh"
`include "configuration.svh"
`include "tl_pkg.svh"

/*
Module      : Sim Top Module
*/

module SimTop import instruction_pkg::*; #(
    parameter   INSTRUCTION_LENGTH = 32,
    parameter string    FAKE_HBM_ELEMENT_INIT_FILE    = "",
    parameter string    FAKE_HBM_SCALE_INIT_FILE      = "",
    parameter string    FP_MEM_INIT_FILE              = "",
    parameter string    FIXED_MEM_INIT_FILE           = "",
    parameter string    VECTOR_MEM_RESULT_FILE        = "",
    parameter string    HBM_ADDR_MAPPER_FILE          = "",
    parameter string    FAKE_HBM_ELEMENT_WRITE_M_FILE = "",
    parameter string    FAKE_HBM_ELEMENT_WRITE_V_FILE = "",
    parameter string    FAKE_HBM_SCALE_WRITE_M_FILE   = "",
    parameter string    FAKE_HBM_SCALE_WRITE_V_FILE   = ""
) (
    input logic clk,
    input logic rst,

    input   logic [INSTRUCTION_LENGTH - 1 : 0] instruction,
    input   logic instruction_valid,
    output  logic instruction_ready
);

import simulation_pkg::*;
import configuration_pkg::*;


`TL_DECLARE(HBM_ELE_WIDTH,  HBM_ADDR_WIDTH, SourceWidth, SinkWidth, m_element_link);
`TL_DECLARE(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, m_scale_link);
`TL_DECLARE(HBM_ELE_WIDTH,  HBM_ADDR_WIDTH, SourceWidth, SinkWidth, v_element_link);
`TL_DECLARE(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, v_scale_link);

// Processor
coprocessor #(
    .FP_MEM_INIT_FILE(FP_MEM_INIT_FILE),
    .FIXED_MEM_INIT_FILE(FIXED_MEM_INIT_FILE),
    .V_SRAM_RESULT_FILE(VECTOR_MEM_RESULT_FILE),
    .HBM_ADDR_MAPPER_FILE(HBM_ADDR_MAPPER_FILE)
) dut (
    .clk(clk),
    .rst(rst),
    .instruction            (instruction),
    .instruction_valid      (instruction_valid),
    .instruction_ready      (instruction_ready),
    `TL_CONNECT_HOST_PORT   (m_out_element,  m_element_link),
    `TL_CONNECT_HOST_PORT   (m_out_scale,    m_scale_link),
    `TL_CONNECT_HOST_PORT   (v_out_element,  v_element_link),
    `TL_CONNECT_HOST_PORT   (v_out_scale,    v_scale_link)
);

fake_hbm #(
    .ADDR_WIDTH         (HBM_ADDR_WIDTH),
    .DATA_WIDTH         (HBM_ELE_WIDTH),
    .BRAM_ADDR_WIDTH    (FAKE_HBM_ADDR_WIDTH),
    .SourceWidth        (SourceWidth),
    .SinkWidth          (SinkWidth),
    .MemInitFile        (FAKE_HBM_ELEMENT_INIT_FILE),
    .ResultFile         (FAKE_HBM_ELEMENT_WRITE_M_FILE)
) fake_hbm_m_element (
    .clk(clk),
    .rst(rst),
    `TL_CONNECT_DEVICE_PORT(host, m_element_link)
);


fake_hbm #(
    .ADDR_WIDTH         (HBM_ADDR_WIDTH),
    .DATA_WIDTH         (HBM_SCALE_WIDTH),
    .BRAM_ADDR_WIDTH    (FAKE_HBM_ADDR_WIDTH),
    .SourceWidth        (SourceWidth),
    .SinkWidth          (SinkWidth),
    .MemInitFile        (FAKE_HBM_SCALE_INIT_FILE),
    .ResultFile         (FAKE_HBM_SCALE_WRITE_M_FILE)
) fake_hbm_m_scale (
    .clk(clk),
    .rst(rst),
    `TL_CONNECT_DEVICE_PORT(host, m_scale_link)
);

fake_hbm #(
    .ADDR_WIDTH         (HBM_ADDR_WIDTH),
    .DATA_WIDTH         (HBM_ELE_WIDTH),
    .BRAM_ADDR_WIDTH    (FAKE_HBM_ADDR_WIDTH),
    .SourceWidth        (SourceWidth),
    .SinkWidth          (SinkWidth),
    .MemInitFile        (FAKE_HBM_ELEMENT_INIT_FILE),
    .ResultFile         (FAKE_HBM_ELEMENT_WRITE_V_FILE)
) fake_hbm_v_element (
    .clk(clk),
    .rst(rst),
    `TL_CONNECT_DEVICE_PORT(host, v_element_link)
);

fake_hbm #(
    .ADDR_WIDTH         (HBM_ADDR_WIDTH),
    .DATA_WIDTH         (HBM_SCALE_WIDTH),
    .BRAM_ADDR_WIDTH    (FAKE_HBM_ADDR_WIDTH),
    .SourceWidth        (SourceWidth),
    .SinkWidth          (SinkWidth),
    .MemInitFile        (FAKE_HBM_SCALE_INIT_FILE),
    .ResultFile         (FAKE_HBM_SCALE_WRITE_V_FILE)
) fake_hbm_v_scale (
    .clk(clk),
    .rst(rst),
    `TL_CONNECT_DEVICE_PORT(host, v_scale_link)
);



endmodule