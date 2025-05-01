`timescale 1ns / 1ps
`include "operation.svh"
// `include "tl_util.svh"

/*
Module      : HBM - DMA - Controller
Timing      : Combinatorial
Status      : Under Development (Need to consider TileLink)
*/

module hbm_controller #(
    parameter   MXFP_EXP_WIDTH      = 4,
    parameter   MXFP_MANT_WIDTH     = 3,
    parameter   MXFP_SCALE_WIDTH    = 8,
    parameter   BLOCK_DIM           = 4,
    parameter   ADDR_WIDTH          = 32,
    parameter   HBM_ADDR_WIDTH      = 64,
    parameter   ADR_OPERAND_WIDTH   = 5,
    parameter   HBM_ADDR_REG_NUM    = 4,
    parameter   MLEN                = 8,
    parameter   VLEN                = 8,
    parameter   Parallel_Rd_Dim     = 4 
    
)(
    input   logic clk,
    input   logic rst,

    input   H_OP    h_op, // HBM operation
    input   logic   set_addr_reg_en,
    input   logic   [ADDR_WIDTH - 1 : 0] addr_in_a,
    input   logic   [ADDR_WIDTH - 1 : 0] addr_in_b,
    input   logic   [ADR_OPERAND_WIDTH - 1 : 0] addr_reg_operand,

    output  logic   [VLEN - 1 : 0] [MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] prefetch_v_element,
    output  logic   [VLEN - 1 : 0] [MXFP_SCALE_WIDTH - 1 : 0] prefetch_v_scale,
    output  logic   dma_v_ready,
    input   logic   prefetch_v_ready,

    output  logic   [Parallel_Rd_Dim * MLEN - 1 : 0] [MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0]  prefetch_m_element,
    output  logic   [MLEN - 1 : 0]  [MXFP_SCALE_WIDTH - 1 : 0] prefetch_m_scale,
    output  logic   dma_m_ready,
    input   logic   prefetch_m_ready,
    output  logic   [ADDR_WIDTH - 1 : 0] prefetch_addr
);

    logic [HBM_ADDR_WIDTH - 1 : 0] hbm_addr_out;

    address_mapper #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .ADR_OPERAND_WIDTH(ADR_OPERAND_WIDTH),
        .HBM_ADDR_WIDTH(HBM_ADDR_WIDTH),
        .HBM_ADDR_REG_NUM(HBM_ADDR_REG_NUM)
    ) address_mapper_inst (
        .clk(clk),
        .rst(rst),
        .mapp_addr_en(h_op != STALL_H ),
        .set_addr_en(set_addr_reg_en),
        .addr_in_a(addr_in_a),
        .addr_in_b(addr_in_b),
        .target_operand(addr_reg_operand),
        .hbm_addr_out(hbm_addr_out)
    );


endmodule