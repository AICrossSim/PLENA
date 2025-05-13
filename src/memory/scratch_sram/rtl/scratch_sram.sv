`timescale 1ns/1ps

/*
Module      : Top Level SRAM design for scratchpad
Timing      : Sequential Logic, 1 cycle for read/write process.
Description :
            : This module supports two port reading
            : The addressing mode is Little Endian.
Status      :
*/

module scratch_sram #(
    // MX-FP Data Format
    parameter MXFP_EXP_WIDTH    = 4,
    parameter MXFP_MANT_WIDTH   = 3,
    parameter MXFP_SCALE_WIDTH  = 8,

    // Dimension
    parameter   VLEN              = 8,                                  // The dimension of the sub SRAM, or the TileSize of the matrix.
    parameter   BLOCK_DIM         = 4,                                
    localparam  BLOCK_NUM         = VLEN / BLOCK_DIM,

    // SRAM
    parameter   SRAM_DEPTH        = 128,
    localparam  AddrLen           = $clog2(SRAM_DEPTH)                // Address Space for the SRAM

)(
    input   logic clk,
    input   logic rst,

    input   logic req_a,
    input   logic write_en_a,
    input   logic [AddrLen-1:0] sram_addr_a,
    input   logic [VLEN - 1 : 0]        [MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]      element_in_a,
    input   logic [BLOCK_NUM - 1 : 0]   [MXFP_SCALE_WIDTH - 1 : 0]                  scale_in_a,
    input   logic [BLOCK_NUM - 1 : 0]                                               mask_in_a,
    output  logic [VLEN - 1 : 0]        [MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]      element_out_a,
    output  logic [BLOCK_NUM - 1 : 0]   [MXFP_SCALE_WIDTH - 1 : 0]                  scale_out_a,

    input   logic req_b,
    input   logic write_en_b,
    input   logic [AddrLen-1:0] sram_addr_b,
    input   logic [VLEN - 1 : 0]        [MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]      element_in_b,
    input   logic [BLOCK_NUM - 1 : 0]   [MXFP_SCALE_WIDTH - 1 : 0]                  scale_in_b,
    input   logic [BLOCK_NUM - 1 : 0]                                               mask_in_b,
    output  logic [VLEN - 1 : 0]        [MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]      element_out_b,
    output  logic [BLOCK_NUM - 1 : 0]   [MXFP_SCALE_WIDTH - 1 : 0]                  scale_out_b

);



// ELement Storage Data
prim_generic_ram_2p #(
    .Width((MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) * VLEN),
    .Depth(SRAM_DEPTH),
    .DataBitsPerMask((MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) * BLOCK_DIM),   // Write mask is able to control the single element
    .MemInitFile("")
) element_storage (
    .clk_a_i(clk),
    .clk_b_i(clk),

    .a_req_i(req_a),
    .a_write_i(write_en_a),
    .a_addr_i(sram_addr_a),
    .a_wdata_i(element_in_a),
    .a_wmask_i(mask_in_a),
    .a_rdata_o(element_out_a),

    .b_req_i(req_b),
    .b_write_i(write_en_b),
    .b_addr_i(sram_addr_b),
    .b_wdata_i(element_in_b),
    .b_wmask_i(mask_in_b),
    .b_rdata_o(element_out_b),

    // Unused
    .cfg_i('0),
    .cfg_rsp_o()
);

// Scale Storage Data
prim_generic_ram_2p #(
    .Width(MXFP_SCALE_WIDTH * BLOCK_NUM),
    .Depth(SRAM_DEPTH),
    .DataBitsPerMask(MXFP_SCALE_WIDTH),
    .MemInitFile("")
) scale_storage (
    .clk_a_i(clk),
    .clk_b_i(clk),

    .a_req_i(req_a),
    .a_write_i(write_en_a),
    .a_addr_i(sram_addr_a),
    .a_wdata_i(scale_in_a),
    .a_wmask_i(mask_in_a),
    .a_rdata_o(scale_out_a),

    .b_req_i(req_b),
    .b_write_i(write_en_b),
    .b_addr_i(sram_addr_b),
    .b_wdata_i(scale_in_b),
    .b_wmask_i(mask_in_b),
    .b_rdata_o(scale_out_b),

    // Unused
    .cfg_i('0),
    .cfg_rsp_o()
);



endmodule