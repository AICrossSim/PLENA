`timescale 1ns/1ps

module subsram #(

  parameter  int DataWidth                  = 4, 
  parameter  int Depth                      = 128,
  parameter  int SubSRAMIndex               = 0,                        // Index of the sub SRAM    
  parameter  int SubSRAM_Amount             = 8,                        // The dimension of the sub SRAM, or the TileSize of the matrix.
  parameter  int Parallel_Rd_Amount         = 2,                        // The number of row/col read in parallel
  localparam int AdrWidth                   = $clog2(Depth),             // derived parameter
  localparam int Parallel_Rd_Index_Width    = $clog2(SubSRAM_Amount/Parallel_Rd_Amount), // The width of the parallel read index
  localparam int ElementWidth               = DataWidth * (Parallel_Rd_Amount ** 2),   // The width of each element in the sub SRAM
  localparam int Element_Amount             = Parallel_Rd_Amount ** 2 // The number of data in a single element

) (
  input  logic                                  clk,

  input  logic                                  req,
  input  logic                                  write_en,
  input  logic                                  transposed_read,
  
  input  logic [AdrWidth-1:0]                   addr,
  input  logic [Parallel_Rd_Index_Width-1:0]    parallel_rd_index,
  input  logic [ElementWidth-1:0]               wdata, // To be confirmed
  output logic [DataWidth-1:0]                  rdata [Element_Amount] // Read data. Data is returned one cycle after req_i is high.
);

// -----
// Wires
// -----
logic [ElementWidth-1:0]            mem [Depth];
logic [AdrWidth-1:0]                addr_for_sub_sram;
logic [ElementWidth-1:0]            raw_rdata;
logic transpose_rawdata;

initial begin
    $dumpfile("dump.vcd");  // Save waveform to dump.vcd
    $dumpvars(0, subsram); // Dump all signals in my_design
    for (int j = 0; j < Element_Amount; j++) begin
        $dumpvars(0, rdata[j]);
    end
    for (int i = 0; i < Element_Amount; i++) begin
        $dumpvars(0, mem[i]);
    end
end


// Address Translation
always_comb begin
    if (transposed_read) begin
        addr_for_sub_sram = { (AdrWidth - Parallel_Rd_Index_Width)'('b0), SubSRAMIndex[Parallel_Rd_Index_Width-1:0] - parallel_rd_index} + addr;
    end
    else begin
        addr_for_sub_sram = { (AdrWidth - Parallel_Rd_Index_Width)'('b0), parallel_rd_index} + addr;
    end
end

// Transposed Read

always @(posedge clk) begin
    if (req) begin
        if (write_en) begin
            // TO be confirmed
            mem[addr] <= wdata;
        end 
        else begin
            raw_rdata <= mem[addr_for_sub_sram];
            transpose_rawdata <= transposed_read;
        end
    end
end

sub_tile_transpose #(
    .Dim(Parallel_Rd_Amount),
    .DataWidth(DataWidth)
) smst (
    .in_data(raw_rdata),
    .transposed_read(transpose_rawdata),
    .out_data(rdata)
);

endmodule


