`timescale 1ns/1ps


module rdata_transform #(
    parameter int DataWidth = 4, 
    parameter int SRAM_Depth = 128,
    parameter int MLEN = 8,                                             // The TileSize of the matrix.
    parameter int Parallel_Rd_Dim = 2,                                  // The number of row/col read in parallel
    localparam int Parallel_Rd_Index_Width    = $clog2(MLEN/Parallel_Rd_Dim), 
    localparam int AdrWidth                   = $clog2(SRAM_Depth),     // Address Space for the SRAM
    localparam int SubSRAM_Amount             = MLEN / Parallel_Rd_Dim,                        // The dimension of the sub SRAM, or the TileSize of the matrix.
    localparam int ElementWidth                 = DataWidth * (Parallel_Rd_Dim ** 2)
) (
    input  logic                        clk,
    input  logic [SubSRAM_Amount -1 : 0] [ElementWidth-1:0]     in_data    ,
    input  logic [AdrWidth-1:0]         sram_addr,
    input  logic                        read_data_valid,
    output logic [Parallel_Rd_Dim * MLEN-1:0] [DataWidth-1:0]        out_data    
);

// -----
// Params
// -----
 // The width of each element in the sub SRAM
localparam int ElementRowWidth              = DataWidth * Parallel_Rd_Dim; // The width of each row in the sub SRAM

logic [Parallel_Rd_Index_Width - 1 : 0] parallel_rd_index;

assign parallel_rd_index = sram_addr[Parallel_Rd_Index_Width-1:0];

// initial begin

// end

always @(*) begin
    if (read_data_valid) begin
        for (int i = 0; i < Parallel_Rd_Dim; i++) begin
            // Row
            for (int j = 0; j < MLEN; j++) begin
                // Column
                out_data[((i * MLEN + j))] = 
                in_data[(parallel_rd_index + (j / Parallel_Rd_Dim) ) % SubSRAM_Amount]
                [(i * ElementRowWidth) + (j % Parallel_Rd_Dim) * DataWidth +: DataWidth];  // Convert to explicit range
                // out_data[((i * MLEN + j + 1) * DataWidth - 1) : ((i * MLEN + j ) * DataWidth)] = in_data[(parallel_rd_index + j) % SubSRAM_Amount][i * DataWidth +: DataWidth];
            end
        end
    end
end


endmodule