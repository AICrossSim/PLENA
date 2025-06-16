/*
Module      : Top Level SRAM design solely for Matrix Machine 
Timing      : Sequential Logic, x cycle for read/write process.
Description :
            : This module supports parallel row / column read and write.
            : The addressing mode is Little Endian.
Status      : TODO
*/


`timescale 1ns/1ps

module matrix_sram_without_rounding #(
    // MX-FP Data Format
    parameter MXFP_EXP_WIDTH    = 4,
    parameter MXFP_MANT_WIDTH   = 3,
    parameter MXFP_SCALE_WIDTH  = 8,

    // Dimension
    parameter   MLEN              = 8,                                // The dimension of the sub SRAM, or the TileSize of the matrix.
    parameter   BLOCK_DIM         = 4,                                
    localparam  BLOCK_NUM         = MLEN / BLOCK_DIM
    // 

) (

);


endmodule