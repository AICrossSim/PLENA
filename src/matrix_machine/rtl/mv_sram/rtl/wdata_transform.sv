`timescale 1ns/1ps


module wdata_transform #(
    parameter int DataWidth = 4, 
    parameter int SRAM_Depth = 128,
    parameter int MLEN = 8,                                             // The TileSize of the matrix.
    parameter int Parallel_Rd_Dim = 2,                                  // The number of row/col read in parallel
    localparam int AdrWidth                   = $clog2(SRAM_Depth)      // Address Space for the SRAM
    
) (
    input  logic clk,
    input  logic [Parallel_Rd_Dim * MLEN * DataWidth - 1:0] in_data,     // Packed input vector
    input  logic [AdrWidth-1:0] addr,
    output logic [SubSRAM_Amount -1 : 0] [ElementWidth - 1 : 0]   sub_sram_wdata 
);

// -----
// Params
// -----
localparam int ElementWidth                 = DataWidth * (Parallel_Rd_Dim ** 2); // The width of each element in the sub SRAM
localparam int ElementRowWidth              = DataWidth * Parallel_Rd_Dim; // The width of each row in the sub SRAM
localparam int Parallel_Rd_Index_Width      = $clog2(MLEN/Parallel_Rd_Dim);

localparam int SubSRAM_Amount               = MLEN / Parallel_Rd_Dim;                        // The dimension of the sub SRAM, or the TileSize of the matrix.
localparam int SubSRAM_Index_Width          = $clog2(SubSRAM_Amount); // The width of the parallel read index



// -----
// Wires
// -----

// Write Data Preparation
logic [SubSRAM_Index_Width-1:0] subtile_col_index;

logic [SubSRAM_Index_Width-1:0] start_subsram_index, subsram_index;
integer subtile_index;
logic [$clog2(SubSRAM_Amount) - 1: 0] row_index_in_tile;

assign start_subsram_index = addr[SubSRAM_Index_Width-1:0];

always @(*) begin
    for (subtile_index = 0; subtile_index < SubSRAM_Amount * Parallel_Rd_Dim; subtile_index++) begin
        
        subtile_col_index   = subtile_index % SubSRAM_Amount;
        subsram_index = (subtile_index[SubSRAM_Index_Width-1:0]  + start_subsram_index);


        for (row_index_in_tile = 0; row_index_in_tile < Parallel_Rd_Dim; row_index_in_tile++) begin
            sub_sram_wdata[subsram_index][ row_index_in_tile * ElementRowWidth +: ElementRowWidth] 
            = in_data[  row_index_in_tile * MLEN * DataWidth + subtile_col_index * ElementRowWidth +: ElementRowWidth];
        end
    end
end





endmodule