`timescale 1ns / 1ps
`include "operation.svh"


/*
Module      : Address Dependency Monitor
Timing      : Sequential, 1 cycle to make the decision
Description : 
*/

module addr_monitor#(
    parameter   ADDR_WIDTH           = 5,
    parameter   PIPELINE_STAGES      = 4
) (
    input   logic clk,
    input   logic rst,

    // Execution Operation
    input   OP_BUNDLE determine_stage_op,  
    input   OP_BUNDLE exe_stage_op,

    // ---------- Monitor SRAM Write Signals -----------
    input   logic [ADDR_WIDTH - 1 : 0] v_sram_addr_a,
    input   logic [ADDR_WIDTH - 1 : 0] v_sram_addr_b,
    input   logic v_sram_wen_a,
    input   logic v_sram_wen_b,

    // Stall Decision
    output  logic stall_req,
    input   logic sys_pipe_stall
);

    // Track Write V Address
    typedef struct {
        logic [ADDR_WIDTH-1:0]          track_addr;
        logic                           activate;
    } TRACK_ADDR;

    localparam TRACK_ADDR_WIDTH = $clog2(PIPELINE_STAGES) + 1;
    TRACK_ADDR v_write_addr_track [PIPELINE_STAGES - 1 : 0];
    logic [TRACK_ADDR_WIDTH - 1 : 0]     free_track_entry_idx;
    logic [ADDR_WIDTH - 1 : 0] locked_entry_1, locked_entry_2;
    logic lock_entry_1_valid, lock_entry_2_valid;    
    logic found_invalid;
    logic pipe_full;

    always_comb begin
        found_invalid           = 1'b0;
        free_track_entry_idx    = '0; // default value, in case all are valid
        for (int i = 0; i < PIPELINE_STAGES; i++) begin
            if (!v_write_addr_track[i].activate && !found_invalid) begin
                free_track_entry_idx    = i;
                found_invalid           = 1'b1;
            end
        end
        pipe_full = !found_invalid;
    end

    // Detection Process
    logic [PIPELINE_STAGES - 1 : 0] addr_collide_flag;
    logic stall_in_process;
    always_comb begin
        if (stall_in_process) begin
            // To Check if the tracked address has been written.
            for (int i = 0; i < PIPELINE_STAGES; i++) begin
                if (((v_write_addr_track[i].track_addr == locked_entry_1)) & (v_write_addr_track[i].activate == 1'b1) & lock_entry_1_valid) begin
                    addr_collide_flag[i] = 1'b1;
                end else if (((v_write_addr_track[i].track_addr == locked_entry_2)) & (v_write_addr_track[i].activate == 1'b1) & lock_entry_2_valid) begin
                    addr_collide_flag[i] = 1'b1;
                end else begin
                    addr_collide_flag[i] = 1'b0;
                end
            end
            stall_req = |addr_collide_flag;

        end else if (!sys_pipe_stall) begin
            if ((determine_stage_op.m_op != STALL_M & determine_stage_op.m_op != MM_WO) ||((determine_stage_op.v_ele_op != STALL_V_ELEMENT) & (!determine_stage_op.v_broadcast_en)) || (determine_stage_op.v_reduct_op != STALL_V_REDUCT)) begin        
                // Two ports of address to monitor
                for (int i = 0; i < PIPELINE_STAGES; i++) begin
                    if ((v_write_addr_track[i].track_addr == determine_stage_op.addr_1) & (v_write_addr_track[i].activate == 1'b1)) begin
                        addr_collide_flag[i] = 1'b1;
                        locked_entry_1 = determine_stage_op.addr_1;
                        lock_entry_1_valid = 1'b1;
                    end else if ((v_write_addr_track[i].track_addr == determine_stage_op.addr_2) & (v_write_addr_track[i].activate == 1'b1)) begin
                        addr_collide_flag[i] = 1'b1;
                        locked_entry_2 = determine_stage_op.addr_2;
                        lock_entry_2_valid = 1'b1;
                    end else begin
                        addr_collide_flag[i] = 1'b0;
                    end
                end
                stall_req = |addr_collide_flag;
            end else if (((determine_stage_op.v_ele_op != STALL_V_ELEMENT) & (determine_stage_op.v_broadcast_en))) begin
                // One port of address to monitor
                for (int i = 0; i < PIPELINE_STAGES; i++) begin
                    if (((v_write_addr_track[i].track_addr == determine_stage_op.addr_1)) & (v_write_addr_track[i].activate == 1'b1)) begin
                        addr_collide_flag[i] = 1'b1;
                        locked_entry_1 = determine_stage_op.addr_1;
                        lock_entry_1_valid = 1'b1;
                    end else begin
                        addr_collide_flag[i] = 1'b0;
                    end
                end
                stall_req = |addr_collide_flag;
            end else if (determine_stage_op.h_op == STORE_V_C ||determine_stage_op.h_op == STORE_V_S ) begin
                // One port of address to monitor
                for (int i = 0; i < PIPELINE_STAGES; i++) begin
                    if (((v_write_addr_track[i].track_addr == determine_stage_op.addr_2)) & (v_write_addr_track[i].activate == 1'b1)) begin
                        addr_collide_flag[i] = 1'b1;
                        locked_entry_2 = determine_stage_op.addr_2;
                        lock_entry_2_valid = 1'b1;
                    end else begin
                        addr_collide_flag[i] = 1'b0;
                    end
                end
                stall_req = |addr_collide_flag;
            end else begin
                stall_req = 1'b0;
                lock_entry_1_valid = 1'b0;
                lock_entry_2_valid = 1'b0;
                locked_entry_1 = '0;
                locked_entry_2 = '0;
            end 
        end else begin
            // If the system is stalled, we do not need to check for address collision.
            stall_req = 1'b0;
            lock_entry_1_valid = 1'b0;
            lock_entry_2_valid = 1'b0;
            locked_entry_1 = '0;
            locked_entry_2 = '0;
        end

    end

    // Update Process
    logic   [ADDR_WIDTH - 1 : 0] insert_addr;
    logic   insert_valid;

    logic   matched_waddr;
    logic   [TRACK_ADDR_WIDTH-1:0] matched_track_entry_idx;
    logic   match_waddr_valid;

    // Decide which source is providing the address this cycle
    always_comb begin
        if (exe_stage_op.h_op == PREFETCH_V_C) begin
            // Note, PREFETCH_M_C does not need to be monitored as it cannot be directly written.
            insert_addr  = exe_stage_op.addr_2;
            insert_valid = 1'b1;
        end else if (exe_stage_op.update_m_waddr) begin
            insert_addr  = exe_stage_op.addr_2;
            insert_valid = 1'b1;
        end else if (exe_stage_op.update_v_waddr) begin
            insert_addr  = exe_stage_op.addr_2;
            insert_valid = 1'b1;
        end else if (exe_stage_op.s_fp_op == MAP_V_FP) begin
            insert_addr  = exe_stage_op.addr_2;
            insert_valid = 1'b1;
        end else begin
            insert_addr  = {ADDR_WIDTH{1'b0}};
            insert_valid = 1'b0;
        end
        // Check if the address is already in the pipeline
        matched_waddr                 = 1'b0;
        matched_track_entry_idx     = '0; // default value, in case all are valid
        for (int i = 0; i < PIPELINE_STAGES; i++) begin
            if (((v_sram_wen_a && v_write_addr_track[i].track_addr == v_sram_addr_a) ||
                    (v_sram_wen_b && v_write_addr_track[i].track_addr == v_sram_addr_b)) & !matched_waddr) begin
                matched_track_entry_idx     = i;
                matched_waddr                 = 1'b1;
            end
        end
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            for (int i = 0; i < PIPELINE_STAGES; i++) begin
                v_write_addr_track[i] <= '{
                    track_addr : {ADDR_WIDTH{1'b0}},
                    activate   : 1'b0
                };
            end
            stall_in_process <= 1'b0;
        end else begin
            stall_in_process <= stall_req;
            // Try inserting into the first available empty slot
            if (pipe_full == 1'b0 & insert_valid) begin
                v_write_addr_track[free_track_entry_idx] <= '{
                    track_addr : insert_addr,
                    activate   : 1'b1
                };
            end

            // Clear track entry if corresponding write to s_sram occurs
            if (matched_waddr) begin
                v_write_addr_track[matched_track_entry_idx] <= '{
                    track_addr : {ADDR_WIDTH{1'b0}},
                    activate   : 1'b0
                };
            end
        end
    end



endmodule