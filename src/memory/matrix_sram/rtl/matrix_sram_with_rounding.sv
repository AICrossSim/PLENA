/*
Module      : Top Level SRAM design solely for Matrix Machine 
Timing      : Sequential Logic, x cycle for read/write process.
Description :
            : This module supports parallel row / column read and write.
            : The addressing mode is Little Endian.
Status      : Passed Simple Row/Col Read/Write Tests
*/


`timescale 1ns/1ps

module matrix_sram_with_rounding #(
    // MX-FP Data Format
    parameter MXFP_EXP_WIDTH    = 4,
    parameter MXFP_MANT_WIDTH   = 3,
    parameter MXFP_SCALE_WIDTH  = 8,

    // Dimension
    parameter   MLEN              = 8,                                // The dimension of the sub SRAM, or the TileSize of the matrix.
    parameter   BLOCK_DIM         = 4,                                
    localparam  BLOCK_NUM         = MLEN / BLOCK_DIM,

    // SRAM
    parameter   SRAM_Depth        = 128,
    parameter   Parallel_Rd_Amount = 2                              // The depth of the SRAM

) (
    input   logic clk,

    input   logic rst,
    input   logic req,
    input   logic transposed_read,
    input   logic write_en,
    output  logic write_response,
    input   logic read_en,

    input   logic [AddrLen-1:0] sram_addr,   
    input   logic [Parallel_Rd_Amount - 1 : 0][MLEN - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] element_in,
    input   logic [Parallel_Rd_Amount - 1 : 0][BLOCK_NUM - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0] scale_in, 
    output  logic [Parallel_Rd_Amount - 1 : 0][MLEN - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] element_out,
    output  logic [Parallel_Rd_Amount - 1 : 0][BLOCK_NUM - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0] scale_out

);

// scale duplication
logic [Parallel_Rd_Amount - 1 : 0][MLEN - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0] dumplicated_scale_in;
logic [Parallel_Rd_Amount - 1 : 0][MLEN - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0] loaded_scale_out;
logic [Parallel_Rd_Amount - 1 : 0][MLEN - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] loaded_element_out;

duplicate_data_section #(
    .DATA_SEC_WIDTH(MXFP_SCALE_WIDTH),
    .REPEAT(BLOCK_DIM),
    .BITSTREAM_WIDTH(MXFP_SCALE_WIDTH * BLOCK_NUM * Parallel_Rd_Amount),
) dumplicate_scale(
    .in_data(scale_in),
    .out_data(dumplicated_scale_in)
);

// scale storage
biaccess_sram #(
    .DataWidth(MXFP_SCALE_WIDTH),
    .SRAM_Depth(SRAM_Depth),
    .MLEN(MLEN),
    .Parallel_Rd_Dim(Parallel_Rd_Amount)
) scale_storage (
    .clk(clk),
    .req(req),
    .transposed_read(transposed_read),
    .write_en(write_en),
    .write_response(write_response),
    .sram_addr(sram_addr),
    .read_en(read_en),
    .write_data(dumplicated_scale_in),
    .out_data(loaded_scale_out)
);

// element storage
biaccess_sram #(
    .DataWidth(MXFP_SCALE_WIDTH),
    .SRAM_Depth(SRAM_Depth),
    .MLEN(MLEN),
    .Parallel_Rd_Dim(Parallel_Rd_Amount)
) scale_storage (
    .clk(clk),
    .req(req),
    .transposed_read(transposed_read),
    .write_en(write_en),
    .write_response(write_response),
    .sram_addr(sram_addr),
    .read_en(read_en),
    .write_data(element_in),
    .out_data(loaded_element_out)
);

// Output Rescale
generate
    for (genvar i = 0; i < Parallel_Rd_Amount * BLOCK_NUM; i++) begin : output_rescale
        mx_fp_rescale #(
            .IN_MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
            .IN_MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
            .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
            .BLOCK_DIM(BLOCK_DIM),
            .OUT_MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
            .OUT_MXFP_MANT_WIDTH(MXFP_MANT_WIDTH)
        ) rescale_output(
            .clk(clk),
            .rst(rst),
            .element_in(loaded_element_out[i]),
            .scale_in(loaded_scale_out[i]),
            .element_data_out(element_out[i]),
            .scale_data_out(scale_out[i])
        )
    end

endgenerate


endmodule