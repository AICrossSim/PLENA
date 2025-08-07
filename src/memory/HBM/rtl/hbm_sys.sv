`timescale 1ns / 1ps
`include "tl_util.svh"
`include "tl_pkg.svh"
`include "configuration.svh"
`include "operation.svh"

/*
Module      : HBM System
Description : 
            : This module is the top level HBM system .
            : It contains the HBM controller, HBM arbiter, and the HBM interface.
            : It controls the read and write process from the HBM, and control the data distribution to matrix SRAM and vector SRAM.
            : It should suppot prefetching data from HBM for the two ports at the same time so that we could drain the HBM bandwidth.
*/

module hbm_sys import precision_pkg::*; import configuration_pkg::*; #(
    `ifdef SIMULATION
        parameter string MemAddrInitFile = "",
        parameter string MemStrideInitFile = "",
    `endif
    localparam int V_BLOCKNUM       = VLEN / BLOCK_DIM,
    localparam int M_BLOCKNUM       = MLEN / BLOCK_DIM
) (
    input   logic clk,
    input   logic rst,

    // Control
    input   OP_BUNDLE exe_stage_op,

    // Data to Matrix SRAM
    input   logic prefetch_m_ready,
    output  logic prefetch_m_valid,
    output  logic [MLEN -1:0] [WT_MX_MANT_WIDTH + WT_MX_EXP_WIDTH:0]                prefetch_m_element,
    output  logic [M_BLOCKNUM -1:0] [MXFP_SCALE_WIDTH-1:0]                          prefetch_m_scale,

    // Data to Vector SRAM
    input   logic prefetch_v_ready,
    output  logic prefetch_v_valid,
    output  logic [VLEN-1:0] [ACT_MXFP_MANT_WIDTH + ACT_MXFP_EXP_WIDTH:0]               prefetch_v_high_precision_element,
    output  logic [VLEN-1:0] [KV_MX_MANT_WIDTH  + KV_MX_EXP_WIDTH:0]                    prefetch_v_low_precision_element,
    output  logic [V_BLOCKNUM-1:0] [MXFP_SCALE_WIDTH-1:0]                               prefetch_v_scale,

    // Write Back to HBM
    input   logic                                 hbm_write_high_valid,
    input   logic                                 hbm_write_low_valid,
    output  logic                                 hbm_write_ready,

    input   logic   [VLEN-1:0] [WT_MX_MANT_WIDTH + WT_MX_EXP_WIDTH:0]               hbm_write_high_element,
    input   logic   [VLEN-1:0] [KV_MX_MANT_WIDTH + KV_MX_EXP_WIDTH:0]               hbm_write_low_element,
    input   logic   [V_BLOCKNUM-1:0] [MXFP_SCALE_WIDTH-1:0]                         hbm_write_scale,

    // Status Tracking
    output logic prefetch_m_in_progress,
    output logic prefetch_v_in_progress,

    // Matrix SRAM TL Interface
    `TL_DECLARE_HOST_PORT(HBM_ELE_WIDTH,   HBM_ADDR_WIDTH, SourceWidth, SinkWidth, host_m_element),
    `TL_DECLARE_HOST_PORT(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, host_m_scale),
    // Vector SRAM TL Interface
    `TL_DECLARE_HOST_PORT(HBM_ELE_WIDTH,   HBM_ADDR_WIDTH, SourceWidth, SinkWidth, host_v_element),
    `TL_DECLARE_HOST_PORT(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth, host_v_scale)
);

    // -----------------------------
    // Declarations
    // -----------------------------
    `TL_DECLARE(HBM_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth,  m_tl_element);
    `TL_DECLARE(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth,m_tl_scale);
    `TL_BIND_HOST_PORT(host_m_element, m_tl_element);
    `TL_BIND_HOST_PORT(host_m_scale, m_tl_scale);
    `TL_DECLARE(HBM_ELE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth,  v_tl_element);
    `TL_DECLARE(HBM_SCALE_WIDTH, HBM_ADDR_WIDTH, SourceWidth, SinkWidth,v_tl_scale);
    `TL_BIND_HOST_PORT(host_v_element, v_tl_element);
    `TL_BIND_HOST_PORT(host_v_scale, v_tl_scale);

    logic v_hbm_prefetch_en, m_hbm_prefetch_en;
    logic v_stride_mode_en, m_stride_mode_en;
    logic v_controller_precision_select, m_controller_precision_select; // 0: High Precision, 1: Low Precision
    logic hbm_write_high_ready, hbm_write_low_ready;

    logic m_hbm_prefetch_valid;
    logic prefetch_m_element_ready, prefetch_m_scale_ready;
    logic stored_prefetch_m_element_ready, stored_prefetch_m_element_valid;
    logic stored_prefetch_m_scale_valid, stored_prefetch_m_scale_ready;

    logic v_hbm_prefetch_valid;
    logic prefetch_v_element_ready, prefetch_v_scale_ready;
    logic stored_prefetch_v_element_ready, stored_prefetch_v_element_valid;
    logic stored_prefetch_v_scale_valid, stored_prefetch_v_scale_ready;
    logic v_hbm_high_precision_element_out_valid, v_hbm_low_precision_element_out_valid;
    logic v_hbm_high_precision_element_out_ready, v_hbm_low_precision_element_out_ready;
    logic stored_prefetch_high_precision_v_element_ready, stored_prefetch_high_precision_v_element_valid;
    logic stored_prefetch_low_precision_v_element_ready, stored_prefetch_low_precision_v_element_valid;

    logic [HBM_ADDR_WIDTH - 1 : 0] hbm_addr_out, recorded_hbm_waddr_out;
    logic [MLEN * (WT_MX_EXP_WIDTH + WT_MX_MANT_WIDTH + 1) - 1 : 0]     m_hbm_high_precision_element_out;
    logic [MLEN * (WT_MX_EXP_WIDTH + WT_MX_MANT_WIDTH + 1) - 1 : 0]     m_hbm_element_out;
    logic [MLEN - 1 : 0] [KV_MX_EXP_WIDTH + KV_MX_MANT_WIDTH : 0]       m_hbm_low_precision_element_out;
    logic [MLEN - 1 : 0] [WT_MX_EXP_WIDTH + WT_MX_MANT_WIDTH : 0]       m_hbm_upcasted_element_out;
    logic [M_BLOCKNUM * MXFP_SCALE_WIDTH - 1 : 0] m_hbm_scale_out;

    logic [ON_CHIP_ADDR_WIDTH - 1 : 0] stride_size, stored_m_scale_offset, stored_v_scale_offset;
    logic [VLEN * (ACT_MXFP_EXP_WIDTH + ACT_MXFP_MANT_WIDTH + 1) - 1 : 0]   v_hbm_high_precision_element_out;
    logic [VLEN * (KV_MX_EXP_WIDTH + KV_MX_MANT_WIDTH + 1) - 1 : 0]     v_hbm_low_precision_element_out;
    logic [V_BLOCKNUM * MXFP_SCALE_WIDTH - 1 : 0] v_hbm_scale_out;

    logic [MLEN -1:0] [WT_MX_MANT_WIDTH + WT_MX_EXP_WIDTH:0]                stored_prefetch_m_element;
    logic [M_BLOCKNUM -1:0] [MXFP_SCALE_WIDTH-1:0]                          stored_prefetch_m_scale;
    logic [VLEN-1:0] [ACT_MXFP_MANT_WIDTH + ACT_MXFP_EXP_WIDTH:0]           stored_prefetch_high_precision_v_element;   
    logic [VLEN-1:0] [KV_MX_MANT_WIDTH  + KV_MX_EXP_WIDTH:0]                stored_prefetch_low_precision_v_element;
    logic [V_BLOCKNUM-1:0] [MXFP_SCALE_WIDTH-1:0]                           stored_prefetch_v_scale; 

    OP_BUNDLE mem_stage_op;


    // -----------------------------
    // HBM System Output Handling
    // -----------------------------
    always_ff @(posedge clk) begin
        if (rst) begin
            prefetch_m_element <= 'b0;
            prefetch_m_scale <= 'b0;
            prefetch_v_high_precision_element <= 'b0;
            prefetch_v_low_precision_element <= 'b0;
            prefetch_v_scale <= 'b0;
        end else begin
            prefetch_m_element                  <= stored_prefetch_m_element;
            prefetch_m_scale                    <= stored_prefetch_m_scale;
            prefetch_v_high_precision_element   <= stored_prefetch_high_precision_v_element;
            prefetch_v_low_precision_element    <= stored_prefetch_low_precision_v_element;
            prefetch_v_scale                    <= stored_prefetch_v_scale;
        end
    end


    // -----------------------------
    // HBM System Control
    // -----------------------------

    assign hbm_write_ready = hbm_write_high_ready & hbm_write_low_ready;

    // One clk delayed for address mapping
    always_ff @(posedge clk) begin
        mem_stage_op <= exe_stage_op;
        if (rst) begin
            v_hbm_prefetch_en <= 1'b0;
            m_hbm_prefetch_en <= 1'b0;
            m_controller_precision_select <= 1'b0;
            v_controller_precision_select <= 1'b0;
            m_stride_mode_en <= 1'b0;
            v_stride_mode_en <= 1'b0;
        end else begin
            case (mem_stage_op.h_op)
                PREFETCH_V_H: begin
                    v_hbm_prefetch_en <= 1'b1;
                    m_hbm_prefetch_en <= 1'b0;
                    m_controller_precision_select   <= m_controller_precision_select;
                    v_controller_precision_select   <= 1'b0;
                end                 
                PREFETCH_V_L: begin
                    v_hbm_prefetch_en <= 1'b1;
                    m_hbm_prefetch_en <= 1'b0;
                    m_controller_precision_select   <= m_controller_precision_select;
                    v_controller_precision_select   <= 1'b1;
                end
                PREFETCH_M_H: begin
                    m_hbm_prefetch_en <= 1'b1;
                    v_hbm_prefetch_en <= 1'b0;
                    m_controller_precision_select   <= 1'b0;
                    v_controller_precision_select   <= v_controller_precision_select;
                end
                PREFETCH_M_L: begin
                    m_hbm_prefetch_en <= 1'b1;
                    v_hbm_prefetch_en <= 1'b0;
                    m_controller_precision_select   <= 1'b1;
                    v_controller_precision_select   <= v_controller_precision_select;
                end
                STORE_V_H: begin
                    v_hbm_prefetch_en   <= 1'b0;
                    m_hbm_prefetch_en   <= 1'b0;
                    v_controller_precision_select   <= 1'b0;
                end
                STORE_V_L: begin
                    v_hbm_prefetch_en   <= 1'b0;
                    m_hbm_prefetch_en   <= 1'b0;
                    m_controller_precision_select   <= m_controller_precision_select;
                    v_controller_precision_select   <= 1'b1;
                end
                default: begin
                    v_hbm_prefetch_en <= 1'b0;
                    m_hbm_prefetch_en <= 1'b0;
                    m_controller_precision_select   <= m_controller_precision_select;
                    v_controller_precision_select   <= v_controller_precision_select;
                end
            endcase
        end
    end

    // -----------------------------
    // HBM Status Tracking
    // -----------------------------

    always_ff @(posedge clk) begin
        if (rst) begin
            prefetch_m_in_progress <= 1'b0;
            prefetch_v_in_progress <= 1'b0;
        end else begin
            if (mem_stage_op.h_op == PREFETCH_V_H || mem_stage_op.h_op == PREFETCH_V_L) begin
                prefetch_v_in_progress <= 1'b1;
            end else if (prefetch_v_valid && prefetch_v_ready) begin
                prefetch_v_in_progress <= 1'b0;
            end
            if (mem_stage_op.h_op == PREFETCH_M_H || mem_stage_op.h_op == PREFETCH_M_L) begin
                prefetch_m_in_progress <= 1'b1;
            end else if (prefetch_m_valid && prefetch_m_ready) begin
                prefetch_m_in_progress <= 1'b0;
            end
        end
    end

    // -----------------------------
    // HBM Address Mapping
    // -----------------------------

    address_mapper #(
        .ADDR_WIDTH             (ON_CHIP_ADDR_WIDTH),
        .HBM_ADR_OPERAND_WIDTH  (HBM_ADR_OPERAND_WIDTH),
        .HBM_ADDR_WIDTH         (HBM_ADDR_WIDTH)
        `ifdef SIMULATION
        , .MemInitFile          (MemAddrInitFile)
        `endif
    ) address_mapper_inst (
        .clk(clk),
        .rst(rst),
        .mapp_addr_en   (mem_stage_op.h_op != STALL_H),
        .set_addr_en    (mem_stage_op.c_op == SET_ADDR_REG),
        .addr_in_a      (mem_stage_op.addr_1),
        .addr_in_b      (mem_stage_op.addr_2),
        .addr_offset    (mem_stage_op.addr_1),
        .read_operand   (mem_stage_op.gp_reg2[HBM_ADR_OPERAND_WIDTH - 1:0]),
        .write_operand  (mem_stage_op.gp_rd[HBM_ADR_OPERAND_WIDTH - 1:0]),
        .hbm_addr_out   (hbm_addr_out)
    );

    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            recorded_hbm_waddr_out <= {HBM_ADDR_WIDTH{1'b0}};
        end else if (mem_stage_op.h_op == STORE_V_H || mem_stage_op.h_op == STORE_V_L) begin
            recorded_hbm_waddr_out <= hbm_addr_out;
        end
    end

    // -----------------------------
    // HBM Stride Width Setting
    // -----------------------------

    always_ff @(posedge clk) begin
        if (rst) begin
            stored_m_scale_offset <= 'b0;
            stored_v_scale_offset <= 'b0;
        end else if (mem_stage_op.c_op == SET_M_SCALE_REG) begin
            stored_m_scale_offset <= mem_stage_op.addr_2;
        end else if (mem_stage_op.c_op == SET_V_SCALE_REG) begin
            stored_v_scale_offset <= mem_stage_op.addr_2;
        end
    end

    non_volatile_1p_storage #(
        .BITWIDTH (ON_CHIP_ADDR_WIDTH),
        .ADDR_WIDTH (STRIDE_OPERAND_WIDTH)
        `ifdef SIMULATION
           , .MemInitFile (MemStrideInitFile)
        `endif
    ) stride_regfile (
        .clk(clk),
        .raddr(mem_stage_op.gp_rstride[STRIDE_OPERAND_WIDTH - 1:0]),
        .rdata(stride_size)
    );


    // -----------------------------
    // HBM Prefetching for Matrix SRAM / Only supporting Read
    // -----------------------------

    double_precision_m_hbm_controller #(
        .HIGH_MXFP_EXP_WIDTH        (WT_MX_EXP_WIDTH),
        .HIGH_MXFP_MANT_WIDTH       (WT_MX_MANT_WIDTH),
        .LOW_MXFP_EXP_WIDTH         (KV_MX_EXP_WIDTH),
        .LOW_MXFP_MANT_WIDTH        (KV_MX_MANT_WIDTH),
        .MXFP_SCALE_WIDTH           (MXFP_SCALE_WIDTH),
        .BLOCK_DIM                  (BLOCK_DIM),
        .DATA_DIM                   (MLEN),
        .HBM_ADDR_WIDTH             (HBM_ADDR_WIDTH),
        .ON_CHIP_ADDR_WIDTH         (ON_CHIP_ADDR_WIDTH),
        .HBM_ELE_WIDTH              (HBM_ELE_WIDTH),
        .HBM_SCALE_WIDTH            (HBM_SCALE_WIDTH),
        .SourceWidth                (SourceWidth),
        .SinkWidth                  (SinkWidth),
        .LOAD_AMOUNT                (HBM_M_Prefetch_Amount)
    ) matrix_hbm_controller_init (
        .clk(clk),
        .rst(rst),
        .precision_select                   (m_controller_precision_select),
        .stride_offset                      (stride_size),
        .scale_offset                       (stored_m_scale_offset),
        .prefetch_high_precision_element    (m_hbm_high_precision_element_out),
        .prefetch_low_precision_element     (m_hbm_low_precision_element_out),
        .prefetch_scale                     (m_hbm_scale_out),
        .prefetch_data_valid                (m_hbm_prefetch_valid),
        .prefetch_element_data_ready        (prefetch_m_element_ready),
        .prefetch_scale_data_ready          (prefetch_m_scale_ready),
        .hbm_prefetch_en                    (m_hbm_prefetch_en),
        .hbm_raddr                          (hbm_addr_out),
        .hbm_write_en                       (hbm_write_high_valid),
        .hbm_write_ready                    (hbm_write_high_ready),
        .write_high_precision_element       (hbm_write_high_element),
        .write_low_precision_element        (hbm_write_low_element),
        .write_scale                        (hbm_write_scale),
        .hbm_waddr                          (recorded_hbm_waddr_out),
        `TL_CONNECT_HOST_PORT(host_element, m_tl_element),
        `TL_CONNECT_HOST_PORT(host_scale, m_tl_scale)
    );

    // Upcast low precision MXFP to high_precision
    generate;
        for (genvar i = 0; i < MLEN; i++) begin : upcast_loaded_low_precision_mxfp
            fp_dequantizer #(
                .IN_EXP_WIDTH   (KV_MX_EXP_WIDTH),
                .IN_MANT_WIDTH  (KV_MX_MANT_WIDTH),
                .OUT_EXP_WIDTH  (WT_MX_EXP_WIDTH),
                .OUT_MANT_WIDTH (WT_MX_MANT_WIDTH)
            ) upcast_mxfp_inst (
                .in_fp    (m_hbm_low_precision_element_out[i]),
                .out_fp   (m_hbm_upcasted_element_out[i])
            );
        end
    endgenerate

    assign m_hbm_element_out = (m_controller_precision_select == 1'b0) ? m_hbm_high_precision_element_out : m_hbm_upcasted_element_out;

    register_slice #(
        .DATA_WIDTH(MLEN * (WT_MX_EXP_WIDTH + WT_MX_MANT_WIDTH + 1))
    ) matrix_sram_high_precision_prefetch_buffer (
        .clk(clk),
        .rst(rst),
        .data_in            (m_hbm_element_out),
        .data_in_valid      (m_hbm_prefetch_valid),
        .data_in_ready      (prefetch_m_element_ready),
        .data_out           (stored_prefetch_m_element),
        .data_out_valid     (stored_prefetch_m_element_valid),
        .data_out_ready     (stored_prefetch_m_element_ready)
    );

    register_slice #(
        .DATA_WIDTH(M_BLOCKNUM * MXFP_SCALE_WIDTH)
    ) matrix_sram_prefetch_scale_buffer (
        .clk(clk),
        .rst(rst),
        .data_in            (m_hbm_scale_out),
        .data_in_valid      (m_hbm_prefetch_valid),
        .data_in_ready      (prefetch_m_scale_ready),
        .data_out           (stored_prefetch_m_scale),
        .data_out_valid     (stored_prefetch_m_scale_valid),
        .data_out_ready     (stored_prefetch_m_scale_ready)
    );

    join2 #(
    ) join_matrix_prefetch (
        .data_in_ready({stored_prefetch_m_element_ready, stored_prefetch_m_scale_ready}),
        .data_in_valid({stored_prefetch_m_element_valid, stored_prefetch_m_scale_valid}),
        .data_out_valid(prefetch_m_valid),
        .data_out_ready(prefetch_m_ready)
    );


    // -----------------------------
    // HBM Prefetching for Vector SRAM
    // -----------------------------

    double_precision_v_hbm_controller #(
        .HIGH_MXFP_EXP_WIDTH        (ACT_MXFP_EXP_WIDTH),
        .HIGH_MXFP_MANT_WIDTH       (ACT_MXFP_MANT_WIDTH),
        .LOW_MXFP_EXP_WIDTH         (KV_MX_EXP_WIDTH),
        .LOW_MXFP_MANT_WIDTH        (KV_MX_MANT_WIDTH),
        .MXFP_SCALE_WIDTH           (MXFP_SCALE_WIDTH),
        .BLOCK_DIM                  (BLOCK_DIM),
        .DATA_DIM                   (VLEN),
        .HBM_ADDR_WIDTH             (HBM_ADDR_WIDTH),
        .ON_CHIP_ADDR_WIDTH         (ON_CHIP_ADDR_WIDTH),
        .HBM_ELE_WIDTH              (HBM_ELE_WIDTH),
        .HBM_SCALE_WIDTH            (HBM_SCALE_WIDTH),
        .SourceWidth                (SourceWidth),
        .SinkWidth                  (SinkWidth),
        .LOAD_AMOUNT                (HBM_V_Prefetch_Amount),
        .WRITE_AMOUNT               (HBM_V_Writeback_Amount)
    ) vector_hbm_controller_init (
        .clk(clk),
        .rst(rst),
        .precision_select                   (v_controller_precision_select),
        .stride_offset                      (stride_size),
        .scale_offset                       (stored_v_scale_offset),
        .prefetch_high_precision_element    (stored_prefetch_high_precision_v_element),
        .prefetch_low_precision_element     (stored_prefetch_low_precision_v_element),
        .prefetch_scale                     (stored_prefetch_v_scale),
        .prefetch_data_valid                (prefetch_v_valid),
        .prefetch_data_ready                (prefetch_v_ready),
        .hbm_prefetch_en                    (v_hbm_prefetch_en),
        .hbm_raddr                          (hbm_addr_out),
        `TL_CONNECT_HOST_PORT(host_element, v_tl_element),
        `TL_CONNECT_HOST_PORT(host_scale,   v_tl_scale)
    );


endmodule