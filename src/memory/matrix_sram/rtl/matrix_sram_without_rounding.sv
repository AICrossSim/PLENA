`timescale 1ns/1ps

/*
Module      : Top Level SRAM design solely for Matrix Machine 
Timing      : Sequential Logic, x cycle for read/write process.
Description :
            : This module supports parallel row / column read and write.
            : For the scale, no matter transposed or not, it is always read in the same way as the 
Status      : Passed Simple Row/Col Read/Write Tests
*/


module matrix_sram_without_rounding #(
    // MX-FP Data Format
    parameter MXFP_EXP_WIDTH    = 4,
    parameter MXFP_MANT_WIDTH   = 3,
    parameter MXFP_SCALE_WIDTH  = 8,
    parameter FIXED_DATA_WIDTH  = 32,

    // Dimension
    parameter   MLEN            = 8,
    parameter   BLOCK_DIM       = 4,                                
    localparam  BLOCK_NUM       = MLEN / BLOCK_DIM,

    // SRAM
    parameter   SRAM_DEPTH      = 128,
    localparam  AddrLen         = $clog2(SRAM_DEPTH),      
    parameter   PARALLEL_DIM    = 1,
    parameter   PREFETCH_AMOUNT = 4                       

) (
    input   logic clk,
    input   logic rst,

    // Read Operation
    input   logic req,
    input   logic transposed_read,
    input   logic [FIXED_DATA_WIDTH-1:0] sram_raddr,   
    output  logic [PARALLEL_DIM - 1 : 0][MLEN - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]    element_out,
    output  logic [PARALLEL_DIM - 1 : 0][MLEN - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0]                scale_out,

    // Write Operation
    input   logic wen,
    output  logic write_response,
    input   logic [FIXED_DATA_WIDTH-1:0] sram_waddr,
    input   logic [PARALLEL_DIM - 1 : 0][MLEN - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]  element_in,
    input   logic [PARALLEL_DIM - 1 : 0][BLOCK_NUM - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0]         scale_in,

    // Prefetch Status
    input   logic [AddrLen - 1 : 0] prefetch_addr,
    input   logic prefetch_en,
    output  logic data_not_ready
);

// -----------------------------
// Address Translation & Prefetch Tag Matching
// -----------------------------

logic [AddrLen - 1 : 0] waddr_for_sub_sram, raddr_for_sub_sram, prefetch_addr_for_sub_sram;
localparam BITWIDTH_PER_ROW =  (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) * MLEN * PARALLEL_DIM / 8;
assign waddr_for_sub_sram = sram_waddr >> $clog2(BITWIDTH_PER_ROW);
assign raddr_for_sub_sram = sram_raddr >> $clog2(BITWIDTH_PER_ROW);
assign prefetch_addr_for_sub_sram = prefetch_addr >> $clog2(BITWIDTH_PER_ROW);

// Tag Matching, trackinng the prefetch status.
logic [SRAM_DEPTH - 1 : 0] mem_data_tag;

logic wen_delay;
logic [AddrLen - 1 : 0] waddr_for_sub_sram_delay;
always_ff @(posedge clk) begin
    if (rst) begin
        wen_delay <= 1'b0;
        waddr_for_sub_sram_delay <= '0;
    end else begin
        wen_delay <= wen;
        waddr_for_sub_sram_delay <= waddr_for_sub_sram;
    end
end

always_ff @(posedge clk) begin
    if (rst) begin
        mem_data_tag <= {{SRAM_DEPTH{1'b1}}};
    end else if (prefetch_en) begin
        for (int i = prefetch_addr_for_sub_sram; i < prefetch_addr_for_sub_sram + PREFETCH_AMOUNT; i++) begin
            mem_data_tag[i] <= 1'b0;
        end
    end else if (wen_delay) begin
        mem_data_tag[waddr_for_sub_sram_delay] <= 1'b1;
    end
end

always_ff @(posedge clk) begin
    if (rst) begin
        data_not_ready <= 1'b0;
    end else begin
        data_not_ready <= (req) & (mem_data_tag[raddr_for_sub_sram] == 1'b0);
    end
end

// scale duplication
logic scale_write_response, element_write_response;
logic [PARALLEL_DIM - 1 : 0][MLEN - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0] dumplicated_scale_in;
logic [PARALLEL_DIM - 1 : 0][MLEN - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0] loaded_scale_out;
logic [PARALLEL_DIM - 1 : 0][MLEN - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] loaded_element_out;

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
    .sram_raddr         (raddr_for_sub_sram),
    .out_data           (loaded_scale_out),
    .wen_req            (wen),
    .write_response     (scale_write_response),
    .sram_waddr         (waddr_for_sub_sram),
    .write_data         (dumplicated_scale_in)
);

// element storage
biaccess_sram #(
    .DataWidth      (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1),
    .SRAM_DEPTH     (SRAM_DEPTH),
    .MLEN           (MLEN),
    .Parallel_Rd_Dim(PARALLEL_DIM)
) element_storage (
    .clk(clk),
    .req(req),
    .transposed_read    (transposed_read),
    .sram_raddr         (raddr_for_sub_sram),
    .out_data           (loaded_element_out),
    .wen_req            (wen),
    .write_response     (element_write_response),
    .sram_waddr         (waddr_for_sub_sram),
    .write_data         (element_in)
);

// -----------------------------
assign element_out = loaded_element_out;
assign scale_out = loaded_scale_out;


endmodule