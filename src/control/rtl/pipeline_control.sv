`timescale 1ns / 1ps
`include "operation.svh"
`include "configuration.svh"

/*
Module      : Pipeline Control
Timing      : Combinatorial
Description : This module monitors the execution stages of each module and decide whether the pipeline is stalled or not. 
            : This module will also control the overall execution of the coprocessor.
            ：Note: The pipeline stages are listed as follows:
            For Vect/Matrix     | Decode | Decision | Data Prep | Execute | Write Back |
            For FP Scalar       | Decode | Decision | Execute | Write Back |
            For Fixed Scalar    | Decode | Execute  | Write Back |
*/

module pipeline_control #(
    parameter   OPERAND_WIDTH           = 5,
    parameter   FIXED_OPERAND_WIDTH     = 5,
    parameter   FP_OPERAND_WIDTH        = 5,
    parameter   FIXED_DATA_WIDTH        = 32,
    parameter   IMM_WIDTH               = 12
) (
    input       logic clk,
    input       logic rst,

    // Decoded Instruction
    input       OP_BUNDLE       decoded_op_bundle,

    // Address
    input       logic [FIXED_DATA_WIDTH - 1 : 0] fixed_addr_1,
    input       logic [FIXED_DATA_WIDTH - 1 : 0] fixed_addr_2,

    // Memory Monitor
    input       logic s_sram_wen_a,
    input       logic [FIXED_DATA_WIDTH - 1 : 0]    s_sram_addr_a,
    input       logic s_sram_wen_b,
    input       logic [FIXED_DATA_WIDTH - 1 : 0]    s_sram_addr_b,

    // Execution Monitor
    input       MEM_WREQ_INFO   mem_write_req,
    input       logic           hbm_in_used,            // Activated when we need to prefetch data from HBM through TL.
    input       logic           continuous_m_prefetch,  // TODO: should be optimized in the future.
    input       logic           fp_stall_req,
    input       logic           fixed_stall_req,
    input       logic           m_load_in_process,
    input       logic           v_load_in_process,

    // Current control operation
    output      logic           pipeline_stall_req,
    output      OP_BUNDLE       assigned_op_bundle,
    output      MEM_WEN_INFO    mem_write_control
);

import pipeline_pkg::*;
    // Pipeline Control
    logic pipeline_stall;
    logic stall_for_prefetch;
    // Decision for pipeline stall
    always_comb begin
        if(stall_in_process) begin
            if(prefetch_in_progress & (recorded_op_bundle.h_op == PREFETCH_M || recorded_op_bundle.h_op == PREFETCH_V )) begin
                pipeline_stall = 1'b1;
            end else begin
                pipeline_stall = 1'b0;
            end
        end else begin
            // If the current decoded instruction is Memory/Vector that required access to thress operands values, stall the pipeline for single cycle to read the rd content.
            if ((prefetch_in_progress || m_load_in_process) & (decoded_op_bundle.m_op != STALL_M)) begin
                // Note: Any M type instruction involves interaction with the matrix sram, hence need to stall when its prefetching.
                pipeline_stall   = 1'b1;            
            end else if ((mem_write_req.wreq_m_sram == 1'b1 || mem_write_req.wreq_s_sram_port_b == 1'b1) & (decoded_op_bundle.m_op != STALL_M) ) begin
                // In prefetching mode
                pipeline_stall   = 1'b1;
            end else if (prefetch_in_progress & (decoded_op_bundle.h_op == PREFETCH_M || decoded_op_bundle.h_op == PREFETCH_V)) begin
                // Prefetching another data while the previous prefetching is not done yet.
                pipeline_stall   = 1'b1;            
            end else if ((prefetch_in_progress || mem_write_req.wreq_s_sram_port_b == 1'b1 || v_load_in_process) & ( decoded_op_bundle.v_ele_op != STALL_V_ELEMENT || decoded_op_bundle.v_reduct_op != STALL_V_REDUCT)) begin
                // Trying to access the two ports of the vector sram while it is being written to.
                pipeline_stall   = 1'b1;            
            end else if (fp_stall_req & (decoded_op_bundle.s_fp_op != STALL_S_FP)) begin
                // Release until the prefetching is done.
                pipeline_stall   = 1'b1;            
            end else if (mem_vwrite_stall_req) begin
                // Unconditionally stall the overall pipeline.
                pipeline_stall   = 1'b1;                
            end else begin
                pipeline_stall   = 1'b0;
            end
        end
    end

    assign pipeline_stall_req = pipeline_stall || stall_in_process; // Extra stall cycle in order to execute the previously unexecuted operation.

    // Prefetch monitor
    logic prefetch_in_progress;
    logic delayed_hbm_in_used; // Extend extra cycle to determine the write to matrix/scratchpad sram
    logic prefetch_stage_1_in_progress, prefetch_stage_2_in_progress;

    assign prefetch_in_progress = prefetch_stage_1_in_progress || prefetch_stage_2_in_progress || continuous_m_prefetch;
    assign prefetch_stage_2_in_progress = hbm_in_used || delayed_hbm_in_used;

    logic [$clog2(PREFETCH_STAGE_1_CYCLES) : 0] prefetch_stage_1_counter;

    always_ff @(posedge clk) begin
        if (rst) begin
            prefetch_stage_1_in_progress <= 1'b0;
            prefetch_stage_1_counter <= 'b0;
            delayed_hbm_in_used <= 1'b0;
        end else begin
            delayed_hbm_in_used <= hbm_in_used;
            if (!pipeline_stall & stall_in_process & (recorded_op_bundle.h_op == PREFETCH_M || recorded_op_bundle.h_op == PREFETCH_V)) begin
                prefetch_stage_1_in_progress <= 1'b1;
                prefetch_stage_1_counter <= 'b0;
            end else if (!pipeline_stall && (decoded_op_bundle.h_op == PREFETCH_M || decoded_op_bundle.h_op == PREFETCH_V)) begin
                prefetch_stage_1_in_progress <= 1'b1;
                prefetch_stage_1_counter <= 'b0;
            end  else if (prefetch_stage_1_counter == PREFETCH_STAGE_1_CYCLES-1) begin
                prefetch_stage_1_in_progress <= 1'b0;
                prefetch_stage_1_counter <= 'b0;
            end else if (prefetch_stage_1_in_progress) begin
                prefetch_stage_1_counter <= prefetch_stage_1_counter + 1'b1;
            end else begin
                prefetch_stage_1_counter <= 'b0;
            end
        end
    end

    // Memory Monitor
    logic           mem_vwrite_stall_req;

    addr_monitor #(
        .ADDR_WIDTH(FIXED_DATA_WIDTH),
        .PIPELINE_STAGES(MAX_PIPELINE_STAGE)
    ) addr_monitor_inst (
        .clk(clk),
        .rst(rst),
        .assigned_op_bundle     (assigned_op_bundle),
        .decoded_op_bundle      (decoded_op_bundle),
        .fixed_addr_1           (fixed_addr_1),
        .fixed_addr_2           (fixed_addr_2),
        .s_sram_addr_a          (s_sram_addr_a),
        .s_sram_addr_b          (s_sram_addr_b),
        .s_sram_wen_a           (s_sram_wen_a),
        .s_sram_wen_b           (s_sram_wen_b),
        .stall_req              (mem_vwrite_stall_req)
    );



    // Operation Assignment
    OP_BUNDLE          invalid_op_bundle, recorded_op_bundle, current_decoded_op_bundle;
    logic stall_in_process;
    always_ff @(posedge clk or negedge rst) begin
        if (rst) begin
            stall_in_process <= 1'b0;
        end else if (pipeline_stall) begin
            stall_in_process <= 1'b1;
        end else begin
            stall_in_process <= 1'b0;
        end
    end

    always_comb begin
        current_decoded_op_bundle.m_op            = decoded_op_bundle.m_op;
        current_decoded_op_bundle.v_ele_op        = decoded_op_bundle.v_ele_op;
        current_decoded_op_bundle.v_reduct_op     = decoded_op_bundle.v_reduct_op;
        current_decoded_op_bundle.s_fp_op         = decoded_op_bundle.s_fp_op;
        current_decoded_op_bundle.c_op            = decoded_op_bundle.c_op;
        current_decoded_op_bundle.h_op            = decoded_op_bundle.h_op;
        current_decoded_op_bundle.m_transposed_read = decoded_op_bundle.m_transposed_read;
        current_decoded_op_bundle.v_broadcast_en  = decoded_op_bundle.v_broadcast_en;
        current_decoded_op_bundle.fps1            = decoded_op_bundle.fps1;
        current_decoded_op_bundle.fps2            = decoded_op_bundle.fps2;
        current_decoded_op_bundle.fpd             = decoded_op_bundle.fpd;
        current_decoded_op_bundle.addr_1          = fixed_addr_1;
        current_decoded_op_bundle.addr_2          = fixed_addr_2; 
        current_decoded_op_bundle.update_m_waddr  = decoded_op_bundle.update_m_waddr;
        current_decoded_op_bundle.update_v_waddr  = decoded_op_bundle.update_v_waddr;
    end
    
    assign invalid_op_bundle = '{
        m_op                : STALL_M,
        v_ele_op            : STALL_V_ELEMENT,
        v_reduct_op         : STALL_V_REDUCT,
        s_fp_op             : STALL_S_FP,
        c_op                : STALL_C,
        h_op                : STALL_H,
        m_transposed_read   : 1'b0,
        v_broadcast_en      : 1'b0,
        fps1                : '0,
        fps2                : '0,
        fpd                 : '0,
        addr_1              : '0,
        addr_2              : '0,
        update_m_waddr      : 1'b0,
        update_v_waddr      : 1'b0
    };

    always_ff @(posedge clk or negedge rst) begin
        if (rst) begin
            mem_write_control <= '{
                w_m_sram_en:        1'b0,
                w_s_sram_port_a_en: 1'b0,
                w_s_sram_port_b_en: 1'b0
            };
        end else begin
            mem_write_control <= '{
                w_m_sram_en           : mem_write_req.wreq_m_sram,
                w_s_sram_port_a_en    : mem_write_req.wreq_s_sram_port_a,
                w_s_sram_port_b_en    : mem_write_req.wreq_s_sram_port_b
            };

            if (pipeline_stall) begin
                assigned_op_bundle <= invalid_op_bundle;
                if (!stall_in_process) begin
                    // If the pipeline is just start
                    recorded_op_bundle <= current_decoded_op_bundle;
                end
            end else begin
                if (stall_in_process) begin
                    // Last piplie, record the previously unexecuted operation
                    assigned_op_bundle <= recorded_op_bundle;
                end else begin
                    assigned_op_bundle <= current_decoded_op_bundle;
                end

            end
        end
    end




endmodule