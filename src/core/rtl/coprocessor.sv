`timescale 1ns / 1ps

`include "operation.svh"
`include "precision.svh"
`include "configuration.svh"
`include "tl_util.svh"
`include "global_define.vh"

/*
Module      : Coprocessor Top Module
Status      : Under Development
Description : This module serves as the top level of the coprocessor, 
              controlling the dataflow between the instruction decoder, computation units and memory units.
              It currently only supports single batch execution.
*/

module coprocessor import configuration_pkg::*; import instruction_pkg::*; #(
    parameter string FP_MEM_INIT_FILE       = "",
    parameter string FIXED_MEM_INIT_FILE    = "",
    parameter string V_SRAM_RESULT_FILE     = ""
)(
    input   logic clk,
    input   logic rst,
    // For testing, incoporate PCIe interface later
    input   logic [INSTRUCTION_LENGTH - 1 : 0] instruction,
    input   logic instruction_valid,
    output  logic instruction_ready,

    // HBM Interface 1 for Matrix
    `TL_DECLARE_HOST_PORT(HBM_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, m_out_element),
    `TL_DECLARE_HOST_PORT(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, m_out_scale),
    // HBM Interface 2 for Vector
    `TL_DECLARE_HOST_PORT(HBM_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, v_out_element),
    `TL_DECLARE_HOST_PORT(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, v_out_scale)
);
    // Import Packages
    import precision_pkg::*;
   
    // Parameter Def
    localparam MATRIX_LOAD_ITERATION = MLEN / Matrix_Parallel_Rd_Dim;
    localparam MATRIX_COUNTER_WIDTH = $clog2(MATRIX_LOAD_ITERATION);
    localparam BLOCK_NUM = MLEN / BLOCK_DIM;
    
    // Execution Control
    OP_BUNDLE   decode_stage_op, exe_stage_op;
    S_FIXED_OP  exe_fixed_op;
    logic pipeline_stall;
    MEM_WEN_INFO mem_write_control;

    // Status Tracking
    logic hbm_in_used;
    logic stall_req_from_fp, fixed_stall_req;
    logic v_in_prep, m_in_prep;
    logic sfu_in_use;
    logic m_prefetch_data_not_ready, v_prefetch_data_not_ready;
    logic m_complete_acc_writeback;

    // Memory Control Signals Declaration
    MEM_WREQ_INFO mem_write_req;

    // Matrix SRAM
    logic [FIXED_DATA_WIDTH - 1 : 0] m_sram_raddr, m_sram_waddr;
    logic [FIXED_DATA_WIDTH - 1 : 0] m_waddr, v_waddr;
    logic m_m_ready,    m_m_valid;
    logic m_v_valid,    m_v_ready;
    logic m_out_valid,  m_out_ready;
    logic m_sram_wen, m_sram_req, m_sram_transposed_read;

    // HBM Control
    logic hbm_m_prefetch_valid, hbm_m_prefetch_en;
    logic hbm_v_prefetch_valid, hbm_v_prefetch_en;
    logic [MLEN * Matrix_Parallel_Rd_Dim-1:0] [(LOW_MXFP_MANT_WIDTH + LOW_MXFP_EXP_WIDTH):0]        prefetch_m_element;
    logic [MLEN * Matrix_Parallel_Rd_Dim-1:0] [MXFP_SCALE_WIDTH-1:0]                                prefetch_m_scale;
    logic hbm_ready_to_write;
    logic hbm_m_prefetch_in_progress, hbm_v_prefetch_in_progress;
    logic hbm_m_req_prefetch_data, hbm_v_req_prefetch_data;

    // Vector SRAM
    logic [VLEN-1:0] [(HIGH_MXFP_MANT_WIDTH + HIGH_MXFP_EXP_WIDTH):0]       v_element_port_b_in;
    logic [VLEN-1:0] [MXFP_SCALE_WIDTH-1:0]                                 v_scale_port_b_in;
    
    // Scalar Machine Control
    logic [IMM_WIDTH - 1 : 0] s_imm;
    logic [FIXED_OPERAND_WIDTH - 1 : 0] s_rs1,  s_rs2,  s_rd;

    logic  m_write_request, v_write_request;
    

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
        .decode_stage_op        (decode_stage_op),
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
        .decode_stage_op                (decode_stage_op),
        .fixed_addr_1                   (fixed_out_1),
        .fixed_addr_2                   (fixed_out_2),
        .v_sram_wen_a                   (v_sram_wen_a),
        .v_sram_addr_a                  (v_sram_addr_a),
        .v_sram_wen_b                   (v_sram_wen_b),
        .v_sram_addr_b                  (v_sram_addr_b),
        .hbm_m_prefetch_in_progress     (hbm_m_prefetch_in_progress),
        .hbm_v_prefetch_in_progress     (hbm_v_prefetch_in_progress),
        .mem_write_req                  (mem_write_req),
        .hbm_in_used                    (hbm_in_used),
        .fp_stall_req                   (stall_req_from_fp),
        .fixed_stall_req                (fixed_stall_req),
        .m_load_in_process              (m_in_prep),
        .v_load_in_process              (v_in_prep),
        .sfu_in_use                     (sfu_in_use),
        .m_complete_acc_writeback       (m_complete_acc_writeback),
        .pipeline_stall_req             (pipeline_stall),
        .exe_stage_op                   (exe_stage_op),
        .mem_write_control              (mem_write_control)
    );


    // Dataflow Control
    data_flow_control #(
    ) data_flow_init(
        .clk(clk),
        .rst(rst),
        .exe_stage_op               (exe_stage_op),
        .mem_write_control          (mem_write_control),
        .write_req                  (mem_write_req),
        .m_m_ready                  (m_m_ready),
        .m_m_valid                  (m_m_valid),
        .m_v_valid                  (m_v_valid),
        .m_v_ready                  (m_v_ready),
        .m_out_valid                (m_out_valid),
        .m_out_ready                (m_out_ready),
        .m_complete_acc_writeback   (m_complete_acc_writeback),
        .m_write_request            (m_write_request),
        .m_write_addr               (m_waddr),
        .m_sram_raddr               (m_sram_raddr),
        .m_sram_waddr               (m_sram_waddr),
        .m_sram_wen                 (m_sram_wen),
        .m_sram_req                 (m_sram_req),
        .m_sram_transposed_read     (m_sram_transposed_read),
        .m_prefetch_data_not_ready  (m_prefetch_data_not_ready),
        .v_v_a_valid                (v_v_a_valid),
        .v_v_a_ready                (v_v_a_ready),
        .v_v_b_valid                (v_v_b_valid),
        .v_v_b_ready                (v_v_b_ready),
        .v_v_out_valid              (v_v_out_valid),
        .v_v_out_ready              (v_v_out_ready),
        .v_s_in_valid               (v_s_in_valid),
        .v_s_in_ready               (v_s_in_ready),
        .v_write_request            (v_write_request),
        .v_write_addr               (v_waddr),
        .v_sram_req_a               (v_sram_req_a),
        .v_sram_wen_a               (v_sram_wen_a),
        .v_sram_addr_a              (v_sram_addr_a),
        .v_sram_mask_a              (v_sram_mask_a),
        .select_write_data_a        (select_write_data_a),
        .v_sram_mxfp_req_b          (v_sram_mxfp_req_b),
        .v_sram_req_b               (v_sram_req_b),
        .v_sram_wen_b               (v_sram_wen_b),
        .v_sram_addr_b              (v_sram_addr_b),
        .v_sram_mask_b              (v_sram_mask_b),
        .v_prefetch_data_not_ready  (v_prefetch_data_not_ready),
        .prefetch_m_valid           (hbm_m_prefetch_valid),
        .prefetch_v_valid           (hbm_v_prefetch_valid),
        .hbm_ready_to_write         (hbm_ready_to_write),
        .hbm_m_req_prefetch_data    (hbm_m_req_prefetch_data),
        .hbm_v_req_prefetch_data    (hbm_v_req_prefetch_data)
    );

    // -----------------------------
    // Computation Units
    // -----------------------------
 
    // Matrix
    logic [MLEN * Matrix_Parallel_Rd_Dim-1:0] [(LOW_MXFP_MANT_WIDTH + LOW_MXFP_EXP_WIDTH):0]    fetched_m_element;
    logic [BLOCK_NUM * Matrix_Parallel_Rd_Dim-1:0] [MXFP_SCALE_WIDTH-1:0]                       fetched_m_scale;
    logic [MLEN-1:0][S_FP_EXP_WIDTH + S_FP_MANT_WIDTH:0]                                        m_out_v_fp;

    // Vector
    logic v_v_a_valid,      v_v_a_ready;
    logic v_v_b_valid,      v_v_b_ready;
    logic v_v_out_valid,    v_v_out_ready;
    logic v_s_in_valid,     v_s_in_ready;
    logic v_s_out_valid,    v_s_out_ready;

    logic select_write_data_a;
    logic v_sram_req_a, v_sram_req_b, v_sram_mxfp_req_b;
    logic v_sram_wen_a, v_sram_wen_b;
    logic [FIXED_DATA_WIDTH - 1 : 0] v_sram_addr_a, v_sram_addr_b;
    logic [VLEN-1:0] v_sram_mask_a, v_sram_mask_b;

    logic [VLEN-1:0]             [(HIGH_MXFP_MANT_WIDTH + HIGH_MXFP_EXP_WIDTH):0]                 v_element_port_b_out;
    logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                                           v_scale_port_b_out;
    logic [VLEN-1:0]             [(HIGH_MXFP_MANT_WIDTH + HIGH_MXFP_EXP_WIDTH):0]                 v_element_port_a_out;
    logic [BLOCK_NUM-1:0]        [MXFP_SCALE_WIDTH-1:0]                                           v_scale_port_a_out;
    logic port_b_mxfp_out_valid;

    logic [VLEN-1:0][V_FP_EXP_WIDTH + V_FP_MANT_WIDTH:0]                                v_port_a_out_fp;
    logic [VLEN-1:0][V_FP_EXP_WIDTH + V_FP_MANT_WIDTH:0]                                v_port_b_out_fp;
    logic [VLEN-1:0][V_FP_EXP_WIDTH + V_FP_MANT_WIDTH:0]                                v_out_fp;

    // Scalar
    logic [V_FP_EXP_WIDTH + V_FP_MANT_WIDTH -1 : 0] fp_s_in;
    logic [V_FP_EXP_WIDTH + V_FP_MANT_WIDTH -1 : 0] fp_s_out;
    logic [FIXED_DATA_WIDTH - 1 : 0] fixed_out_1;
    logic [FIXED_DATA_WIDTH - 1 : 0] fixed_out_2;
    logic [FP_OPERAND_WIDTH - 1 : 0] s_wtarget_from_v;

                
    generate;
        // Matrix Compute Unit
        matrix_machine_v2 #(
        ) matrix_machine_init (
            .clk(clk),
            .rst(rst),
            .exe_stage_op           (exe_stage_op),
            .load_in_progress       (m_in_prep),
            .m_element              (fetched_m_element),
            .m_scale                (fetched_m_scale),
            .m_valid                (m_m_valid),
            .m_ready                (m_m_ready),
            .v_element              (v_element_port_a_out),
            .v_scale                (v_scale_port_a_out),
            .v_valid                (m_v_valid),
            .v_ready                (m_v_ready),
            .out_v_fp               (m_out_v_fp),
            .out_valid              (m_out_valid),
            .out_ready              (m_out_ready),
            .m_waddr                (m_waddr),
            .m_wreq                 (m_write_request)
        );

        // Vector Compute Unit
        vector_machine_v2 #(
        ) vector_machine_init (
            .clk(clk),
            .rst(rst),
            .broadcast_fp2          (exe_stage_op.v_broadcast_en),
            .element_v_control      (exe_stage_op.v_ele_op),
            .reduct_v_control       (exe_stage_op.v_reduct_op),
            .in_preparation_stage   (v_in_prep),
            .v_a_in                 (v_port_a_out_fp),
            .v_a_valid              (v_v_a_valid),
            .v_a_ready              (v_v_a_ready),
            .v_b_in                 (v_port_b_out_fp),
            .v_b_valid              (v_v_b_valid),
            .v_b_ready              (v_v_b_ready),
            .s_in                   (fp_s_in),
            .s_in_valid             (v_s_in_valid),
            .s_in_ready             (v_s_in_ready),
            .s_wtarget              (exe_stage_op.fps2),
            .result_waddr           (exe_stage_op.addr_2),
            .result_waddr_update    (exe_stage_op.update_v_waddr),
            .v_out                  (v_out_fp),
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
            .FP_MEM_INIT_FILE(FP_MEM_INIT_FILE),
            .FIXED_MEM_INIT_FILE(FIXED_MEM_INIT_FILE)
        ) scalar_machine_init (
            .clk(clk),
            .rst(rst),
            .exe_stage_op           (exe_stage_op),
            .assigned_fixed_op      (exe_fixed_op),
            .rs1                    (s_rs1),
            .rs2                    (s_rs2),
            .rd                     (s_rd),
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

    // Matrix SRAM 
    matrix_sram_with_rounding #(
        .MXFP_EXP_WIDTH     (LOW_MXFP_EXP_WIDTH),
        .MXFP_MANT_WIDTH    (LOW_MXFP_MANT_WIDTH),
        .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH),
        .MLEN               (MLEN),
        .BLOCK_DIM          (BLOCK_DIM),
        .SRAM_DEPTH         (MATRIX_SRAM_DEPTH),
        .PARALLEL_DIM       (Matrix_Parallel_Rd_Dim),
        .PREFETCH_AMOUNT    (HBM_M_Prefetch_Amount)
    ) matrix_sram (
        .clk(clk),
        .rst(rst),
        .req                (m_sram_req),
        .transposed_read    (m_sram_transposed_read),
        .sram_raddr         (m_sram_raddr),
        .element_out        (fetched_m_element),
        .scale_out          (fetched_m_scale),
        .wen                (m_sram_wen),
        .sram_waddr         (m_sram_waddr),
        .element_in         (prefetch_m_element),
        .scale_in           (prefetch_m_scale),
        .prefetch_addr      (exe_stage_op.addr_2),
        .prefetch_en        (exe_stage_op.h_op == PREFETCH_M),
        .data_not_ready     (m_prefetch_data_not_ready)
    );

    // Vector SRAM
    fp_vector_sram #(
        .MXFP_EXP_WIDTH     (HIGH_MXFP_EXP_WIDTH),
        .MXFP_MANT_WIDTH    (HIGH_MXFP_MANT_WIDTH),
        .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH),
        .EXP_WIDTH          (V_FP_EXP_WIDTH),
        .MANT_WIDTH         (V_FP_MANT_WIDTH),
        .VLEN               (VLEN),
        .MLEN               (MLEN),
        .BLOCK_DIM          (BLOCK_DIM),
        .SRAM_DEPTH         (SCRATCHPAD_SRAM_DEPTH),
        .ON_CHIP_ADDR_WIDTH (ON_CHIP_ADDR_WIDTH),
        .PREFETCH_AMOUNT    (HBM_V_Prefetch_Amount),
        .MEM_RESULT_FILE    (V_SRAM_RESULT_FILE)
    ) vector_sram (
        .clk(clk),
        .rst(rst),
        .control(select_write_data_a),
        .port_a_req         (v_sram_req_a),
        .port_a_write_en    (v_sram_wen_a),
        .port_a_addr        (v_sram_addr_a),
        .port_a_m_fp_in     (m_out_v_fp),
        .port_a_v_fp_in     (v_out_fp),
        .port_a_mask_in     (v_sram_mask_a),
        .port_a_v_fp_out    (v_port_a_out_fp),
        .port_a_element_out (v_element_port_a_out),
        .port_a_scale_out   (v_scale_port_a_out),
        .port_b_req         (v_sram_req_b),
        .port_b_write_en    (v_sram_wen_b),
        .port_b_addr        (v_sram_addr_b),
        .port_b_fp_out      (v_port_b_out_fp),
        .port_b_mask_in     (v_sram_mask_b),
        .port_b_element_in  (v_element_port_b_in),
        .port_b_scale_in    (v_scale_port_b_in),
        .port_b_mxfp_req    (v_sram_mxfp_req_b),
        .port_b_element_out (v_element_port_b_out),
        .port_b_scale_out   (v_scale_port_b_out),
        .port_b_mxfp_out_valid(port_b_mxfp_out_valid),
        .prefetch_en        (exe_stage_op.h_op == PREFETCH_V),
        .prefetch_addr      (exe_stage_op.addr_2),
        .data_not_ready     (v_prefetch_data_not_ready)
    );

    // -----------------------------
    // HBM Control & Interface
    // -----------------------------
    
    // TL Declaration
    `TL_DECLARE(HBM_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, m_element);
    `TL_BIND_HOST_PORT(m_out_element, m_element);
    `TL_DECLARE(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, m_scale);
    `TL_BIND_HOST_PORT(m_out_scale, m_scale);

    `TL_DECLARE(HBM_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, v_element);
    `TL_BIND_HOST_PORT(v_out_element, v_element);
    `TL_DECLARE(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, v_scale);
    `TL_BIND_HOST_PORT(v_out_scale, v_scale);

    hbm_sys #(
    ) hbm_interface_init (
        .clk(clk),
        .rst(rst),
        .exe_stage_op           (exe_stage_op),
        .prefetch_m_ready       (hbm_m_req_prefetch_data),
        .prefetch_m_valid       (hbm_m_prefetch_valid),
        .prefetch_m_element     (prefetch_m_element),
        .prefetch_m_scale       (prefetch_m_scale),
        .prefetch_v_ready       (hbm_v_req_prefetch_data),
        .prefetch_v_valid       (hbm_v_prefetch_valid),
        .prefetch_v_element     (v_element_port_b_in),
        .prefetch_v_scale       (v_scale_port_b_in),
        .hbm_write_v_en         (port_b_mxfp_out_valid),
        .hbm_write_v_ready      (hbm_ready_to_write),
        .hbm_write_v_element    (v_element_port_b_out),
        .hbm_write_v_scale      (v_scale_port_b_out),
        .prefetch_m_in_progress (hbm_m_prefetch_in_progress),
        .prefetch_v_in_progress (hbm_v_prefetch_in_progress),
        `TL_CONNECT_HOST_PORT   (host_m_element, m_element),
        `TL_CONNECT_HOST_PORT   (host_m_scale, m_scale),
        `TL_CONNECT_HOST_PORT   (host_v_element, v_element),
        `TL_CONNECT_HOST_PORT   (host_v_scale, v_scale)
    );

endmodule