`timescale 1ns/1ps


module rdata_transform #(
    parameter int DataWidth = 4, 
    parameter int SRAM_Depth = 128,
    parameter int MLEN = 8,                                             // The TileSize of the matrix.
    parameter int Parallel_Wr_Dim = 2,                                  // The number of row/col write in parallel
    parameter int Parallel_Rd_Dim = 2,                                  // The number of row/col read in parallel
    localparam int Parallel_Rd_Index_Width    = $clog2(MLEN/Parallel_Rd_Dim), 
    localparam int AdrWidth                   = $clog2(SRAM_Depth),     // Address Space for the SRAM
    localparam int SubSRAM_Amount             = MLEN / Parallel_Rd_Dim                        // The dimension of the sub SRAM, or the TileSize of the matrix.
    
) (
    input  logic                        clk,
    input  logic [ElementWidth-1:0]     in_data     [SubSRAM_Amount],
    input  logic [AdrWidth-1:0]         sram_addr,
    input  logic                        read_data_valid,
    output logic [DataWidth-1:0]        out_data    [Parallel_Rd_Dim * MLEN-1:0]
);

// -----
// Params
// -----
localparam int ElementWidth                 = DataWidth * (Parallel_Rd_Dim ** 2); // The width of each element in the sub SRAM
localparam int ElementRowWidth              = DataWidth * Parallel_Rd_Dim; // The width of each row in the sub SRAM
localparam int Parallel_Wr_Element_Amount   = Parallel_Wr_Dim / Parallel_Rd_Dim ; // The number of element written to a single sub SRAM in one cycle
localparam int Parallel_Wr_Amount           = MLEN / Parallel_Wr_Dim; // The number of row/col read in parallel

localparam int SubSRAMWrWidth               = DataWidth * (Parallel_Wr_Dim * Parallel_Rd_Dim);
localparam int SubSRAM_Index_Width          = $clog2(SubSRAM_Amount); // The width of the parallel read index
localparam int SubTile_Index_Width          = $clog2(SubSRAM_Amount * Parallel_Wr_Element_Amount); // The width of the parallel read index


logic [Parallel_Rd_Index_Width - 1 : 0] parallel_rd_index;

assign parallel_rd_index = sram_addr[Parallel_Rd_Index_Width-1:0];

initial begin

end

always @(posedge clk) begin
    for (int i = 0; i < Parallel_Rd_Dim; i++) begin
        for (int j = 0; j < SubSRAM_Amount; j++) begin
            out_data[((i * MLEN + j * Parallel_Rd_Dim) )] <= 
            in_data[(parallel_rd_index + j) % SubSRAM_Amount]
            [(i * DataWidth) +: DataWidth];  // Convert to explicit range
            // out_data[((i * MLEN + j + 1) * DataWidth - 1) : ((i * MLEN + j ) * DataWidth)] = in_data[(parallel_rd_index + j) % SubSRAM_Amount][i * DataWidth +: DataWidth];
        end
    end
end


endmodule