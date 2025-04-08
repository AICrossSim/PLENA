/*
Module      : mxint matrix vector mult units
Description : This module does a matrix @ vector + offset vector.

              The dimensions for the matrix multiplcation are:
              (MLEN, MLEN) * (MLEN, 1) + (MLEN, 1) = (MLEN, 1)

*/


`timescale 1ns / 1ps

module mv_unit #(
    // MX-FP Data Format
    parameter   MXFP_MANT_WIDTH   = 8,
    parameter   MXFP_EXP_WIDTH    = 4,
    parameter   MX_FP_SCALE_WIDTH = 8,

    // Total dimensions
    parameter   MLEN              = 8,
    parameter   BLOCK_DIM         = 4,
    localparam  BLOCK_NUM         = MLEN / BLOCK_DIM,

    // Precision Control
    parameter   PRODUCT_EXT_EXP_WIDTH   = 1,
    parameter   PRODUCT_EXT_MANT_WIDTH  = 0,
    parameter   BLOCK_ADD_EXT_EXP_WIDTH       = 1,
    parameter   BLOCK_ADD_EXT_MANT_WIDTH      = 0,
    parameter   FP_ADD_EXT_EXP_WIDTH       = 1,
    parameter   FP_ADD_EXT_MANT_WIDTH      = 0,

    // Intermediate FP Control
    parameter   ROUND_FP_EN            = 0,
    parameter   ROUND_FP_EXP_WIDTH     = 4,
    parameter   ROUND_FP_MANT_WIDTH    = 3, 

) (
    input logic clk,
    input logic rst,

    // Matix - row-major order
    input  logic [MLEN*MLEN-1:0]                    [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      matrix_element_data,
    input  logic [BLOCK_NUM*BLOCK_NUM-1:0]          [MX_FP_SCALE_WIDTH-1:0]                     matrix_scale_data,
    input  logic                   m_data_valid,
    output logic                   m_data_ready,

    // Vector - row-major order
    input  logic [MLEN-1:0]             [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      vector_element_data,
    input  logic [BLOCK_NUM-1:0]        [MX_FP_SCALE_WIDTH-1:0]                     vector_scale_data,
    input  logic                   v_data_valid,
    output logic                   v_data_ready,

    // Offset - row-major order
    input  logic [MLEN-1:0]             [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      offset_element_data,
    input  logic [BLOCK_NUM-1:0]        [MX_FP_SCALE_WIDTH-1:0]                     offset_scale_data,
    input  logic                   o_data_valid,
    output logic                   o_data_ready,

    // Output
    output logic [MLEN-1:0]             [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      out_element_data,
    output logic [BLOCK_NUM-1:0]        [MX_FP_SCALE_WIDTH-1:0]                     out_scale_data,
    output logic                     out_valid,
    input  logic                     out_ready
);
  initial begin

  end

  // Keep 


  endmodule