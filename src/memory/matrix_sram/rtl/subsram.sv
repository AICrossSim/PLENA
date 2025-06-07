`timescale 1ns/1ps

/*
Module      : Sub SRAM units within the Matrix Machine SRAM
Timing      : Sequential Logic, 1 cycle for read/write process.
Description : 
Status      : Passed Simple Tests
*/

module subsram #(

  parameter  int DataWidth                  = 4, 
  parameter  int SRAM_DEPTH                 = 128,
  parameter  int SubSRAMIndex               = 0,                                // Index of the sub SRAM    
  parameter  int MLEN                       = 8,                                // The dimension of the sub SRAM, or the TileSize of the matrix.
  parameter  int PARALLEL_DIM               = 2,                                // The number of row/col read in parallel
  localparam int AdrWidth                   = $clog2(SRAM_DEPTH),               // derived parameter
  localparam int Parallel_Rd_Index_Width    = $clog2(MLEN/PARALLEL_DIM),        // The width of the parallel read index
  localparam int ElementWidth               = DataWidth * (PARALLEL_DIM ** 2),  // The width of each element in the sub SRAM
  localparam int Element_Amount             = PARALLEL_DIM ** 2                 // The number of data in a single element
) (
    input  logic                                  clk,

    // Read Port
    input  logic                                  req,
    input  logic [AdrWidth-1:0]                   raddr,
    input  logic                                  transposed_read,
    output logic [ElementWidth-1:0]               rdata,               // Read data. Data is returned one cycle after req_i is high.
    output logic                                  read_data_valid,
  
    // Write Port
    input  logic                                  wen,
    input  logic [AdrWidth-1:0]                   waddr,
    input  logic [ElementWidth -1:0]              wdata,              // To be confirmed
    output logic                                  write_response
);

// -----
// Wires
// -----
logic [ElementWidth-1:0]            mem [SRAM_DEPTH];
logic [AdrWidth-1:0]                translated_raddr;
logic [ElementWidth-1:0]            raw_rdata;
logic transpose_rawdata;

logic signed [Parallel_Rd_Index_Width-1:0]    sram_index, addr_offset;

initial begin
    sram_index = SubSRAMIndex[Parallel_Rd_Index_Width-1:0];
end

// Read Address Translation
always @(*) begin

    addr_offset = sram_index - raddr[Parallel_Rd_Index_Width-1:0];

    if (transposed_read) begin
        translated_raddr = { raddr[AdrWidth - 1 : Parallel_Rd_Index_Width], addr_offset};
    end
    else begin
        translated_raddr = raddr;
    end
end
// Write
always @(posedge clk) begin
    if (wen) begin
        mem[waddr]      <= wdata;
        write_response  <= 1'b1;
        read_data_valid <= 1'b0;
    end else begin
        write_response  <= 1'b0;
        read_data_valid <= 1'b0;
    end
end

// Transposed Read
always @(posedge clk) begin
    if (req) begin
        raw_rdata <= mem[translated_raddr];
        transpose_rawdata <= transposed_read;
        read_data_valid <= 1'b1;
    end
    else begin
        read_data_valid <= 1'b0;
    end
end

subtile_transpose #(
    .Dim(PARALLEL_DIM),
    .DataWidth(DataWidth)
) smst (
    .in_data(raw_rdata),
    .transposed_read(transpose_rawdata),
    .out_data(rdata)
);

endmodule


