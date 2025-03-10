`timescale 1ns/1ps

module subsram #(

  parameter  int DataWidth                  = 4, 
  parameter  int SRAM_Depth                 = 128,
  parameter  int SubSRAMIndex               = 0,                                // Index of the sub SRAM    
  parameter  int MLEN                       = 8,                                // The dimension of the sub SRAM, or the TileSize of the matrix.
  parameter  int Parallel_Wr_Amount         = 2,                                // The number of row/col write in parallel
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
  input  logic [ElementWidth-1:0]               wdata, // To be confirmed
  output logic [ElementWidth-1:0]               rdata  // Read data. Data is returned one cycle after req_i is high.
);

// -----
// Wires
// -----
logic [ElementWidth-1:0]            mem [SRAM_Depth];
logic [AdrWidth-1:0]                addr_for_sub_sram;
logic [ElementWidth-1:0]            raw_rdata;
logic transpose_rawdata;
logic [Parallel_Rd_Index_Width-1:0]    parallel_rd_index;

initial begin
    $dumpfile("dump.vcd");  // Save waveform to dump.vcd
    $dumpvars(0, subsram); // Dump all signals in my_design
    for (int j = 0; j < Element_Amount; j++) begin
        $dumpvars(0, rdata[j]);
    end
end

assign parallel_rd_index = addr[Parallel_Rd_Index_Width-1:0];
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
            for (int i = 0; i < Parallel_Wr_Amount; i++) begin
                mem[addr + i]<= wdata[i*DataWidth - 1 +: DataWidth];
            end

        end 
        else begin
            raw_rdata <= mem[addr_for_sub_sram];
            transpose_rawdata <= transposed_read;
        end
    end
end


// Transpose the matrix
// genvar row, col;
// generate
//     for (row = 0; row < Parallel_Rd_Amount; row++) begin : transpose_rows
//         for (col = 0; col < Parallel_Rd_Amount; col++) begin : transpose_cols
//             assign rdata[col*Parallel_Rd_Amount + row] = transposed_read ?
//                 raw_rdata[((row * Parallel_Rd_Amount + col) + 1) * DataWidth - 1 : (row * Parallel_Rd_Amount + col) * DataWidth] :
//                 raw_rdata[((col * Parallel_Rd_Amount + row) + 1) * DataWidth - 1 : (col * Parallel_Rd_Amount + row) * DataWidth];
//         end
//     end
// endgenerate

subtile_transpose #(
    .Dim(Parallel_Rd_Amount),
    .DataWidth(DataWidth)
) smst (
    .in_data(raw_rdata),
    .transposed_read(transpose_rawdata),
    .out_data(rdata)
);


endmodule


