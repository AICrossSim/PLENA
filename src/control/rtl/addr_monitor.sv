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
    input   OP_BUNDLE assigned_op_bundle,  

    // ----------- Monitor Operand Write Signals -----------
    input   logic [ADDR_WIDTH - 1 : 0] load_m_waddr,
    input   logic load_m_waddr_en,
    input   logic [ADDR_WIDTH - 1 : 0] load_v_waddr,
    input   logic load_v_waddr_en,

    // ---------- Monitor Operand Read Signals -----------
    input   logic [ADDR_WIDTH - 1 : 0] fixed_addr_1,
    input   logic [ADDR_WIDTH - 1 : 0] fixed_addr_2,

    // ---------- Monitor SRAM Write Signals -----------
    input   logic [ADDR_WIDTH - 1 : 0] s_sram_addr_a,
    input   logic [ADDR_WIDTH - 1 : 0] s_sram_addr_b,
    input   logic s_sram_wen_a,
    input   logic s_sram_wen_b,

    // Stall Decision
    output  logic stall_req
);

    // Track Write V Address
    typedef struct {
        logic [ADDR_WIDTH-1:0]          track_addr;
        logic                           activate;
    } TRACK_ADDR;

    TRACK_ADDR v_write_addr_track [PIPELINE_STAGES - 1 : 0];
    logic [$clog2(PIPELINE_STAGES) : 0]     free_track_entry_idx;    
    logic                                   found_invalid;
    logic                                   pipe_full;

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
    always_comb begin
        if ((assigned_op_bundle.m_op != STALL_M) ||((assigned_op_bundle.v_ele_op != STALL_V_ELEMENT) & (!assigned_op_bundle.v_broadcast_en)) || (assigned_op_bundle.v_reduct_op != STALL_V_REDUCT)) begin        
            // Two ports of address to monitor
            for (int i = 0; i < PIPELINE_STAGES; i++) begin
                if (((v_write_addr_track[i].track_addr == fixed_addr_1) || (v_write_addr_track[i].track_addr == fixed_addr_2)) & (v_write_addr_track[i].activate == 1'b1)) begin
                    addr_collide_flag[i] = 1'b1;
                end else begin
                    addr_collide_flag[i] = 1'b0;
                end
            end
            stall_req = |addr_collide_flag;
        end else if (((assigned_op_bundle.v_ele_op != STALL_V_ELEMENT) & (assigned_op_bundle.v_broadcast_en))) begin
            // One port of address to monitor
            for (int i = 0; i < PIPELINE_STAGES; i++) begin
                if (((v_write_addr_track[i].track_addr == fixed_addr_1)) & (v_write_addr_track[i].activate == 1'b1)) begin
                    addr_collide_flag[i] = 1'b1;
                end else begin
                    addr_collide_flag[i] = 1'b0;
                end
            end
            stall_req = |addr_collide_flag;
        end else begin
            stall_req = 1'b0;
        end 
    end


    // Update Process
    logic [ADDR_WIDTH - 1 : 0] insert_addr;
    logic   insert_valid;

    always_comb begin
        // Decide which source is providing the address this cycle
        if (assigned_op_bundle.h_op == PREFETCH_V) begin
            insert_addr  = fixed_addr_1;
            insert_valid = 1'b1;
        end else if (load_m_waddr_en) begin
            insert_addr  = fixed_addr_2;
            insert_valid = 1'b1;
        end else if (load_v_waddr_en) begin
            insert_addr  = fixed_addr_2;
            insert_valid = 1'b1;
        end else begin
            insert_addr  = {ADDR_WIDTH{1'b0}};
            insert_valid = 1'b0;
        end
    end

    always_ff @(posedge clk or negedge rst) begin
        if (rst) begin
            for (int i = 0; i < PIPELINE_STAGES; i++) begin
                v_write_addr_track[i] <= '{
                    track_addr : {ADDR_WIDTH{1'b0}},
                    activate   : 1'b0
                };
            end
        end else begin
            // Try inserting into the first available empty slot
            if (pipe_full == 1'b0 & insert_valid) begin
                v_write_addr_track[free_track_entry_idx] <= '{
                    track_addr : insert_addr,
                    activate   : 1'b1
                };
            end

            // Clear track entry if corresponding write to s_sram occurs
            for (int i = 0; i < PIPELINE_STAGES; i++) begin
                if ((s_sram_wen_a && v_write_addr_track[i].track_addr == s_sram_addr_a) ||
                    (s_sram_wen_b && v_write_addr_track[i].track_addr == s_sram_addr_b)) begin
                    v_write_addr_track[i].activate <= 1'b0;
                end
            end
        end
    end


endmodule