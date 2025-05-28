`timescale 1ns / 1ps

`include "operation.svh"
`include "precision.svh"
`include "configuration.svh"
`include "tl_util.svh"
`include "Global_Define.vh"

/*
Module      : Coprocessor Top Module
Status      : Under Development
Description : This module serves as the top level of the coprocessor, 
              controlling the dataflow between the instruction decoder, computation units and memory units.
              It currently only supports single batch execution.
*/

module coprocessor #(
        // Simulation Purpose
        `ifdef SIMULATION
            parameter string FP_MEM_INIT_FILE = " ",
            parameter string FIXED_MEM_INIT_FILE = " "
        `endif
)(
    input   logic clk,
    input   logic rst,
    // For testing, incoporate PCIe interface later
    input   logic [INSTRUCTION_LENGTH - 1 : 0] instruction,
    input   logic instruction_valid,
    output  logic instruction_ready,

    // HBM Interface TileLink
    `TL_DECLARE_HOST_PORT(HBM_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, out_element),
    `TL_DECLARE_HOST_PORT(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, out_scale)
);
    // Import Packages
    import precision_pkg::*;
    import configuration_pkg::*;
    import instruction_pkg::*;

    // Parameter Def
    localparam MATRIX_LOAD_ITERATION = MLEN / Matrix_Parallel_Rd_Dim;
    localparam MATRIX_COUNTER_WIDTH = $clog2(MATRIX_LOAD_ITERATION);
    localparam BLOCK_NUM = MLEN / BLOCK_DIM;
    
    // Execution Control
    OP_BUNDLE   decoded_op_bundle, assigned_op_bundle;
    S_FIXED_OP  exe_fixed_op;
    logic pipeline_stall;
    MEM_WEN_INFO mem_write_control;

    // Status Tracking
    logic hbm_in_used;
    logic stall_req_from_fp, fixed_stall_req;
    logic v_in_prep, m_in_prep;
    logic sfu_in_use;

    // Memory Control Signals Declaration
    MEM_WREQ_INFO mem_write_req;

    // HBM Control
    logic hbm_m_prefetch_complete, hbm_m_prefetch_en;
    logic hbm_v_prefetch_complete, hbm_v_prefetch_en;
    logic [MLEN * Matrix_Parallel_Rd_Dim-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      prefetch_m_element;
    logic [MLEN * Matrix_Parallel_Rd_Dim-1:0] [MXFP_SCALE_WIDTH-1:0]                      prefetch_m_scale;
    logic hbm_ready_to_write;
    logic [MATRIX_COUNTER_WIDTH - 1 : 0] m_sram_continuous_prefetch_counter;
    

    // Scratchpad SRAM
    logic [VLEN-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      v_element_port_a_in;
    logic [VLEN-1:0] [MXFP_SCALE_WIDTH-1:0]                      v_scale_port_a_in;
    logic [VLEN-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]      v_element_port_b_in;
    logic [VLEN-1:0] [MXFP_SCALE_WIDTH-1:0]                      v_scale_port_b_in;
    
    // Scalar Machine Control
    logic [IMM_WIDTH - 1 : 0] s_imm;
    logic [FIXED_OPERAND_WIDTH - 1 : 0] s_rs1,  s_rs2,  s_rd;

    logic       m_write_request, v_write_request;
    

    // -----------------------------
    // Dataflow & Execution Control
    // -----------------------------
    
    // Frontend
    decoder #(
        .INSTRUCTION_LENGTH         (INSTRUCTION_LENGTH),
        .OPERAND_WIDTH              (OPERAND_WIDTH),
        .OPCODE_WIDTH               (OPCODE_WIDTH),
        .IMM_WIDTH                  (IMM_WIDTH),
        .INST_BUFF_DEPTH            (OPCODE_WIDTH)
    ) decoder_init (
        .clk(clk),
        .rst(rst),
        .pipeline_stall         (pipeline_stall),
        .instruction            (instruction),
        .instruction_valid      (instruction_valid),
        .instruction_ready      (instruction_ready),
        .decoded_op_bundle      (decoded_op_bundle),
        .exe_fixed_op           (exe_fixed_op),
        .rs1                    (s_rs1),
        .rs2                    (s_rs2),
        .rd                     (s_rd),
        .imm                    (s_imm)
    );

    pipeline_control #(
        .OPERAND_WIDTH          (OPERAND_WIDTH),
        .FIXED_OPERAND_WIDTH    (FIXED_OPERAND_WIDTH),
        .FP_OPERAND_WIDTH       (FP_OPERAND_WIDTH),
        .FIXED_DATA_WIDTH       (FIXED_DATA_WIDTH),
        .IMM_WIDTH              (IMM_WIDTH)
    ) pipeline_control_init (
        .clk(clk),
        .rst(rst),
        .decoded_op_bundle      (decoded_op_bundle),
        .fixed_addr_1           (fixed_out_1),
        .fixed_addr_2           (fixed_out_2),
        .s_sram_wen_a           (s_sram_wen_a),
        .s_sram_addr_a          (s_sram_addr_a),
        .s_sram_wen_b           (s_sram_wen_b),
        .s_sram_addr_b          (s_sram_addr_b),
        .mem_write_req          (mem_write_req),
        .hbm_in_used            (hbm_in_used),
        .continuous_m_prefetch  (continuous_prefetch_m_en),
        .fp_stall_req           (stall_req_from_fp),
        .fixed_stall_req        (fixed_stall_req),
        .m_load_in_process      (m_in_prep),
        .v_load_in_process      (v_in_prep),
        .sfu_in_use             (sfu_in_use),
        .pipeline_stall_req     (pipeline_stall),
        .assigned_op_bundle     (assigned_op_bundle),
        .mem_write_control      (mem_write_control)
    );


    // Dataflow Control
    data_flow_control #(
        .OPERAND_WIDTH(FIXED_OPERAND_WIDTH),
        .VLEN(MLEN),
        .MLEN(MLEN),
        .Parallel_Rd_Dim(Matrix_Parallel_Rd_Dim)
    ) data_flow_init(
        .clk(clk),
        .rst(rst),
        .assigned_op_bundle     (assigned_op_bundle),
        .mem_write_control      (mem_write_control),
        .m_offset_addr          (m_offset_addr),
        .write_req              (mem_write_req),
        .m_m_ready              (m_m_ready),
        .m_m_valid              (m_m_valid),
        .m_v_valid              (m_v_valid),
        .m_v_ready              (m_v_ready),
        .m_o_valid              (m_o_valid),
        .m_o_ready              (m_o_ready),
        .m_out_valid            (m_out_valid),
        .m_out_ready            (m_out_ready),
        .m_write_request        (m_write_request),
        .m_write_addr           (m_waddr),
        .m_sram_addr            (m_sram_addr),
        .m_sram_wen             (m_sram_wen),
        .m_sram_req             (m_sram_req),
        .m_sram_transposed_read (m_sram_transposed_read),
        .v_v_a_valid            (v_v_a_valid),
        .v_v_a_ready            (v_v_a_ready),
        .v_v_b_valid            (v_v_b_valid),
        .v_v_b_ready            (v_v_b_ready),
        .v_v_out_valid          (v_v_out_valid),
        .v_v_out_ready          (v_v_out_ready),
        .v_s_in_valid           (v_s_in_valid),
        .v_s_in_ready           (v_s_in_ready),
        .v_write_request        (v_write_request),
        .v_write_addr           (v_waddr),
        .s_sram_req_a           (s_sram_req_a),
        .s_sram_wen_a           (s_sram_wen_a),
        .s_sram_addr_a          (s_sram_addr_a),
        .s_sram_mask_a          (s_sram_mask_a),
        .select_write_data_a    (select_write_data_a),
        .s_sram_req_b           (s_sram_req_b),
        .s_sram_wen_b           (s_sram_wen_b),
        .s_sram_addr_b          (s_sram_addr_b),
        .s_sram_mask_b          (s_sram_mask_b),
        .dma_m_ready            (hbm_m_prefetch_complete),
        .dma_v_ready            (hbm_v_prefetch_complete),
        .continuous_prefetch_m_en(continuous_prefetch_m_en),
        .hbm_ready_to_write           (hbm_ready_to_write),
        .m_sram_continuous_prefetch_counter(m_sram_continuous_prefetch_counter)
    );

    // -----------------------------
    // Computation Units
    // -----------------------------
 
    // Matrix
    logic [FIXED_DATA_WIDTH - 1 : 0] m_sram_addr;
    logic [FIXED_DATA_WIDTH - 1 : 0] m_waddr, v_waddr;
    logic m_m_ready,    m_m_valid;
    logic m_v_valid,    m_v_ready;
    logic m_o_valid,    m_o_ready;
    logic m_out_valid,  m_out_ready;
    logic m_sram_wen, m_sram_req, m_sram_transposed_read;
    logic continuous_prefetch_m_en;

    logic [MLEN * Matrix_Parallel_Rd_Dim-1:0] [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]    fetched_m_element;
    logic [BLOCK_NUM * Matrix_Parallel_Rd_Dim-1:0] [MXFP_SCALE_WIDTH-1:0]               fetched_m_scale;

    logic [MLEN-1:0]             [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]                 m_out_element;
    logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                                 m_out_scale;
    // Vector
    logic v_v_a_valid,      v_v_a_ready;
    logic v_v_b_valid,      v_v_b_ready;
    logic v_v_out_valid,    v_v_out_ready;
    logic v_s_in_valid,     v_s_in_ready;
    logic v_s_out_valid,    v_s_out_ready;

    logic select_write_data_a;
    logic s_sram_req_a, s_sram_req_b;
    logic s_sram_wen_a, s_sram_wen_b;
    logic [FIXED_DATA_WIDTH - 1 : 0] s_sram_addr_a, s_sram_addr_b;
    logic [BLOCK_NUM-1:0] s_sram_mask_a, s_sram_mask_b;
    logic [FIXED_DATA_WIDTH - 1 : 0] prefetch_addr;

    logic [MLEN-1:0]             [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]                 v_element_port_a_out;
    logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                                 v_scale_port_a_out;
    logic [MLEN-1:0]             [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]                 v_element_port_b_out;
    logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                                 v_scale_port_b_out;
    logic [MLEN-1:0]             [(MXFP_MANT_WIDTH + MXFP_EXP_WIDTH):0]                 v_out_element;
    logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                                 v_out_scale;

    // Scalar
    logic [FP_EXP_WIDTH + FP_MANT_WIDTH -1 : 0] fp_s_in;
    logic [FP_EXP_WIDTH + FP_MANT_WIDTH -1 : 0] fp_s_out;
    logic [FIXED_DATA_WIDTH - 1 : 0] fixed_in;
    logic [FIXED_DATA_WIDTH - 1 : 0] fixed_out_1;
    logic [FIXED_DATA_WIDTH - 1 : 0] fixed_out_2;
    logic [FIXED_DATA_WIDTH - 1 : 0] m_offset_addr;
    logic [FP_OPERAND_WIDTH - 1 : 0] s_wtarget_from_v;

                
    generate;
        // Matrix Compute Unit
        matrix_machine #(
        ) matrix_machine_init (
            .clk(clk),
            .rst(rst),
            .matrix_opcode          (assigned_op_bundle.m_op),
            .prepare_flag           (m_in_prep),
            .set_offset_addr        ((assigned_op_bundle.c_op == SET_M_OFFSET)),
            .addr_in                (assigned_op_bundle.addr_2),
            .offset_addr_out        (m_offset_addr),
            .m_element              (fetched_m_element),
            .m_scale                (fetched_m_scale),
            .m_valid                (m_m_valid),
            .m_ready                (m_m_ready),
            .v_element              (v_element_port_a_out),
            .v_scale                (v_scale_port_a_out),
            .v_valid                (m_v_valid),
            .v_ready                (m_v_ready),
            .o_element              (v_element_port_b_out),
            .o_scale                (v_scale_port_b_out),
            .o_valid                (m_o_valid),
            .o_ready                (m_o_ready),
            .result_waddr_update    (assigned_op_bundle.update_m_waddr),
            .out_element            (m_out_element),
            .out_scale              (m_out_scale),
            .out_valid              (m_out_valid),
            .out_ready              (m_out_ready),
            .m_waddr                (m_waddr),
            .m_wreq                 (m_write_request)
        );

        // Vector Compute Unit
        vector_machine #(
        ) vector_machine_init (
            .clk(clk),
            .rst(rst),
            .broadcast_fp2          (assigned_op_bundle.v_broadcast_en),
            .element_v_control      (assigned_op_bundle.v_ele_op),
            .reduct_v_control       (assigned_op_bundle.v_reduct_op),
            .in_preparation_stage   (v_in_prep),
            .v_a_element            (v_element_port_a_out),
            .v_a_scale              (v_scale_port_a_out),
            .v_a_valid              (v_v_a_valid),
            .v_a_ready              (v_v_a_ready),
            .v_b_element            (v_element_port_b_out),
            .v_b_scale              (v_scale_port_b_out),
            .v_b_valid              (v_v_b_valid),
            .v_b_ready              (v_v_b_ready),
            .s_in                   (fp_s_in),
            .s_in_valid             (v_s_in_valid),
            .s_in_ready             (v_s_in_ready),
            .s_wtarget              (s_fps2),
            .result_waddr           (assigned_op_bundle.addr_2),
            .result_waddr_update    (assigned_op_bundle.update_v_waddr),
            .v_out_element          (v_out_element),
            .v_out_scale            (v_out_scale),
            .v_out_valid            (v_v_out_valid),
            .v_out_ready            (v_v_out_ready),
            .v_waddr                (v_waddr),
            .v_wreq                 (v_write_request),
            .s_out                  (fp_s_out),
            .s_out_valid            (v_s_out_valid),
            .s_out_ready            (v_s_out_ready),
            .s_out_rd               (s_wtarget_from_v)
        );

        // Scalar Compute Unit
        scalar_machine #(
            `ifdef SIMULATION
                .FP_MEM_INIT_FILE(FP_MEM_INIT_FILE),
                .FIXED_MEM_INIT_FILE(FIXED_MEM_INIT_FILE)
            `endif
        ) scalar_machine_init (
            .clk(clk),
            .rst(rst),
            .assigned_op_bundle     (assigned_op_bundle),
            .assigned_fixed_op      (exe_fixed_op),
            .rs1                    (s_rs1),
            .rs2                    (s_rs2),
            .rd                     (s_rd),
            .fixed_in               (fixed_in),
            .imm_in                 (s_imm),
            .fixed_out_1            (fixed_out_1),
            .fixed_out_2            (fixed_out_2),
            .external_fp_in         (fp_s_out),
            .external_fp_in_valid   (v_s_out_valid),
            .external_fp_in_ready   (v_s_out_ready),
            .external_fp_wtarget    (s_wtarget_from_v),
            .fp_out                 (fp_s_in),
            .sfu_in_use             (sfu_in_use),
            .fp_stall_req           (stall_req_from_fp),
            .fixed_stall_req        (fixed_stall_req)
        );

    endgenerate


    // -----------------------------
    // Memory Units
    // -----------------------------

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
        .req                (m_sram_req),
        .transposed_read    (m_sram_transposed_read),
        .write_en           (m_sram_wen),
        .sram_addr          (m_sram_addr),
        .element_in         (prefetch_m_element),
        .scale_in           (prefetch_m_scale),
        .element_out        (fetched_m_element),
        .scale_out          (fetched_m_scale)
    );

    // Scratchpad SRAM
    // Port A ->  R: Matrix Multiplicand Vector or Vector Operand               W: Vector Result from either Matrix or Vector Machine, 
    // Port B ->  R: Matrix Offest Vector or Vector Operand or HBM Write Data   W: Vector Prefetch
    assign v_element_port_a_in = select_write_data_a ? m_out_element : v_out_element;
    assign v_scale_port_a_in   = select_write_data_a ? m_out_scale : v_out_scale;
    
    scratch_sram #(
        .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
        .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
        .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
        .VLEN(VLEN),
        .BLOCK_DIM(BLOCK_DIM),
        .SRAM_DEPTH(SCRATCHPAD_SRAM_DEPTH)
    ) vector_sram (
        .clk(clk),
        .rst(rst),
        .req_a              (s_sram_req_a),
        .write_en_a         (s_sram_wen_a),
        .sram_addr_a        (s_sram_addr_a),
        .element_in_a       (v_element_port_a_in),
        .scale_in_a         (v_scale_port_a_in),
        .mask_in_a          (s_sram_mask_a),
        .element_out_a      (v_element_port_a_out),
        .scale_out_a        (v_scale_port_a_out),
        
        .req_b              (s_sram_req_b),
        .write_en_b         (s_sram_wen_b),
        .sram_addr_b        (s_sram_addr_b),
        .element_in_b       (v_element_port_b_in),
        .scale_in_b         (v_scale_port_b_in),
        .mask_in_b          (s_sram_mask_b),
        .element_out_b      (v_element_port_b_out),
        .scale_out_b        (v_scale_port_b_out)
    );

    // HBM Control
    // TL Declaration
    `TL_DECLARE(HBM_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, element);
    `TL_BIND_HOST_PORT(out_element, element);

    `TL_DECLARE(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, scale);
    `TL_BIND_HOST_PORT(out_scale, scale);

    logic [MLEN * MLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) - 1 : 0] hbm_element_out;
    logic [MLEN * BLOCK_NUM * MXFP_SCALE_WIDTH - 1 : 0] hbm_scale_out;
    logic hbm_prefetch_valid, hbm_prefetch_en;
    logic [HBM_ADDR_WIDTH - 1 : 0] addr_to_prefetch, addr_for_prefetched_data;

    logic hbm_write_en;
    logic [Matrix_Parallel_Rd_Dim * MLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) - 1 : 0] hbm_element_in;
    logic [Matrix_Parallel_Rd_Dim * BLOCK_NUM * MXFP_SCALE_WIDTH - 1 : 0] hbm_scale_in;
    logic hbm_write_valid, hbm_write_ready;

    hbm_arbiter #(
        .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
        .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
        .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
        .BLOCK_DIM(BLOCK_DIM),
        .ADDR_WIDTH(FIXED_DATA_WIDTH),
        .MLEN(MLEN),
        .VLEN(VLEN),
        .Parallel_Rd_Dim(Matrix_Parallel_Rd_Dim)
    ) hbm_arbiter_init (
        .clk(clk),
        .rst(rst),

        // HBM Prefetching
        .prefetch_element       (hbm_element_out),
        .prefetch_scale         (hbm_scale_out),
        .prefetch_data_valid    (hbm_prefetch_valid),
        .hbm_prefetch_en        (hbm_prefetch_en),
        .addr_to_prefetch       (addr_to_prefetch),
        .addr_for_prefetched_data (addr_for_prefetched_data),

        // HBM Write
        .hbm_write_en           (hbm_write_en),
        .hbm_write_ready        (hbm_write_ready),
        .hbm_write_valid        (hbm_write_valid),
        .hbm_write_element      (hbm_element_in),
        .hbm_write_scale        (hbm_scale_in),

        // Matrix SRAM
        // Write to Matrix SRAM
        .prefetch_m_ready       (m_sram_wen),
        .prefetch_m_element     (prefetch_m_element),
        .prefetch_m_scale       (prefetch_m_scale),

        // Vector SRAM
        // Write to Vector SRAM
        .prefetch_v_ready       (s_sram_wen_b),
        .prefetch_v_element     (v_element_port_b_in),
        .prefetch_v_scale       (v_scale_port_b_in),

        // Read from Vector SRAM
        .v_out_element          (v_element_port_b_out),
        .v_out_scale            (v_scale_port_b_out),
        .v_out_data_wen         (hbm_ready_to_write), // Left for store vector into HBM

        // HBM Operation
        .h_op(assigned_op_bundle.h_op),
        .continuous_prefetch_m_en (continuous_prefetch_m_en),
        .hbm_m_prefetch_complete (hbm_m_prefetch_complete),
        .hbm_v_prefetch_complete (hbm_v_prefetch_complete),
        .hbm_arbiter_busy         (hbm_in_used)
    );

    hbm_controller #(
        .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
        .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
        .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
        .BLOCK_DIM(BLOCK_DIM),
        .ADDR_WIDTH(FIXED_DATA_WIDTH),
        .MLEN(MLEN),
        .VLEN(VLEN),
        .Parallel_Rd_Dim(Matrix_Parallel_Rd_Dim),
        .ADR_OPERAND_WIDTH(ADR_OPERAND_WIDTH),
        .HBM_ADDR_WIDTH(HBM_ADDR_WIDTH),
        .HBM_ADDR_REG_NUM(HBM_ADDR_REG_NUM),
        .SourceWidth(SourceWidth),
        .SinkWidth(SinkWidth),
        .HBM_ELE_WIDTH(HBM_ELE_WIDTH),
        .HBM_SCALE_WIDTH(HBM_SCALE_WIDTH)
    ) hbm_controller_init (
        .clk(clk),
        .rst(rst),

        // Address Register
        .set_addr_reg_en                    (assigned_op_bundle.c_op == SET_ADDR_REG),
        .addr_in_a                          (fixed_out_1),
        .addr_in_b                          (fixed_out_2),
        // Address Register Index
        .addr_reg_write_operand             (s_rd),
        .addr_reg_read_operand              (s_rs2),

        // Prefetching
        .prefetch_element                   (hbm_element_out),
        .prefetch_scale                     (hbm_scale_out),
        .prefetch_data_valid                (hbm_prefetch_valid),
        .hbm_prefetch_en                    (hbm_prefetch_en),
        .addr_to_prefetch                   (addr_to_prefetch),
        .addr_for_prefetched_data           (addr_for_prefetched_data),
        .continuous_prefetch_m_en           (continuous_prefetch_m_en),
        .m_sram_continuous_prefetch_counter (m_sram_continuous_prefetch_counter),

        // HBM Write
        .hbm_write_en                       (hbm_write_en),
        .hbm_write_valid                    (hbm_write_valid),
        .hbm_write_ready                    (hbm_write_ready),
        .hbm_write_element                  (hbm_element_in),
        .hbm_write_scale                    (hbm_scale_in),
        .hbm_prefetch_content_exist         (hbm_m_prefetch_complete || hbm_v_prefetch_complete),

        // HBM Interface
        `TL_CONNECT_HOST_PORT(host_element, element),
        `TL_CONNECT_HOST_PORT(host_scale, scale)

    );

endmodule