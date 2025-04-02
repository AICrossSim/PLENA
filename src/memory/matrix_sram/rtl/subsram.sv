`timescale 1ns/1ps

/*
Module      : Sub SRAM units within the Matrix Machine SRAM
Timing      : Sequential Logic, 1 cycle for read/write process.
Description : 
Status      : Passed Simple Tests
*/

module subsram #(

  parameter  int DataWidth                  = 4, 
  parameter  int SRAM_Depth                 = 128,
  parameter  int SubSRAMIndex               = 0,                                // Index of the sub SRAM    
  parameter  int MLEN                       = 8,                                // The dimension of the sub SRAM, or the TileSize of the matrix.
  parameter  int Parallel_Rd_Amount         = 2,                                // The number of row/col read in parallel
  localparam int AdrWidth                   = $clog2(SRAM_Depth),               // derived parameter
  localparam int Parallel_Rd_Index_Width    = $clog2(MLEN/Parallel_Rd_Amount),  // The width of the parallel read index
  localparam int ElementWidth               = DataWidth * (Parallel_Rd_Amount ** 2),   // The width of each element in the sub SRAM
  localparam int Element_Amount             = Parallel_Rd_Amount ** 2           // The number of data in a single element
) (
  input  logic                                  clk,

  input  logic                                  req,
  input  logic                                  write_en,
  input  logic                                  transposed_read,
  
  input  logic [AdrWidth-1:0]                   addr,
  input  logic [ElementWidth -1:0]               wdata, // To be confirmed
  output logic                                  write_response,
  output logic                                  read_data_valid,
  output logic [ElementWidth-1:0]               rdata  // Read data. Data is returned one cycle after req_i is high.
);

// -----
// Wires
// -----
logic [ElementWidth-1:0]            mem [SRAM_Depth];
logic [AdrWidth-1:0]                addr_for_sub_sram;
logic [ElementWidth-1:0]            raw_rdata;
logic transpose_rawdata;

logic signed [Parallel_Rd_Index_Width-1:0]    sram_index, addr_offset;

initial begin
    // $dumpvars(0, subsram); // Dump all signals in my_design
    // $dumpfile("dump.vcd");  // Save waveform to dump.vcd
    sram_index = SubSRAMIndex[Parallel_Rd_Index_Width-1:0];
end

// Address Translation
always @(*) begin

    addr_offset = sram_index - addr[Parallel_Rd_Index_Width-1:0];

    if (transposed_read) begin
        addr_for_sub_sram = { addr[AdrWidth - 1 : Parallel_Rd_Index_Width], addr_offset};
    end
    else begin
        addr_for_sub_sram = addr;
    end
end

// Transposed Read
always @(posedge clk) begin
    if (req) begin
        if (write_en) begin
            mem[addr_for_sub_sram] <= wdata;
            write_response <= 1'b1;
            read_data_valid <= 1'b0;
        end 
        else begin
            write_response <= 1'b0;
            raw_rdata <= mem[addr_for_sub_sram];
            transpose_rawdata <= transposed_read;
            read_data_valid <= 1'b1;
        end
    end
    else begin
        write_response <= 1'b0;
        read_data_valid <= 1'b0;
    end
end

subtile_transpose #(
    .Dim(Parallel_Rd_Amount),
    .DataWidth(DataWidth)
) smst (
    .in_data(raw_rdata),
    .transposed_read(transpose_rawdata),
    .out_data(rdata)
);

endmodule


