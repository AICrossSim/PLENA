// This is the module that is responsible for mapping the sram address to the sub_sram_addr_array
// Note: Here we assume that the sram_addr refers to the start of the tile matrix we want to read.
`timescale 1ns/1ps
module ram_access_mapping # (
    parameter integer DataWidth = 4,
    parameter integer MLEN = 16,
    parameter integer ParallelRdDim = 4,
    parameter integer AddrLen = 6,
    parameter integer SubSRAMDim = MLEN / ParallelRdDim // The number of sub SRAMs / Continuous Rd Amount for a Tiled Matrix
)(
    input logic clk,
    input logic rst,
    input logic [AddrLen-1:0] sram_addr,
    input logic stall,                      // Indicates whether the read is stalled
    input logic transpose_read,
    input logic read_en,
    output logic [AddrLen-1:0] sub_sram_addr_array [SubSRAMDim],
    output logic addr_array_ready,
    output logic end_of_tile_read
);

// -----
// Params
// -----
localparam integer  CRAWidth = $clog2(SubSRAMDim);      // Continuous Rd Amount Width

// -----
// Wires
// -----
integer i;
logic [CRAWidth - 1 : 0] current_rd_amount, index_in_array;
logic [AddrLen-1:0] next_sub_sram_addr_array [SubSRAMDim];

initial begin
    $dumpfile("dump.vcd");  // Save waveform to dump.vcd
    $dumpvars(0, ram_access_mapping); // Dump all signals in my_design


    for (i = 0; i < SubSRAMDim; i++) begin
        next_sub_sram_addr_array[i] = 'x;
    end
    current_rd_amount = CRAWidth'('b0);
    addr_array_ready = 1'b0;
end

always_ff @(posedge clk or negedge rst) begin
    if (!rst) begin
        for (i = 0; i < SubSRAMDim; i++) begin
            next_sub_sram_addr_array[i] <= 'x;
        end
        current_rd_amount <= CRAWidth'('b0);
        addr_array_ready <= 1'b0;
    end
    else begin
        if (read_en & !stall & !end_of_tile_read) begin
            current_rd_amount <= current_rd_amount + CRAWidth'('b1);
            if (transpose_read) begin
                for (i = 0; i < SubSRAMDim; i++) begin
                    next_sub_sram_addr_array[index_in_array] <= sram_addr + {(AddrLen-CRAWidth)'('b0), current_rd_amount} + i[AddrLen-1:0];
                end
            end
            else begin
                for (i = 0; i < SubSRAMDim; i++) begin
                    next_sub_sram_addr_array[i] <= sram_addr + {(AddrLen-CRAWidth)'('b0), current_rd_amount} ;
                end
            end
            addr_array_ready <= 1'b1;
        end
        else begin
            addr_array_ready <= 1'b0;
        end
    end
end

assign end_of_tile_read = (current_rd_amount == SubSRAMDim[CRAWidth - 1 : 0] - 1);
assign sub_sram_addr_array = next_sub_sram_addr_array;
assign index_in_array = (transpose_read == 1'b1) ? ((current_rd_amount + i[CRAWidth - 1 : 0])) : {CRAWidth{1'b0}};
    
endmodule