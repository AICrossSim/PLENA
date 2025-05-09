`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : HBM Arbiter
Timing      : Combinatorial
Description : This module is used to schedule the data prefetched from HBM to Matrix SRAM and Scratchpad SRAM.
            : It also shdules the write process from the two SRAMs to HBM.
            ： When the prefetch data is ready, it will outputs to the pipeline control to decide when to pass the data to the sram.
Status      : Under Development
*/

module hbm_arbiter #(
    parameter   MXFP_EXP_WIDTH      = 4,
    parameter   MXFP_MANT_WIDTH     = 3,
    parameter   MXFP_SCALE_WIDTH    = 8,
    parameter   BLOCK_DIM           = 4,
    parameter   ADDR_WIDTH          = 32,
    parameter   MLEN                = 8,
    parameter   VLEN                = 8,
    parameter   Parallel_Rd_Dim     = 4,
    parameter   HBM_ADDR_WIDTH      = 64,

    localparam int M_BLOCK_NUM      = MLEN / BLOCK_DIM,
    localparam int V_BLOCK_NUM      = VLEN / BLOCK_DIM,
    localparam int HBM_ELE_WIDTH    = MLEN * MLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1),
    localparam int HBM_SCALE_WIDTH  = MLEN * M_BLOCK_NUM * MXFP_SCALE_WIDTH,
    localparam int ELE_WIDTH        = Parallel_Rd_Dim * MLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1),
    localparam int SCALE_WIDTH      = Parallel_Rd_Dim * M_BLOCK_NUM * MXFP_SCALE_WIDTH,
    localparam int V_ELE_WIDTH      = VLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1),
    localparam int V_SCALE_WIDTH    = V_BLOCK_NUM * MXFP_SCALE_WIDTH

)(
    input logic clk,
    input logic rst,

    // HBM 
    input   logic   [HBM_ELE_WIDTH - 1 : 0]         prefetch_element,
    input   logic   [HBM_SCALE_WIDTH - 1 : 0]       prefetch_scale,
    input   logic                                   prefetch_data_valid,
    output  logic                                   hbm_prefetch_en,
    input   logic   [ADDR_WIDTH - 1 : 0]            target_addr,

    input   logic   [HBM_ADDR_WIDTH - 1 : 0]        addr_to_prefetch,
    input   logic   [HBM_ADDR_WIDTH - 1 : 0]        addr_for_prefetched_data,

    output   logic                                  hbm_write_en,
    input    logic                                  hbm_write_ready,
    output   logic                                  hbm_write_valid,
    output   logic   [ELE_WIDTH - 1 : 0]            hbm_write_element,
    output   logic   [SCALE_WIDTH - 1 : 0]          hbm_write_scale,

    // Matrix SRAM
    input    logic                                  prefetch_m_ready,
    output   logic   [ELE_WIDTH - 1 : 0]            prefetch_m_element,
    output   logic   [SCALE_WIDTH - 1 : 0]          prefetch_m_scale,


    // Scratchpad SRAM
    input    logic                                  prefetch_v_ready,
    output   logic   [V_ELE_WIDTH- 1 : 0]           prefetch_v_element,
    output   logic   [V_SCALE_WIDTH- 1 : 0]         prefetch_v_scale,

    input    logic   [ELE_WIDTH - 1 : 0]            v_out_element,
    input    logic   [SCALE_WIDTH - 1 : 0]          v_out_scale,
    input    logic                                  v_out_data_wen,

    // Control signals
    input    H_OP                                   h_op, 
    output   logic                                  hbm_m_prefetch_complete, // For matrix prefetch, indicates that this data is already fetched from HBM and can be extracted directly.
    output   logic                                  hbm_v_prefetch_complete  // For vector prefetch, indicates that this data is already fetched from HBM and can be extracted directly.
);

// Matrix SRAM, as the load data dimension matches the HBM data dimension, just need to assign the data directly. We also don't need to read from Matrix SRAM for HBM write.
// Scratchpad SRAM, Distributer is required.

typedef enum logic [1:0] {
    IDLE            = 2'b00, 
    HBM_PREFETCH_M  = 2'b01, 
    HBM_PREFETCH_V  = 2'b10, 
    HBM_STORE_V     = 2'b11
} HBM_STATE;

HBM_STATE hbm_state, next_hbm_state;

logic [MLEN - 1 : 0] [V_ELE_WIDTH - 1 : 0]       hbm_v_element;
logic [MLEN - 1 : 0] [V_SCALE_WIDTH - 1 : 0]     hbm_v_scale;
logic [MLEN - 1 : 0] [HBM_ADDR_WIDTH - 1 : 0]    hbm_v_addr_tag;

logic [MATRIX_READ_ITERATIONS - 1 : 0][ELE_WIDTH - 1 : 0]       hbm_m_element;
logic [MATRIX_READ_ITERATIONS - 1 : 0][SCALE_WIDTH - 1 : 0]     hbm_m_scale;

logic [MATRIX_READ_ITERATIONS - 1 : 0] [HBM_ADDR_WIDTH - 1 : 0]  hbm_m_addr_tag;

// Storting the prefetch data
always_ff @(posedge clk or posedge rst) begin
    if (rst) begin
        hbm_state <= IDLE;
    end else begin
        hbm_state <= next_hbm_state;
        if (prefetch_data_valid) begin
            if (hbm_state == HBM_PREFETCH_V) begin
                hbm_v_element <= prefetch_element;
                hbm_v_scale   <= prefetch_scale;
                for (int i = 0; i < MLEN; i++) begin
                    hbm_v_addr_tag[i] <= addr_for_prefetched_data + i * (MLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) / 8);
                end
            end else if (hbm_state == HBM_PREFETCH_M) begin
                hbm_m_element   <= prefetch_element;
                hbm_m_scale     <= prefetch_scale;
                for (int i = 0; i < MATRIX_READ_ITERATIONS; i++) begin
                    hbm_m_addr_tag[i] <= addr_for_prefetched_data + i * (Parallel_Rd_Dim * MLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) / 8);
                end
            end
        end 
    end
end

logic [ADDR_WIDTH - 1 : 0]          recorded_prefetch_waddr;
logic [HBM_ADDR_WIDTH - 1 : 0]      recorded_hbm_prefetch_addr;
logic [MLEN - 1 : 0]     matched_v_tag;
localparam MATRIX_READ_ITERATIONS = MLEN / BLOCK_DIM;
logic [MATRIX_READ_ITERATIONS - 1 : 0] matched_m_tag;

logic [V_ELE_WIDTH- 1 : 0]          matched_v_element;
logic [V_SCALE_WIDTH- 1 : 0]        matched_v_scale;

logic [ELE_WIDTH - 1 : 0]            matched_m_element;
logic [SCALE_WIDTH - 1 : 0]          matched_m_scale;

always_comb  begin
    case (hbm_state)
        IDLE: begin
            if (h_op == PREFETCH_M) begin
                next_hbm_state = HBM_PREFETCH_M;
                recorded_prefetch_waddr = target_addr;
                hbm_prefetch_en = 1'b1;
            end else if (h_op == PREFETCH_V) begin
                next_hbm_state = HBM_PREFETCH_V;
                recorded_prefetch_waddr = target_addr;
                hbm_prefetch_en = 1'b1;
            end else if (h_op == STORE_V) begin
                next_hbm_state = HBM_STORE_V;
                hbm_prefetch_en = 1'b0;
                recorded_prefetch_waddr = target_addr;
            end else begin
                next_hbm_state = IDLE;
                hbm_prefetch_en = 1'b0;
            end
            hbm_write_en = 1'b0;
        end

        HBM_PREFETCH_M: begin
            hbm_prefetch_en = 1'b0;
            if (prefetch_m_ready & hbm_m_prefetch_complete) begin
                next_hbm_state = IDLE;
                prefetch_m_element = matched_m_element;
                prefetch_m_scale   = matched_m_scale;
            end else begin
                next_hbm_state = HBM_PREFETCH_M;
                recorded_hbm_prefetch_addr = addr_to_prefetch;
            end
        end

        HBM_PREFETCH_V: begin
            hbm_prefetch_en = 1'b0;
            if (prefetch_v_ready & hbm_v_prefetch_complete) begin
                next_hbm_state = HBM_STORE_V;
                prefetch_v_element = matched_v_element;
                prefetch_v_scale   = matched_v_scale;
            end else begin
                next_hbm_state = HBM_PREFETCH_V;
            end
        end

        HBM_STORE_V: begin
            if (v_out_data_wen & hbm_write_ready) begin
                next_hbm_state = IDLE;
                hbm_write_en = 1'b1;
                hbm_write_element   = v_out_element;
                hbm_write_scale     = v_out_scale;
                hbm_write_valid     = 1'b1;
            end else begin
                next_hbm_state = HBM_STORE_V;
                hbm_write_en = 1'b0;
            end
        end

        default: next_hbm_state = IDLE;
        
    endcase
    // Check if the prefetch data is ready.
    if (hbm_state == HBM_PREFETCH_V) begin
        for (int i = 0; i < MLEN; i++) begin
            if (hbm_v_addr_tag[i] == recorded_hbm_prefetch_addr) begin
                matched_v_tag[i]      = 1'b1;
                matched_v_element   = hbm_v_element[i];
                matched_v_scale     = hbm_v_scale[i];
            end 
            else begin
                matched_v_tag[i] = 1'b0;
            end
        end
        hbm_v_prefetch_complete = |matched_v_tag;
    end else if (hbm_state == HBM_PREFETCH_M) begin
        for (int i = 0; i < MATRIX_READ_ITERATIONS; i++) begin
            if (hbm_m_addr_tag[i] == recorded_hbm_prefetch_addr) begin
                matched_m_tag[i]      = 1'b1;
                matched_m_element   = hbm_m_element[i];
                matched_m_scale     = hbm_m_scale[i];
            end 
            else begin
                matched_m_tag[i] = 1'b0;
            end
        end
        hbm_m_prefetch_complete = |matched_m_tag;
    end else begin
        hbm_v_prefetch_complete = 1'b0;
        hbm_m_prefetch_complete = 1'b0;
    end
end

endmodule