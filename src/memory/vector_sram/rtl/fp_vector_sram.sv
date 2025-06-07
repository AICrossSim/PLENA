`timescale 1ns/1ps

/*
Module      : Top Level SRAM design for scratchpad
Timing      : Sequential Logic, 1 cycle for read/write process.
Description :
            : This module supports two port reading
            : The addressing mode is Little Endian.
            : Port A ->  R: Matrix Multiplicand Vector or Vector Operand (RS1)               W: Vector Result from either Matrix or Vector Machine, 
            : Port B ->  R: Matrix Offest Vector or Vector Operand (RS2) or HBM Write Data   W: Vector Prefetch
Status      :
*/

module fp_vector_sram #(
    
    // MX-FP Data Format
    parameter MXFP_EXP_WIDTH    = 4,
    parameter MXFP_MANT_WIDTH   = 3,
    parameter MXFP_SCALE_WIDTH  = 8,
    // FP Data Format
    parameter   EXP_WIDTH         = 8,                                  
    parameter   MANT_WIDTH        = 7,

    // Dimension
    parameter   VLEN              = 8,                                  // The dimension of the sub SRAM, or the TileSize of the matrix.
    parameter   BLOCK_DIM         = 4,                                
    localparam  BLOCK_NUM         = VLEN / BLOCK_DIM,

    // SRAM
    parameter   SRAM_DEPTH        = 128,
    localparam  AddrLen           = $clog2(SRAM_DEPTH)                // Address Space for the SRAM

)(
    input   logic clk,
    input   logic rst,

    // Port A
    input   logic port_a_req,
    input   logic port_a_write_en,
    input   logic [AddrLen-1:0] port_a_addr,
    // FP Data Connection
    input   logic [VLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0]    port_a_fp_in,
    input   logic [VLEN - 1 : 0]                                        port_a_mask_in,
    output  logic [VLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0]    port_a_fp_out,

    // Port B
    input   logic port_b_req,
    input   logic port_b_write_en,
    input   logic [AddrLen-1:0] port_b_addr,
    // FP Data Connection
    output  logic [VLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0]                port_b_fp_out,
    input   logic [VLEN - 1 : 0]                                                    port_b_mask_in,
    // MX-FP Connection
    input   logic [VLEN - 1 : 0]        [MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]      element_in_b,
    input   logic [BLOCK_NUM - 1 : 0]   [MXFP_SCALE_WIDTH - 1 : 0]                  scale_in_b,

    output  logic [VLEN - 1 : 0]        [MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]      element_out_b,
    output  logic [BLOCK_NUM - 1 : 0]   [MXFP_SCALE_WIDTH - 1 : 0]                  scale_out_b

);




    // -----------------------------
    // Port B Management
    // -----------------------------
    // Convert MX-FP Data to FP Data
    logic [VLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0]    converted_b_fp_in;
    logic [VLEN - 1 : 0]        [EXP_WIDTH + MANT_WIDTH : 0]    converted_b_fp_out;
    generate;
        for (genvar i = 0; i < BLOCK_NUM; i++) begin : gen_mxfp_2_fp_convert
            mx_fp_2_fp_block #(
                .BLOCK_DIM(BLOCK_DIM),
                .MX_FP_MANT_WIDTH(MXFP_MANT_WIDTH),
                .MX_FP_EXP_WIDTH(MXFP_EXP_WIDTH),
                .FP_MANT_WIDTH(MANT_WIDTH),
                .FP_EXP_WIDTH(EXP_WIDTH)
            ) mx_fp_2_fp_convert (
                .element_in(element_in_b[(i+1)*BLOCK_DIM-1 : i*BLOCK_DIM]),
                .scale_in(scale_in_b[i]),
                .fp_out(converted_b_fp_in)
            );
        end
    endgenerate


    // Convert FP Data to MX-FP Data for HBM write
    logic [BLOCK_NUM - 1 : 0] mxfp_fp_convert_in_valid;
    logic [BLOCK_NUM - 1 : 0] mxfp_fp_convert_out_ready;
    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            mxfp_fp_convert_in_valid <= '0;
        end else begin
            mxfp_fp_convert_in_valid <= port_b_req ? {BLOCK_NUM{1'b1}} : '0;
            mxfp_fp_convert_out_ready <= {BLOCK_NUM{1'b1}};
        end
    end

    for (genvar j = 0; j < BLOCK_NUM; j++) begin
        fp_2_mx_fp_block #(
            .BLOCK_DIM(BLOCK_DIM),
            .FP_MANT_WIDTH(ACC_MANT_WIDTH),
            .FP_EXP_WIDTH(ACC_EXP_WIDTH),
            .MX_FP_MANT_WIDTH(MXFP_MANT_WIDTH),
            .MX_FP_EXP_WIDTH(MXFP_EXP_WIDTH),
            .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH)
        ) fp_2_mx_convert_init(
            .clk(clk),
            .rst(rst),
            .data_in(fp_dot_out[(j+1)*BLOCK_DIM-1 : j*BLOCK_DIM]),
            .data_in_valid(mxfp_fp_convert_in_valid[j]),
            .data_in_ready(),
            .element_data_out(element_out_b[(j+1) * BLOCK_DIM-1 : j * BLOCK_DIM]),
            .scale_data_out(scale_out_b[j]),
            .mx_fp_data_out_valid(mxfp_fp_convert_out_valid[j]),
            .mx_fp_data_out_ready(mxfp_fp_convert_out_ready[j])
        );

    end

// ELement Storage Data
prim_generic_ram_2p #(
    .Width((EXP_WIDTH + MANT_WIDTH + 1) * VLEN),
    .Depth(SRAM_DEPTH),
    .DataBitsPerMask((EXP_WIDTH + MANT_WIDTH + 1)),
    .MemInitFile("")
) element_storage (
    .clk_a_i(clk),
    .clk_b_i(clk),

    .a_req_i        (port_a_req),
    .a_write_i      (port_a_write_en),
    .a_addr_i       (port_a_addr),
    .a_wdata_i      (port_a_fp_in),
    .a_wmask_i      (port_a_mask_in),
    .a_rdata_o      (element_out_a),

    .b_req_i        (port_b_req),
    .b_write_i      (port_b_write_en),
    .b_addr_i       (port_b_addr),
    .b_wdata_i      (converted_b_fp_in),
    .b_wmask_i      (mask_in_b),
    .b_rdata_o      (element_out_b),
    // Unused
    .cfg_i('0),
    .cfg_rsp_o()
);



endmodule