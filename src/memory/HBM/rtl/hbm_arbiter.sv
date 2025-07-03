`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : HBM Arbiter
Timing      : Combinatorial
Description : This module is used to schedule the data prefetched from HBM to Matrix SRAM and Scratchpad SRAM.
            : It also shdules the write process from the two SRAMs to HBM.
            ： When the prefetch data is ready, it will outputs to the pipeline control to decide when to pass the data to the sram.
Status      : No longer used
*/

module hbm_arbiter #(
    localparam int M_BLOCK_NUM      = MLEN / BLOCK_DIM,
    localparam int V_BLOCK_NUM      = VLEN / BLOCK_DIM,
    localparam int HBM_ELE_WIDTH    = MLEN * MLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1),
    localparam int HBM_SCALE_WIDTH  = MLEN * M_BLOCK_NUM * MXFP_SCALE_WIDTH,
    localparam int PREFETCH_ELE_WIDTH        = HBM_Parallel_Rd_Dim * MLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1),
    localparam int PREFETCH_SCALE_WIDTH      = HBM_Parallel_Rd_Dim * M_BLOCK_NUM * MXFP_SCALE_WIDTH,
    localparam int M_ELE_WIDTH      = Matrix_Parallel_Rd_Dim * MLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1),
    localparam int M_SCALE_WIDTH    = Matrix_Parallel_Rd_Dim * M_BLOCK_NUM * MXFP_SCALE_WIDTH,
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

    input    logic   [V_ELE_WIDTH - 1 : 0]            v_out_element,
    input    logic   [V_SCALE_WIDTH - 1 : 0]          v_out_scale,
    input    logic                                  v_out_data_wen,

    // Control signals
    input    H_OP                                   h_op, 
    input    logic                                  continuous_prefetch_m_en, // For matrix prefetch, it requires multiple cycles to prefetch the MLEN * MLEN data to the matrix sram.
    output   logic                                  hbm_m_prefetch_complete, // For matrix prefetch, indicates that this data is already fetched from HBM and can be extracted directly.
    output   logic                                  hbm_v_prefetch_complete,  // For vector prefetch, indicates that this data is already fetched from HBM and can be extracted directly.
    output   logic                                  hbm_arbiter_busy
);

// Parameters
localparam M_LD_AMOUNT = HBM_M_Prefetch_Amount / Matrix_Parallel_Rd_Dim;
localparam V_LD_AMOUNT = HBM_V_Prefetch_Amount;

localparam MATRIX_READ_ITERATIONS = MLEN / Parallel_Rd_Dim;

typedef enum logic [1:0] {
    IDLE            = 2'b00, 
    HBM_PREFETCH_M  = 2'b01, 
    HBM_PREFETCH_V  = 2'b10, 
    HBM_STORE_V     = 2'b11
} HBM_STATE;

HBM_STATE hbm_state, next_hbm_state, previous_hbm_state;

logic [MLEN - 1 : 0] [V_ELE_WIDTH - 1 : 0]       hbm_v_element;
logic [MLEN - 1 : 0] [V_SCALE_WIDTH - 1 : 0]     hbm_v_scale;
logic [MLEN - 1 : 0] [HBM_ADDR_WIDTH - 1 : 0]    hbm_v_addr_tag;

logic [MATRIX_READ_ITERATIONS - 1 : 0][ELE_WIDTH - 1 : 0]       hbm_m_element;
logic [MATRIX_READ_ITERATIONS - 1 : 0][SCALE_WIDTH - 1 : 0]     hbm_m_scale;
logic [MATRIX_READ_ITERATIONS - 1 : 0] [HBM_ADDR_WIDTH - 1 : 0]  hbm_m_addr_tag;
logic tag_m_valid, tag_v_valid;

assign hbm_arbiter_busy = (hbm_state != IDLE) ? 1'b1 : 1'b0;

// Storting the prefetch data
always_ff @(posedge clk or posedge rst) begin
    if (rst) begin
        hbm_state <= IDLE;
        previous_hbm_state <= IDLE;
        tag_m_valid <= 1'b0;
        tag_v_valid <= 1'b0;
    end else begin
        hbm_state <= next_hbm_state;
        previous_hbm_state <= hbm_state;
        if (prefetch_data_valid) begin
            if (hbm_state == HBM_PREFETCH_V) begin
                tag_v_valid <= 1'b1;
                hbm_v_element <= prefetch_element;
                hbm_v_scale   <= prefetch_scale;
                for (int i = 0; i < MLEN; i++) begin
                    hbm_v_addr_tag[i] <= addr_for_prefetched_data + i * (MLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) / 8);
                end
            end else if (hbm_state == HBM_PREFETCH_M) begin
                tag_m_valid <= 1'b1;
                hbm_m_element   <= prefetch_element;
                hbm_m_scale     <= prefetch_scale;
                for (int i = 0; i < MATRIX_READ_ITERATIONS; i++) begin
                    hbm_m_addr_tag[i] <= addr_for_prefetched_data + i * (Parallel_Rd_Dim * MLEN * (MXFP_EXP_WIDTH + MXFP_MANT_WIDTH + 1) / 8);
                end
            end
        end 
    end
end

logic [HBM_ADDR_WIDTH - 1 : 0]      recorded_hbm_prefetch_addr;
logic [MLEN - 1 : 0]     matched_v_tag;

logic [MATRIX_READ_ITERATIONS - 1 : 0] matched_m_tag;

logic [V_ELE_WIDTH- 1 : 0]          matched_v_element;
logic [V_SCALE_WIDTH- 1 : 0]        matched_v_scale;

logic [ELE_WIDTH - 1 : 0]            matched_m_element;
logic [SCALE_WIDTH - 1 : 0]          matched_m_scale;

always_comb  begin
    case (hbm_state)
        IDLE: begin
            if (h_op == PREFETCH_M || continuous_prefetch_m_en == 1'b1) begin
                next_hbm_state = HBM_PREFETCH_M;
                hbm_prefetch_en = 1'b1;
            end else if (h_op == PREFETCH_V) begin
                next_hbm_state = HBM_PREFETCH_V;
                hbm_prefetch_en = 1'b1;
            end else if (h_op == STORE_V) begin
                next_hbm_state = HBM_STORE_V;
                hbm_prefetch_en = 1'b0;
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
                
            end
            if (previous_hbm_state == IDLE) begin
                // Only update when the state just changed from IDLE to HBM_PREFETCH_M
                recorded_hbm_prefetch_addr = addr_to_prefetch;
            end

        end

        HBM_PREFETCH_V: begin
            hbm_prefetch_en = 1'b0;
            if (prefetch_v_ready & hbm_v_prefetch_complete) begin
                next_hbm_state = IDLE;
                prefetch_v_element = matched_v_element;
                prefetch_v_scale   = matched_v_scale;
            end else begin
                next_hbm_state = HBM_PREFETCH_V;
            end
            if (previous_hbm_state == IDLE) begin
                // Only update when the state just changed from IDLE to HBM_PREFETCH_M
                recorded_hbm_prefetch_addr = addr_to_prefetch;
            end
        end

        HBM_STORE_V: begin
            if (v_out_data_wen & hbm_write_ready) begin
                next_hbm_state = IDLE;
                hbm_write_en = 1'b1;
                hbm_write_element   = {{ELE_WIDTH - V_ELE_WIDTH{1'b0}}, v_out_element};
                hbm_write_scale     = {{SCALE_WIDTH - V_SCALE_WIDTH{1'b0}}, v_out_scale};
                hbm_write_valid     = 1'b1;
            end else begin
                next_hbm_state = HBM_STORE_V;
                hbm_write_en = 1'b0;
            end
        end

        default: next_hbm_state = IDLE;
        
    endcase
    // Check if the prefetch data is ready.
    if ((hbm_state == HBM_PREFETCH_V) & (tag_v_valid == 1'b1)) begin
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
    end else if ((hbm_state == HBM_PREFETCH_M) & (tag_m_valid == 1'b1)) begin
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