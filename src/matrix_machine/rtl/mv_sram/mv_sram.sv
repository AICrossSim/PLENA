`timescale 1ns/1ps


module mv_sram #(
    parameter int DataWidth = 4, 
    parameter int SRAM_Depth = 128,
    parameter int MLEN = 8,                                             // The TileSize of the matrix.
    parameter int Parallel_Rd_Amount = 2,                               // The number of row/col read in parallel
    localparam int AdrWidth                   = $clog2(SRAM_Depth),     // Address Space for the SRAM
) (
    input  logic clk,
    input  logic rst,
    input  logic req,
    input  logic write_en,
    input  logic transposed_read,
    input  logic [AddrLen-1:0] sram_addr,
    input  logic stall,                      // Indicates whether the read is stalled
    input  logic read_en,
    input  logic [Parallel_Rd_Amount * MLEN * DataWidth - 1:0] in_data,  // Packed input vector
    output logic [DataWidth-1:0] out_data [MLEN*MLEN-1:0] // Unpacked output array
);





endmodule