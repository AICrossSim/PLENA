`timescale 1ns/1ps

/*
Module      : Wrapper for tthe prim_generic_ram_1p
Timing      : Sequential Logic, 1 cycle for read/write process.
Description :
            : This module supports single read/write port
            : The addressing mode is Little Endian.
*/


module scalar_sram #(
    parameter DATA_WIDTH = 32,
    parameter DEPTH      = 32,         // Address Space for the SRAM
    parameter DataBitsPerMask = 1,
    parameter string MemInitFile = "",
    localparam int Aw              = $clog2(Depth)
)(
    input   logic clk,
    input   logic rst,

    input   logic req,
    input   logic write_en,
    input   logic [Aw-1:0] sram_addr,
    input   logic [DATA_WIDTH - 1 : 0] sram_data_in,
    output  logic [DATA_WIDTH - 1 : 0] sram_data_out
);


prim_generic_ram_1p #(
    .Width(DATA_WIDTH),
    .Depth(DEPTH),
    .DataBitsPerMask(DataBitsPerMask),
    .MemInitFile(MemInitFile)
) sram (
    .clk_i(clk),
    .rst_ni(!rst),
    .req_i(req),
    .write_i(write_en),
    .addr_i(sram_addr),
    .wdata_i(sram_data_in),
    .wmask_i({DATA_WIDTH{1'b1}}), // Only one bit is used for write mask
    .rdata_o(sram_data_out)
);



endmodule