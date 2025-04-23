/*
Module      : SRAM Unit that support parallel row/column read/write
Timing      : Sequential Logic : Require x cycles for the read process.
Description : This module supports parallel row / column read and write.
            : The addressing mode is Little Endian.

Limitation  : The write dimension is constrained to be the same as the parallel read dimension. 
The reason is that, parrallel rd involves the data stored as the (Parallel_Rd_Dim, Parallel_Rd_Dim) data type. Hence, for simplicity, 
we assume the Parallel_Wr_Dim is the same as the Parallel_Rd_Dim.
Status      : Passed Simple Row/Col Read/Write Tests
*/


`timescale 1ns/1ps

module biaccess_sram #(
    parameter   int DataWidth = 4, 
    parameter   int SRAM_DEPTH = 128,
    parameter   int MLEN = 8,                                       // The TileSize of the matrix.
    parameter   int Parallel_Rd_Dim = 2,                            // The number of row/col read in parallel
    localparam  int AddrLen = $clog2(SRAM_DEPTH)                    // Address Space for the SRAM 
) (
    input  logic clk,

    // input  logic rst,
    input  logic req,
    input  logic transposed_read,
    input  logic write_en,
    // input  logic last_write,
    output logic write_response,

    input  logic [AddrLen-1:0] sram_addr,                                   // Indicates whether the read is stalled
    input  logic [Parallel_Rd_Dim * MLEN * DataWidth - 1:0] write_data,     // Packed input vector
    output logic [Parallel_Rd_Dim * MLEN-1:0] [DataWidth-1:0] out_data      // Unpacked output array
);


// -----
// Params
// -----
localparam int SubTileWidth                 = DataWidth * (Parallel_Rd_Dim ** 2);       // The width of each element in the sub SRAM
localparam int SubSRAM_Amount               = MLEN / Parallel_Rd_Dim;                   // The dimension of the sub SRAM, or the TileSize of the matrix.


// -----
// Wires
// -----
logic [SubSRAM_Amount - 1 : 0] [SubTileWidth - 1 : 0]   sub_sram_wdata, sub_sram_rdata ;

logic [SubSRAM_Amount-1:0] individual_subs_sram_write_response ;
logic [SubSRAM_Amount-1:0] individual_subs_sram_read_valid ;
logic read_data_valid;

// Control Signals
always_comb begin
    write_response = 1'b1;
    read_data_valid = 1'b1;
    write_response =  (individual_subs_sram_write_response == {SubSRAM_Amount{1'b1}});
    read_data_valid = (individual_subs_sram_read_valid == {SubSRAM_Amount{1'b1}});
end 

// Instantiate the sub SRAMs
genvar sub_sram_index;
generate
    for (sub_sram_index = 0; sub_sram_index < SubSRAM_Amount; sub_sram_index++) begin : sub_sram_gen
        subsram #(
            .DataWidth(DataWidth),
            .SRAM_DEPTH(SRAM_DEPTH),
            .SubSRAMIndex(sub_sram_index),
            .MLEN(MLEN),
            .PARALLEL_DIM(Parallel_Rd_Dim)
        ) sub_sram_1 (
            .clk(clk),
            .req(req),
            .write_en(write_en),
            .transposed_read(transposed_read),
            .addr(sram_addr),   
            .wdata(sub_sram_wdata[sub_sram_index]),
            .write_response(individual_subs_sram_write_response[sub_sram_index]),
            .read_data_valid(individual_subs_sram_read_valid[sub_sram_index]),
            .rdata(sub_sram_rdata[sub_sram_index])
        );
    end
endgenerate

// Write Data Transformation
wdata_transform #(
    .DataWidth(DataWidth),
    .SRAM_DEPTH(SRAM_DEPTH),
    .MLEN(MLEN),
    .Parallel_Rd_Dim(Parallel_Rd_Dim)
) wdata_transform_init (
    .clk(clk),
    .in_data(write_data),
    .addr(sram_addr),
    .sub_sram_wdata(sub_sram_wdata)
);

// Read Data Transformation
rdata_transform #(
    .DataWidth(DataWidth),
    .SRAM_DEPTH(SRAM_DEPTH),
    .MLEN(MLEN),
    .Parallel_Rd_Dim(Parallel_Rd_Dim)
) rdata_transform_1_init (
    .in_data(sub_sram_rdata),
    .sram_addr(sram_addr),
    .read_data_valid(read_data_valid),
    .out_data(out_data)
);



endmodule