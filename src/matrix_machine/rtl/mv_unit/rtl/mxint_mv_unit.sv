/*
Module      : mxint matrix vector mult units
Description : This module does a matrix @ vector + offset vector.

              The dimensions for the matrix multiplcation are:
              (MLEN, MLEN) * (MLEN, 1) + (MLEN, 1) = (MLEN, 1)

*/


`timescale 1ns / 1ps

module mxint_mv_unit #(
    // Total dimensions
    parameter MLEN = 8,
    parameter Parallel_Rd_Dim
    parameter MAN_WIDTH = 8,
    parameter Parallel_Rd_Dim = 4,
    parameter EXP_WIDTH = 4,
    parameter MX_BLOCK_SIZE = 4,
    localparam M_MX_EXP_PARTIAL_AMOUNT = (MLEN * Parallel_Rd_Amount) / MX_BLOCK_SIZE,
    localparam M_MX_EXP_AMOUNT = ((MLEN * MLEN) / MX_BLOCK),
    localparam V_MX_EXP_AMOUNT = (MLEN / MX_BLOCK),
) (
    input logic clk,
    input logic rst,

    // Matix - row-major order
    input  logic [MLEN*Parallel_Rd_Dim-1:0]         [MAN_WIDTH-1:0] matrix_m_data,
    input  logic [M_MX_EXP_PARTIAL_AMOUNT-1:0]      [EXP_WIDTH-1:0] matrix_e_data,
    input  logic                   p_rd_matrix_valid,
    output logic                   p_rd_matrix_ready,

    // Vector - row-major order
    input  logic [MLEN-1:0]             [MAN_WIDTH-1:0] vector_m_data,
    input  logic [V_MX_EXP_AMOUNT-1:0]  [EXP_WIDTH-1:0] vector_e_data,
    input  logic                   vector_valid,
    output logic                   vector_ready,

    // Offset - row-major order
    input  logic [MLEN-1:0]             [MAN_WIDTH-1:0] offset_m_data,
    input  logic [V_MX_EXP_AMOUNT-1:0]  [EXP_WIDTH-1:0] offset_e_data,
    input  logic                   offset_valid,
    output logic                   offset_ready,

    // Output
    output logic [MLEN-1:0]             [MAN_WIDTH-1:0] out_m_data,
    output logic [V_MX_EXP_AMOUNT-1:0]  [EXP_WIDTH-1:0] out_e_data,
    output logic                     out_valid,
    input  logic                     out_ready
);
  initial begin

  end

  // Keep 


  endmodule