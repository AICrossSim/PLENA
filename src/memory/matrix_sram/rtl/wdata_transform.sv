`timescale 1ns/1ps


module wdata_transform #(
    parameter  DataWidth = 4, 
    parameter  SRAM_DEPTH = 128,
    parameter  MLEN = 8,                                             // The TileSize of the matrix.
    parameter  Parallel_Rd_Dim = 2,                                  // The number of row/col read in parallel
    localparam  AdrWidth                   = $clog2(SRAM_DEPTH),      // Address Space for the SRAM
    localparam  SubSRAM_Amount               = MLEN / Parallel_Rd_Dim, // The dimension of the sub SRAM, or the TileSize of the matrix.
    localparam  ElementWidth                 = DataWidth * (Parallel_Rd_Dim ** 2) // The width of each element in the sub SRAM
    
) (
    input  logic clk,
    input  logic wreq,
    input  logic [Parallel_Rd_Dim * MLEN * DataWidth - 1:0] in_data,     // Packed input vector
    input  logic [AdrWidth-1:0] addr,
    output logic [SubSRAM_Amount -1 : 0] [ElementWidth - 1 : 0]   sub_sram_wdata 
);

// -----
// Params
// -----

localparam  ElementRowWidth              = DataWidth * Parallel_Rd_Dim; // The width of each row in the sub SRAM
localparam  Parallel_Rd_Index_Width      = $clog2(MLEN/Parallel_Rd_Dim);
localparam  SubSRAM_Index_Width          = $clog2(SubSRAM_Amount); // The width of the parallel read index

// -----
// Wires
// -----
logic [SubSRAM_Index_Width-1:0] subtile_col_index;
logic [SubSRAM_Index_Width-1:0] start_subsram_index, subsram_index;
integer subtile_index;
integer row_index_in_tile;
logic [Parallel_Rd_Dim * MLEN * DataWidth - 1:0] stored_in_data;

assign start_subsram_index = addr[SubSRAM_Index_Width-1:0];

always_ff @(posedge clk) begin
    if (wreq)
        stored_in_data <= in_data;
    else
        stored_in_data <= '0;
end


always @(*) begin
    for (subtile_index = 0; subtile_index < SubSRAM_Amount * Parallel_Rd_Dim; subtile_index = subtile_index + 1) begin
        subtile_col_index   = subtile_index % SubSRAM_Amount;
        subsram_index = (subtile_index[SubSRAM_Index_Width-1:0]  + start_subsram_index);
        for (row_index_in_tile = 0; row_index_in_tile < Parallel_Rd_Dim; row_index_in_tile++) begin
            sub_sram_wdata[subsram_index][ row_index_in_tile * ElementRowWidth +: ElementRowWidth] 
            = stored_in_data[row_index_in_tile * MLEN * DataWidth + subtile_col_index * ElementRowWidth +: ElementRowWidth];
        end
    end
end





endmodule