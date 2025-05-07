`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : HBM Arbiter
Timing      : Combinatorial
Description : This module is used to schedule the data prefetched from HBM to Matrix SRAM and Scratchpad SRAM.
            : It also shdules the write process from the two SRAMs to HBM.
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
    localparam int ELE_WIDTH        = Parallel_Rd_Dim * MLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1),
    localparam int SCALE_WIDTH      = Parallel_Rd_Dim * M_BLOCK_NUM * MXFP_SCALE_WIDTH,
    localparam int V_ELE_WIDTH      = VLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1),
    localparam int V_SCALE_WIDTH    = V_BLOCK_NUM * MXFP_SCALE_WIDTH

)(
    input logic clk,
    input logic rst,

    // HBM 
    input   logic   [ELE_WIDTH - 1 : 0]             prefetch_element,
    input   logic   [SCALE_WIDTH - 1 : 0]           prefetch_scale,
    input   logic                                   prefetch_data_valid,
    output  logic                                   hbm_prefetch_en,
    input   logic   [ADDR_WIDTH - 1 : 0]            target_addr,

    input   logic   [HBM_ADDR_WIDTH - 1 : 0]        prefetch_hbm_raddr,

    output   logic                                  hbm_write_en,
    input    logic                                  hbm_write_ready,
    output   logic                                  hbm_write_valid,
    output   logic   [ELE_WIDTH - 1 : 0]            hbm_write_element,
    output   logic   [SCALE_WIDTH - 1 : 0]          hbm_write_scale,

    // Matrix SRAM
    input    logic                                  prefetch_m_ready,
    output   logic   [ELE_WIDTH - 1 : 0]            prefetch_m_element,
    output   logic   [SCALE_WIDTH - 1 : 0]          prefetch_m_scale,
    output   logic                                  prefetch_m_data_valid,


    // Scratchpad SRAM
    input    logic                                  prefetch_v_ready,
    output   logic   [V_ELE_WIDTH- 1 : 0]           prefetch_v_element,
    output   logic   [V_SCALE_WIDTH- 1 : 0]         prefetch_v_scale,
    output   logic                                  prefetch_v_data_valid,

    input    logic   [ELE_WIDTH - 1 : 0]            v_out_element,
    input    logic   [SCALE_WIDTH - 1 : 0]          v_out_scale,
    input    logic                                  v_out_data_wen,

    // Control signals
    input    H_OP                                   h_op, 
    output   logic                                  prefetch_content_ready  // For vector prefetch, indicates that this data is already fetched from HBM and can be extracted directly.
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

logic [Parallel_Rd_Dim - 1 : 0] [V_ELE_WIDTH - 1 : 0]       hbm_v_element;
logic [Parallel_Rd_Dim - 1 : 0] [V_SCALE_WIDTH - 1 : 0]     hbm_v_scale;
logic [Parallel_Rd_Dim - 1 : 0] [HBM_ADDR_WIDTH - 1 : 0]    hbm_v_addr_tag;

logic [ELE_WIDTH - 1 : 0]       hbm_m_element;
logic [SCALE_WIDTH - 1 : 0]     hbm_m_scale;
logic [HBM_ADDR_WIDTH - 1 : 0]  hbm_m_addr_tag;


always_ff @(posedge clk or posedge rst) begin
    if (rst) begin
        hbm_state <= IDLE;
    end else begin
        hbm_state <= next_hbm_state;
        if (prefetch_data_valid) begin
            if (hbm_state == HBM_PREFETCH_V) begin
                hbm_v_element <= prefetch_element;
                hbm_v_scale   <= prefetch_scale;
                for (int i = 0; i < Parallel_Rd_Dim; i++) begin
                    hbm_v_addr_tag[i] <= prefetch_hbm_raddr + i * (VLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) / 8);
                end
            end else if (hbm_state == HBM_PREFETCH_M) begin
                hbm_m_element <= prefetch_element;
                hbm_m_scale   <= prefetch_scale;
                hbm_m_addr_tag <= prefetch_hbm_raddr;
            end
        end 
    end
end

logic [ADDR_WIDTH - 1 : 0]          recorded_prefetch_waddr;
logic [Parallel_Rd_Dim - 1 : 0]     matched_tag;
logic [V_ELE_WIDTH- 1 : 0]          matched_v_element;
logic [V_SCALE_WIDTH- 1 : 0]        matched_v_scale;

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
            prefetch_m_data_valid = 1'b0;
            prefetch_v_data_valid = 1'b0;
        end

        HBM_PREFETCH_M: begin
            if (prefetch_m_ready) begin
                next_hbm_state = IDLE;
                prefetch_m_element = hbm_m_element;
                prefetch_m_scale   = hbm_m_scale;
                prefetch_m_data_valid = 1'b1;
            end else begin
                next_hbm_state = HBM_PREFETCH_M;
                prefetch_m_data_valid = 1'b0;
            end
        end

        HBM_PREFETCH_V: begin
            if (prefetch_v_ready) begin
                next_hbm_state = HBM_STORE_V;
                prefetch_v_element = matched_v_element;
                prefetch_v_scale   = matched_v_scale;
                prefetch_v_data_valid = 1'b1;
            end else begin
                next_hbm_state = HBM_PREFETCH_V;
                prefetch_v_data_valid = 1'b0;
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
        for (int i = 0; i < Parallel_Rd_Dim; i++) begin
            if (hbm_v_addr_tag[i] == recorded_prefetch_waddr) begin
                matched_tag[i] = 1'b1;
                matched_v_element[i] = hbm_v_element[i];
                matched_v_scale[i] = hbm_v_scale[i];
            end 
            else begin
                matched_tag[i] = 1'b0;
            end
        end
        prefetch_content_ready = &matched_tag;
    end else if (hbm_state == HBM_PREFETCH_M) begin
        prefetch_content_ready = (hbm_m_addr_tag == recorded_prefetch_waddr);
    end
end

endmodule