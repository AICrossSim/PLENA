`timescale 1ns/1ps


module wdata_transform #(
    parameter int DataWidth = 4, 
    parameter int SRAM_Depth = 128,
    parameter int MLEN = 8,                                             // The TileSize of the matrix.
    parameter int Parallel_Wr_Dim = 2,                                  // The number of row/col write in parallel
    parameter int Parallel_Rd_Dim = 2,                                  // The number of row/col read in parallel
    localparam int AdrWidth                   = $clog2(SRAM_Depth)      // Address Space for the SRAM
    
) (
    input  logic clk,
    input  logic [Parallel_Rd_Dim * MLEN * DataWidth - 1:0] in_data,     // Packed input vector
    input  logic [AdrWidth-1:0] addr,
    output logic [ElementWidth * Parallel_Wr_Element_Amount - 1 : 0]   sub_sram_wdata [SubSRAM_Amount]
);

// -----
// Params
// -----
localparam int ElementWidth                 = DataWidth * (Parallel_Rd_Dim ** 2); // The width of each element in the sub SRAM
localparam int ElementRowWidth              = DataWidth * Parallel_Rd_Dim; // The width of each row in the sub SRAM
localparam int Parallel_Wr_Element_Amount   = Parallel_Wr_Dim / Parallel_Rd_Dim ; // The number of element written to a single sub SRAM in one cycle
localparam int Parallel_Wr_Amount           = MLEN / Parallel_Wr_Dim; // The number of row/col read in parallel
localparam int Parallel_Rd_Index_Width      = $clog2(MLEN/Parallel_Rd_Dim);

localparam int SubSRAMWrWidth               = DataWidth * (Parallel_Wr_Dim * Parallel_Rd_Dim);
localparam int SubSRAM_Amount               = MLEN / Parallel_Rd_Dim;                        // The dimension of the sub SRAM, or the TileSize of the matrix.
localparam int SubSRAM_Index_Width          = $clog2(SubSRAM_Amount); // The width of the parallel read index
localparam int SubTile_Index_Width          = $clog2(SubSRAM_Amount * Parallel_Wr_Element_Amount); // The width of the parallel read index

initial begin
    assert (Parallel_Wr_Dim >= Parallel_Rd_Dim)
    else $fatal("Parallel_Wr_Dim %d must be larger than Parallel_Rd_Dim %d", Parallel_Wr_Dim, SubSRAM_Amount);

    assert (Parallel_Wr_Dim % Parallel_Rd_Dim == 0)
    else $fatal("Parallel_Wr_Dim %d must be divisible by Parallel_Rd_Dim %d", Parallel_Wr_Dim, Parallel_Rd_Dim);
end

// -----
// Wires
// -----

// Write Data Preparation
logic [SubTile_Index_Width-1:0] subtile_row_offset, subtile_col_index, subtile_index;
logic [SubSRAM_Index_Width-1:0] start_subsram_index, subsram_index;
assign start_subsram_index = addr[SubSRAM_Index_Width-1:0];
logic [$clog2(SubSRAM_Amount) - 1: 0] row_index_in_tile;

always @(posedge clk) begin
    for (subtile_index = 0; subtile_index < SubSRAM_Amount * Parallel_Wr_Element_Amount; subtile_index++) begin
        
        subtile_row_offset  = (subtile_index / SubSRAM_Amount) * Parallel_Rd_Dim;
        subtile_col_index   = subtile_index % SubSRAM_Amount;

        subsram_index = (subtile_index[SubSRAM_Index_Width-1:0]  + start_subsram_index);

        for (row_index_in_tile = 0; row_index_in_tile < Parallel_Rd_Dim; row_index_in_tile++) begin
            sub_sram_wdata[subsram_index][ row_index_in_tile * ElementRowWidth +: ElementRowWidth] 
            = in_data[  (subtile_row_offset  + row_index_in_tile) * MLEN * DataWidth + subtile_col_index * ElementRowWidth +: ElementRowWidth];
        end
    end
end





endmodule