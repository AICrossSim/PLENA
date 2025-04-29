`timescale 1ns / 1ps
`include "operation.svh"
`include "precision.svh"
`include "configuration.svh"

import precision_pkg::*;
import configuration_pkg::*;
import instruction_pkg::*;

// `include "tl_util.svh"

/*
Module      : Coprocessor Top Module
Status      : Under Development
*/

module coprocessor (
    input   logic clk,
    input   logic rst,
    // For testing, incoporate PCIe interface later
    input   logic [INSTRUCTION_LENGTH - 1 : 0] instruction,
    input   logic instruction_valid,

    // HBM Interface TileLink
    // `TL_DECLARE_DEVICE_PORT(DataWidth, AddrWidth, SourceWidth, 1, host),

    // For testing
    input logic [MLEN * Matrix_Parallel_Rd_Dim-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      prefetched_m_element,
    input logic [MLEN * Matrix_Parallel_Rd_Dim-1:0] [MXFP_SCALE_WIDTH-1:0]                     prefetched_m_scale,

    input logic [MLEN * Matrix_Parallel_Rd_Dim-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      prefetched_v_element_port1,
    input logic [MLEN * Matrix_Parallel_Rd_Dim-1:0] [MXFP_SCALE_WIDTH-1:0]                     prefetched_v_scale_port1,

    input logic [MLEN * Matrix_Parallel_Rd_Dim-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      prefetched_v_element_port2,
    input logic [MLEN * Matrix_Parallel_Rd_Dim-1:0] [MXFP_SCALE_WIDTH-1:0]                     prefetched_v_scale_port2
);

    // Control Signals
    // HBM Control
    logic hbm_m_prefetch_complete, hbm_m_prefetch_en;
    logic hbm_v_prefetch_complete, hbm_v_prefetch_en;
    logic hbm_v_write_en;

    // logic [MLEN*Matrix_Parallel_Rd_Dim-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      prefetched_m_element;
    // logic [MLEN*Matrix_Parallel_Rd_Dim-1:0] [MXFP_SCALE_WIDTH-1:0]                     prefetched_m_scale;

    // logic [MLEN*Matrix_Parallel_Rd_Dim-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      prefetched_v_element_port1;
    // logic [MLEN*Matrix_Parallel_Rd_Dim-1:0] [MXFP_SCALE_WIDTH-1:0]                     prefetched_v_scale_port1;

    // logic [MLEN*Matrix_Parallel_Rd_Dim-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      prefetched_v_element_port2;
    // logic [MLEN*Matrix_Parallel_Rd_Dim-1:0] [MXFP_SCALE_WIDTH-1:0]                     prefetched_v_scale_port2;
    
    // SRAM Control
    logic read_from_m_sram_en, m_transposed_rd_en;
    logic read_from_s_sram_en;


    // Operation Control
    M_OP            m_opcode;

    V_ELEMENT_OP    v_element_opcode;
    V_REDUCT_OP     v_reduce_opcode;
    logic           v_broadcast_fp2;

    S_FIXED_OP      s_fixed_opcode;
    S_FP_OP         s_fp_opcode;
    logic [IMM_WIDTH - 1 : 0] s_imm;
    logic [FIXED_OPERAND_WIDTH - 1 : 0] s_rs1, s_rs2, s_rd;
    logic [FP_OPERAND_WIDTH - 1 : 0]    s_fps1, s_fps2, s_fpd;


    // Frontend Control
    frontend #(
        .INSTRUCTION_LENGTH     (INSTRUCTION_LENGTH),
        .OPERAND_WIDTH          (OPERAND_WIDTH),
        .FIXED_OPERAND_WIDTH    (FIXED_OPERAND_WIDTH),
        .FP_OPERAND_WIDTH       (FP_OPERAND_WIDTH),
        .OPCODE_WIDTH           (OPCODE_WIDTH),
        .IMM_WIDTH              (IMM_WIDTH),
        .INST_BUFF_DEPTH        (INST_BUFF_DEPTH)
    ) frontend_init (
        .clk(clk),
        .rst(rst),
        .instruction        (instruction),
        .instruction_valid  (instruction_valid),
        .instruction_ready  (instruction_ready),

        .matrix_opcode      (m_opcode),
        .transposed_read    (m_transposed_rd_en),
        
        .element_opcode     (v_element_opcode),
        .reduce_opcode      (v_reduce_opcode),
        .broadcast_fp2      (v_broadcast_fp2),
        
        .fixed_opcode       (s_fixed_opcode),
        .imm                (s_imm),
        .rs1                (s_rs1),
        .rs2                (s_rs2),
        .rd                 (s_rd),
        .fp_opcode          (s_fp_opcode),
        .fps1               (s_fps1),
        .fps2               (s_fps2),
        .fpd                (s_fpd)
    );

    // Matrix
    parameter BLOCK_NUM = MLEN / BLOCK_DIM;

    logic [MLEN*Matrix_Parallel_Rd_Dim-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      fetched_m_element;
    logic [MLEN*Matrix_Parallel_Rd_Dim-1:0] [MXFP_SCALE_WIDTH-1:0]                      fetched_m_scale;
    logic fetched_m_valid, fetched_m_ready;

    logic [MLEN-1:0]             [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]                 fetched_v_element_port1;
    logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                                 fetched_v_scale_port1;
    logic fetched_v_valid_port1, fetched_v_ready_port1;

    logic [MLEN-1:0]             [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]                 fetched_v_element_port2;
    logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                                 fetched_v_scale_port2;
    logic fetched_v_valid_port2, fetched_v_ready_port2;

    logic [MLEN-1:0]             [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]                 m_out_element;
    logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                                 m_out_scale;
    logic m_out_valid, m_out_ready;

    generate;
        matrix_machine #(
            .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
            .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
            .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
            .MLEN(MLEN),
            .BLOCK_DIM(BLOCK_DIM),
            .PRODUCT_EXT_EXP_WIDTH(PRODUCT_EXT_EXP_WIDTH),
            .PRODUCT_EXT_MANT_WIDTH(PRODUCT_EXT_MANT_WIDTH),
            .BLOCK_ADD_EXT_EXP_WIDTH(BLOCK_ADD_EXT_EXP_WIDTH),
            .BLOCK_ADD_EXT_MANT_WIDTH(BLOCK_ADD_EXT_MANT_WIDTH),
            .FP_ADD_EXT_EXP_WIDTH(FP_ADD_EXT_EXP_WIDTH),
            .FP_ADD_EXT_MANT_WIDTH(FP_ADD_EXT_MANT_WIDTH)
        ) matrix_machine (
            .clk(clk),
            .rst(rst),

            .m_element  (fetched_m_element),
            .m_scale    (fetched_m_scale),
            .m_valid    (fetched_m_valid),
            .m_ready    (fetched_m_ready),

            .v_element(fetched_v_element_port1),
            .v_scale(fetched_v_scale_port1),
            .v_valid(fetched_v_valid_port1),
            .v_ready(),

            .o_element(fetched_v_element_port2),
            .o_scale(fetched_v_scale_port2),
            .o_valid(fetched_v_valid_port2),
            .o_ready(),

            .out_element(m_out_element),
            .out_scale(m_out_scale),
            .out_valid(m_out_valid),
            .out_ready(m_out_ready)
        );

        // Matrix Memory 
        matrix_sram_with_rounding #(
            .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
            .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
            .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
            .MLEN(MLEN),
            .BLOCK_DIM(BLOCK_DIM),
            .SRAM_DEPTH(MATRIX_SRAM_DEPTH),
            .PARALLEL_DIM(Matrix_Parallel_Rd_Dim)
        ) matrix_sram (
            .clk(clk),
            .rst(rst),
            .req(hbm_m_prefetch_en || read_from_m_sram_en),
            .transposed_read(m_transposed_rd_en),
            .write_en(hbm_m_prefetch_en),
            .write_response(fetched_m_valid),
            .sram_addr(fixed_out_1),
            .element_in(prefetched_m_element),
            .scale_in(prefetched_m_scale),
            .element_out(fetched_m_element),
            .scale_out(fetched_m_scale)
        );

    endgenerate

    logic read_from_s_sram_port_1_en, read_from_s_sram_port_2_en;
    logic write_to_s_sram_port_1_en, write_to_s_sram_port_2_en;

    // Scratchpad SRAM
    scratch_sram #(
        .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
        .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
        .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
        .VLEN(MLEN),
        .BLOCK_DIM(BLOCK_DIM),
        .SRAM_DEPTH(SCRATCHPAD_SRAM_DEPTH)
    ) vector_sram (
        .clk(clk),
        .rst(rst),
        .req_a(read_from_s_sram_port_1_en || read_from_s_sram_port_1_en),
        .write_en_a(write_to_s_sram_port_1_en),
        .sram_addr_a(fixed_out_1),
        .element_in_a(prefetched_v_element_port1),
        .scale_in_a(prefetched_v_scale_port1),
        .mask_in_a(),
        .element_out_a(fetched_v_element_port1),
        .scale_out_a(fetched_v_scale_port1),
        
        .req_b(read_from_s_sram_port_2_en || read_from_s_sram_port_2_en),
        .write_en_b(write_to_s_sram_port_1_en),
        .sram_addr_b(fixed_out_2),
        .element_in_b(prefetched_v_element_port2),
        .scale_in_b(prefetched_v_scale_port2),
        .mask_in_b(),
        .element_out_b(fetched_v_element_port2),
        .scale_out_b(fetched_v_scale_port2)
    );

    logic [MLEN-1:0]             [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]         v_out_element;
    logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                         v_out_scale;
    logic v_out_valid, v_out_ready;

    // Vector Compute Unit
    vector_machine #(
        .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
        .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
        .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
        .FP_EXP_WIDTH(FP_EXP_WIDTH),
        .FP_MANT_WIDTH(FP_MANT_WIDTH),
        .VLEN(MLEN),
        .BLOCK_DIM(BLOCK_DIM),
        .VE_EXT_EXP_WIDTH(0),
        .VE_EXT_MANT_WIDTH(0),
        .VR_EXT_EXP_WIDTH(0),
        .VR_EXT_MANT_WIDTH(0),
        .ROUND_FP_EN(1),
        .ROUND_FP_EXP_WIDTH(ROUND_FP_EXP_WIDTH),
        .ROUND_FP_MANT_WIDTH(ROUND_FP_MANT_WIDTH)
    ) vector_machine (
        .clk(clk),
        .rst(rst),
        .broadcast_fp2          (v_broadcast_fp2),
        .element_v_control      (v_element_opcode),
        .reduct_v_control       (v_reduce_opcode),
        .v_a_element            (fetched_v_element_port1),
        .v_a_scale              (fetched_v_scale_port1),
        .v_a_valid              (),
        .v_a_ready              (),

        .v_b_element            (fetched_v_element_port2),
        .v_b_scale              (fetched_v_scale_port2),
        .v_b_valid              (),
        .v_b_ready              (),

        .s_in(fp_s_in),
        .s_in_valid(),
        .s_in_ready(),
        .s_out(fp_s_out),
        .s_out_valid(),
        .s_out_ready(),

        .v_out_element          (v_out_element),
        .v_out_scale            (v_out_scale),
        .v_out_valid            (v_out_valid),
        .v_out_ready            (v_out_ready)
    );

    logic [FP_EXP_WIDTH + FP_MANT_WIDTH -1 : 0] fp_s_in;
    logic [FP_EXP_WIDTH + FP_MANT_WIDTH -1 : 0] fp_s_out;
    logic [FIXED_DATA_WIDTH - 1 : 0] fixed_in;
    logic [FIXED_DATA_WIDTH - 1 : 0] fixed_out_1;
    logic [FIXED_DATA_WIDTH - 1 : 0] fixed_out_2;

    // Scalar Compute Unit
    scalar_machine #(
        .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
        .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
        .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
        .FP_EXP_WIDTH(FP_EXP_WIDTH),
        .FP_MANT_WIDTH(FP_MANT_WIDTH),
        .FIXED_DATA_WIDTH(FIXED_DATA_WIDTH)
    ) scalar_machine (
        .clk(clk),
        .rst(rst),
        .fp_control(fp_opcode),
        .fixed_control(fixed_opcode),
        .rs1(s_rs1),
        .rs2(s_rs2),
        .rd(s_rd),
        .fp_rs1(s_fps1),
        .fp_rs2(s_fps2),
        .fp_rd(s_fpd),
        .fixed_in(fixed_in),
        .imm_in(s_imm),
        .fixed_out_1(fixed_out_1),
        .fixed_out_2(fixed_out_2),
        .fp_in(fp_s_out),
        .fp_out_1(fp_s_in)
    );

    prim_generic_ram_1p #(
        .Width(FIXED_DATA_WIDTH),
        .Depth(SRAM_DEPTH),
        .DataBitsPerMask(FIXED_DATA_WIDTH)
    ) scalar_sram (
        .clk_i(clk),
        .rst_ni(rst),

        .req_i(),
        .write_i(),
        .addr_i()
        .wdata_i(),
        .wmask_i(),
        .data_in_a(),
        .rdata_o(),

    );

    // SRAM for Scalar

endmodule