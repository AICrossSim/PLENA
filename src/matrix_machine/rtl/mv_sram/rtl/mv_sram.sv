`timescale 1ns/1ps

module mv_sram #(
    parameter int DataWidth = 4, 
    parameter int SRAM_Depth = 128,
    parameter int MLEN = 8,                                             // The TileSize of the matrix.
    parameter int Parallel_Wr_Dim = 2,                                  // The number of row/col write in parallel
    parameter int Parallel_Rd_Dim = 2,                                  // The number of row/col read in parallel
    localparam int AddrLen                   = $clog2(SRAM_Depth)     // Address Space for the SRAM
    
) (
    input  logic clk,

    // input  logic rst,
    input  logic req,
    input  logic transposed_read,
    input  logic write_en,
    // input  logic last_write,
    output logic write_response,
    output logic read_data_valid,

    input  logic [AddrLen-1:0] sram_addr,
    input  logic stall,                                                     // Indicates whether the read is stalled
    input  logic read_en,
    input  logic [Parallel_Wr_Dim * MLEN * DataWidth - 1:0] write_data,     // Packed input vector
    output logic [DataWidth-1:0] out_data [Parallel_Rd_Dim * MLEN-1:0]      // Unpacked output array
);

// -----
// Params
// -----
localparam int ElementWidth                 = DataWidth * (Parallel_Rd_Dim ** 2);       // The width of each element in the sub SRAM
localparam int Parallel_Wr_Element_Amount   = Parallel_Wr_Dim / Parallel_Rd_Dim ;       // The number of element written to a single sub SRAM in one cycle
localparam int Parallel_Wr_Amount           = MLEN / Parallel_Wr_Dim;                   // The number of row/col read in parallel
localparam int SubSRAM_Amount               = MLEN / Parallel_Rd_Dim;                   // The dimension of the sub SRAM, or the TileSize of the matrix.


initial begin
    assert (Parallel_Wr_Dim >= Parallel_Rd_Dim)
    else $fatal("Parallel_Wr_Dim %d must be larger than Parallel_Rd_Dim %d", Parallel_Wr_Dim, SubSRAM_Amount);

    assert (Parallel_Wr_Dim % Parallel_Rd_Dim == 0)
    else $fatal("Parallel_Wr_Dim %d must be divisible by Parallel_Rd_Dim %d", Parallel_Wr_Dim, Parallel_Rd_Dim);
end


// -----
// Wires
// -----
logic [ElementWidth * Parallel_Wr_Element_Amount - 1 : 0]   sub_sram_wdata [SubSRAM_Amount];
logic [ElementWidth-1:0]                                    sub_sram_rdata [SubSRAM_Amount];

logic individual_subs_sram_write_response [SubSRAM_Amount];

// Control Signals
// assign write_response = & individual_subs_sram_write_response;
always_comb begin
    write_response = 1'b1;
    for (int i = 0; i < SubSRAM_Amount; i++) begin
        write_response &= individual_subs_sram_write_response[i];
    end
end 

// Instantiate the sub SRAMs
genvar sub_sram_index;
generate
    for (sub_sram_index = 0; sub_sram_index < SubSRAM_Amount; sub_sram_index++) begin : sub_sram
        subsram #(
            .DataWidth(DataWidth),
            .SRAM_Depth(SRAM_Depth),
            .SubSRAMIndex(sub_sram_index),
            .MLEN(MLEN),
            .Parallel_Wr_Amount(Parallel_Wr_Amount),
            .Parallel_Rd_Amount(Parallel_Rd_Dim)
        ) sub_sram_1 (
            .clk(clk),
            .req(req),
            .write_en(write_en),
            .transposed_read(transposed_read),
            .addr(sram_addr),   
            .wdata(sub_sram_wdata[sub_sram_index]),
            .write_response(individual_subs_sram_write_response[sub_sram_index]),
            .rdata(sub_sram_rdata[sub_sram_index])
        );
    end
endgenerate


// Write Data Transformation
wdata_transform #(
    .DataWidth(DataWidth),
    .SRAM_Depth(SRAM_Depth),
    .MLEN(MLEN),
    .Parallel_Wr_Dim(Parallel_Wr_Dim),
    .Parallel_Rd_Dim(Parallel_Rd_Dim)
) wdata_transform_1 (
    .clk(clk),
    .in_data(write_data),
    .addr(sram_addr),
    .sub_sram_wdata(sub_sram_wdata)
);

// Read Data Transformation
rdata_transform #(
    .DataWidth(DataWidth),
    .SRAM_Depth(SRAM_Depth),
    .MLEN(MLEN),
    .Parallel_Wr_Dim(Parallel_Wr_Dim),
    .Parallel_Rd_Dim(Parallel_Rd_Dim)
) rdata_transform_1 (
    .in_data(sub_sram_rdata),
    .sram_addr(sram_addr),
    .read_data_valid(read_data_valid),
    .out_data(out_data)
);



endmodule