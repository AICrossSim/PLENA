`timescale 1ns/1ps

/*
Module      : Top Level SRAM design solely for Matrix Machine 
Timing      : Sequential Logic, x cycle for read/write process.
Description :
            : This module supports parallel row / column read and write.
            : The addressing mode is Little Endian.
            ： The units for the address is Byte
Status      : Passed Simple Row/Col Read/Write Tests
*/


module matrix_sram_with_rounding #(
    // MX-FP Data Format
    parameter MXFP_EXP_WIDTH    = 4,
    parameter MXFP_MANT_WIDTH   = 3,
    parameter MXFP_SCALE_WIDTH  = 8,

    parameter FIXED_DATA_WIDTH  = 32,

    // Dimension
    parameter   MLEN              = 8,                                  // The dimension of the sub SRAM, or the TileSize of the matrix.
    parameter   BLOCK_DIM         = 4,                                
    localparam  BLOCK_NUM         = MLEN / BLOCK_DIM,

    // SRAM
    parameter   SRAM_DEPTH        = 128,
    localparam  AddrLen           = $clog2(SRAM_DEPTH),                 // Address Space for the SRAM
    parameter   PARALLEL_DIM = 2                                        // The depth of the SRAM

) (
    input   logic clk,

    input   logic rst,
    input   logic req,
    input   logic transposed_read,
    input   logic write_en,
    output  logic write_response,

    input   logic [FIXED_DATA_WIDTH-1:0] sram_addr,   
    input   logic [PARALLEL_DIM - 1 : 0][MLEN - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]  element_in,
    input   logic [PARALLEL_DIM - 1 : 0][BLOCK_NUM - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0]         scale_in, 
    output  logic [PARALLEL_DIM - 1 : 0][MLEN - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]  element_out,
    output  logic [PARALLEL_DIM - 1 : 0][BLOCK_NUM - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0]         scale_out

);


// Address Translation
localparam BITWIDTH_PER_ROW =  (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) * MLEN * PARALLEL_DIM / 8;
logic [AddrLen - 1 : 0] addr_for_sub_sram;
assign addr_for_sub_sram = sram_addr >> $clog2(BITWIDTH_PER_ROW);


// scale duplication
logic [PARALLEL_DIM - 1 : 0][MLEN - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0] dumplicated_scale_in;
logic [PARALLEL_DIM - 1 : 0][MLEN - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0] loaded_scale_out;
logic [PARALLEL_DIM - 1 : 0][MLEN - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] loaded_element_out;
logic scale_write_response, element_write_response;

assign write_response = scale_write_response & element_write_response;

duplicate_data_section #(
    .DATA_SEC_WIDTH     (MXFP_SCALE_WIDTH),
    .REPEAT             (BLOCK_DIM),
    .BITSTREAM_WIDTH    (MXFP_SCALE_WIDTH * BLOCK_NUM * PARALLEL_DIM)
) dumplicate_scale(
    .in_data        (scale_in),
    .out_data       (dumplicated_scale_in)
);

// scale storage
biaccess_sram #(
    .DataWidth      (MXFP_SCALE_WIDTH),
    .SRAM_DEPTH     (SRAM_DEPTH),
    .MLEN           (MLEN),
    .Parallel_Rd_Dim(PARALLEL_DIM)
) scale_storage (
    .clk(clk),
    .req(req),
    .transposed_read    (transposed_read),
    .write_en           (write_en),
    .write_response     (scale_write_response),
    .sram_addr          (addr_for_sub_sram),
    .write_data         (dumplicated_scale_in),
    .out_data           (loaded_scale_out)
);

// element storage
biaccess_sram #(
    .DataWidth      (MXFP_SCALE_WIDTH),
    .SRAM_DEPTH     (SRAM_DEPTH),
    .MLEN           (MLEN),
    .Parallel_Rd_Dim(PARALLEL_DIM)
) element_storage (
    .clk(clk),
    .req(req),
    .transposed_read    (transposed_read),
    .write_en           (write_en),
    .write_response     (element_write_response),
    .sram_addr          (addr_for_sub_sram),
    .write_data         (element_in),
    .out_data           (loaded_element_out)
);

// Output Rescale
generate
    for (genvar i = 0; i < PARALLEL_DIM; i++) begin : output_rescale
        for (genvar j = 0; j < BLOCK_NUM; j++) begin : output_rescale_block
            mx_fp_rescale #(
                .IN_MXFP_EXP_WIDTH      (MXFP_EXP_WIDTH),
                .IN_MXFP_MANT_WIDTH     (MXFP_MANT_WIDTH),
                .MXFP_SCALE_WIDTH       (MXFP_SCALE_WIDTH),
                .BLOCK_DIM              (BLOCK_DIM),
                .OUT_MXFP_EXP_WIDTH     (MXFP_EXP_WIDTH),
                .OUT_MXFP_MANT_WIDTH    (MXFP_MANT_WIDTH)
            ) rescale_output(
                .clk(clk),
                .rst(rst),
                .element_in         (loaded_element_out[i][j * BLOCK_DIM +: BLOCK_DIM]),
                .scale_in           (loaded_scale_out[i][j * BLOCK_DIM +: BLOCK_DIM]),
                .element_data_out   (element_out[i][j * BLOCK_DIM +: BLOCK_DIM]),
                .scale_data_out     (scale_out[i][j])
            );
        end

    end

endgenerate


endmodule