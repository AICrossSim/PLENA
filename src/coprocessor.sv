`timescale 1ns / 1ps

/*
Module      : Coprocessor Top Module
Timing      : Sequential, Takes x cycles to compute the dot product
Description : This module conducts the operation m(MLEN, MLEN) @ v(MLEN, 1) + o (MLEN, 1)
Status      : Under Testing
*/

module coprocessor #(
    // MX-FP Data Format
    parameter   MXFP_MANT_WIDTH   = 8,
    parameter   MXFP_EXP_WIDTH    = 4,
    parameter   MX_FP_SCALE_WIDTH = 8,

    // Dimensions
    parameter   MLEN              = 8,
    parameter   BLOCK_DIM         = 4,
    localparam  BLOCK_NUM         = MLEN / BLOCK_DIM,

    // Precision Control
    parameter   PRODUCT_EXT_EXP_WIDTH   = 1,
    parameter   PRODUCT_EXT_MANT_WIDTH  = 0,
    parameter   BLOCK_ADD_EXT_EXP_WIDTH       = 1,  // Note: this param control precision for both blockwise addition within adder tree and the blockwise adder
    parameter   BLOCK_ADD_EXT_MANT_WIDTH      = 0,
    parameter   FP_ADD_EXT_EXP_WIDTH       = 1,
    parameter   FP_ADD_EXT_MANT_WIDTH      = 0,

    // Intermediate FP Control
    parameter   ROUND_FP_EN            = 0,
    parameter   ROUND_FP_EXP_WIDTH     = 4,
    parameter   ROUND_FP_MANT_WIDTH    = 3, 

    // Memory Dimensions
    parameter   Matrix_Parallel_Rd_Dim = 2
    parameter   SRAM_DEPTH        = 128

) (
    input   logic clk,
    input   logic rst

)


// Computation
matrix_machine #(
    .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
    .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
    .MX_FP_SCALE_WIDTH(MX_FP_SCALE_WIDTH),
    .MLEN(MLEN),
    .BLOCK_DIM(BLOCK_DIM),
    .BLOCK_NUM(BLOCK_NUM),
    .PRODUCT_EXT_EXP_WIDTH(PRODUCT_EXT_EXP_WIDTH),
    .PRODUCT_EXT_MANT_WIDTH(PRODUCT_EXT_MANT_WIDTH),
    .BLOCK_ADD_EXT_EXP_WIDTH(BLOCK_ADD_EXT_EXP_WIDTH),
    .BLOCK_ADD_EXT_MANT_WIDTH(BLOCK_ADD_EXT_MANT_WIDTH),
    .FP_ADD_EXT_EXP_WIDTH(FP_ADD_EXT_EXP_WIDTH),
    .FP_ADD_EXT_MANT_WIDTH(FP_ADD_EXT_MANT_WIDTH)
) matrix_machine (
    .clk(clk),
    .rst(rst),

    m_element(),
    m_scale(),
    m_valid(),
    m_ready(),

    v_element(),
    v_scale(),
    v_valid(),
    v_ready(),

    o_element(),
    o_scale(),
    o_valid(),
    o_ready(),

    out_element(),
    out_scale(),
    out_valid(),
    out_ready()
);




// Mempory 

matrix_sram_with_rounding #(
    .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
    .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
    .MXFP_SCALE_WIDTH(MX_FP_SCALE_WIDTH),
    .MLEN(MLEN),
    .BLOCK_DIM(BLOCK_DIM),
    .SRAM_DEPTH(SRAM_DEPTH),
    .PARALLEL_DIM(Matrix_Parallel_Rd_Dim)
) matrix_sram (
    .clk(clk),
    .rst(rst),
    .req(req),
    .transposed_read(),
    .write_en(),
    .write_response(),
    .sram_addr(),
    .element_in(),
    .scale_in(),
    .element_out(),
    .scale_out()
);


// Vector SRAM

scratch_sram #(
    .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
    .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
    .MXFP_SCALE_WIDTH(MX_FP_SCALE_WIDTH),
    .VLEN(MLEN),
    .BLOCK_DIM(BLOCK_DIM),
    .BLOCK_NUM(BLOCK_NUM),
    .SRAM_DEPTH(SRAM_DEPTH)
) vector_sram (
    .clk(clk),
    .rst(rst),
    .req_a(),
    .write_en_a(),
    .sram_addr_a(),
    .element_in_a(),
    .scale_in_a(),
    .mask_in_a(),
    .element_out_a(),
    .scale_out_a(),
    
    .req_b(),
    .write_en_b(),
    .sram_addr_b(),
    .element_in_b(),
    .scale_in_b(),
    .mask_in_b(),
    .element_out_b(),
    .scale_out_b()
)



endmodule