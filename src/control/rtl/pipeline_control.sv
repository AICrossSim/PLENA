`timescale 1ns / 1ps
`include "operation.svh"
`include "configuration.svh"

/*
Module      : Pipeline Control
Timing      : Combinatorial
Description : This module monitors the execution stages of each module and decide whether the pipeline is stalled or not. 
            : This module will also control the overall execution of the coprocessor.
*/

module pipeline_control #(
    parameter   OPERAND_WIDTH           = 5,
    parameter   FIXED_OPERAND_WIDTH     = 5,
    parameter   FP_OPERAND_WIDTH        = 5,
    parameter   FIXED_DATA_WIDTH        = 32,
    parameter   IMM_WIDTH             = 12
) (
    input       logic clk,
    input       logic rst,

    // Decoded Instruction
    input       INSTR_INFO decode_instr_info,
    input       logic decode_instr_valid,
    output      logic fetch_next_instr,

    // Execution Monitor
    input       MEM_STALL_TYPE  mem_stall_req,
    input       logic           hbm_in_used,   // Activated when we need to prefetch data from HBM through TL.
    input       logic           continuous_m_prefetch,  // TODO: should be optimized in the future.

    // Current control operation
    output      logic           pipeline_stall,
    output      OP_BUNDLE       assigned_op_bundle,
    output      logic           m_update_waddr,
    output      logic           v_update_waddr,

    output      logic [FIXED_OPERAND_WIDTH - 1 : 0] rs1,
    output      logic [FIXED_OPERAND_WIDTH - 1 : 0] rs2,
    output      logic [FIXED_OPERAND_WIDTH - 1 : 0] rd,
    output      logic [FP_OPERAND_WIDTH - 1 : 0]    fps1,
    output      logic [FP_OPERAND_WIDTH - 1 : 0]    fps2,
    output      logic [FP_OPERAND_WIDTH - 1 : 0]    fpd,
    output      logic [IMM_WIDTH - 1 : 0]           imm
);

import pipeline_pkg::*;
    // Pipeline Control
    
    // Status Monitor Signals
    // Prefetch monitor
    logic prefetch_in_progress;
    logic prefetch_stage_1_in_progress, prefetch_stage_2_in_progress;
    assign prefetch_in_progress = prefetch_stage_1_in_progress || prefetch_stage_2_in_progress || continuous_m_prefetch;
    assign prefetch_stage_2_in_progress = hbm_in_used;
    logic [$clog2(PREFETCH_STAGE_1_CYCLES) : 0] prefetch_stage_1_counter;

    always_ff @(posedge clk) begin
        if (rst) begin
            prefetch_stage_1_in_progress <= 1'b0;
            prefetch_stage_1_counter <= 'b0;
        end else begin
            if (!pipeline_stall && decode_instr_valid && (decode_instr_info.opcode == H_PREFETCH_M || decode_instr_info.opcode == H_PREFETCH_V)) begin
                prefetch_stage_1_in_progress <= 1'b1;
                prefetch_stage_1_counter <= 'b0;
            end else if (prefetch_stage_1_counter == PREFETCH_STAGE_1_CYCLES - 1) begin
                prefetch_stage_1_in_progress <= 1'b0;
                prefetch_stage_1_counter <= 'b0;
            end else if (prefetch_stage_1_in_progress) begin
                prefetch_stage_1_counter <= prefetch_stage_1_counter + 1'b1;
            end else begin
                prefetch_stage_1_counter <= 'b0;
            end
        end
    end

    // Matrix Monitor
    logic rd_operand_ready; // The stall is for loading the third operand from the register files.


    // Decision for pipeline stall
    always_comb begin
        // If the current decoded instruction is Memory/Vector that required access to thress operands values, stall the pipeline for single cycle to read the rd content.
        if (rd_operand_ready == 1'b0 & (decode_instr_info.opcode == M_MV_O || decode_instr_info.opcode == M_TMV_O)) begin
            m_update_waddr   = 1'b1;
            v_update_waddr   = 1'b0;
            pipeline_stall   = 1'b1;
        end else if (prefetch_in_progress & (decode_instr_info.instruction_type == M)) begin
            // Note: Any M type instruction involves interaction with the matrix sram, hence need to stall when its prefetching.
            m_update_waddr   = 1'b0;
            v_update_waddr   = 1'b0;
            pipeline_stall   = 1'b1;            
        end else if (decode_instr_info.opcode == V_ADD_VV || decode_instr_info.opcode == V_SUB_VV || decode_instr_info.opcode == V_MUL_VV) begin
            m_update_waddr   = 1'b0;
            v_update_waddr   = 1'b1;
            pipeline_stall   = 1'b1;
        end else if (mem_stall_req.stall_m_sram == 1'b1 & (decode_instr_info.opcode == M_MV || decode_instr_info.opcode == M_TMV) ) begin
            m_update_waddr   = 1'b0;
            v_update_waddr   = 1'b0;
            pipeline_stall   = 1'b1;
        end else if (prefetch_in_progress & (decode_instr_info.opcode == H_PREFETCH_M || decode_instr_info.opcode == H_PREFETCH_V)) begin
            // Release until the prefetching is done.
            m_update_waddr   = 1'b0;
            v_update_waddr   = 1'b0;
            pipeline_stall   = 1'b1;            
        end else begin
            m_update_waddr   = 1'b0;
            v_update_waddr   = 1'b0;
            pipeline_stall   = 1'b0;
        end

    end

    assign fetch_next_instr = decode_instr_valid && !pipeline_stall;

    always_ff @(posedge clk) begin
        // TODO rewrite the pipeline determination logic
        if (pipeline_stall) begin
            // Stall Condition 1: When the three oprands both pointer for addresses, need 2 cycles to obtain the address for the two port regfile.
            if (m_update_waddr || v_update_waddr) begin
                rd_operand_ready <= 1'b1;
                assigned_op_bundle.m_op            <= STALL_M;
                assigned_op_bundle.v_ele_op        <= STALL_V_ELEMENT;
                assigned_op_bundle.v_reduct_op     <= STALL_V_REDUCT;
                assigned_op_bundle.s_fp_op         <= STALL_S_FP;
                assigned_op_bundle.s_fixed_op      <= COMP_ADDR;
                assigned_op_bundle.c_op            <= STALL_C;
                assigned_op_bundle.h_op            <= STALL_H;
                rs1             <= rd;
                rs2             <= 'b0;
                rd              <= 'b0;
                fps1            <= 'b0;
                fps2            <= 'b0;
                fpd             <= 'b0;
                imm             <= 'b0;
            end else begin
                // If any of the stall request is enabled.
                rd_operand_ready <= 1'b0;
                assigned_op_bundle.m_op            <= STALL_M;
                assigned_op_bundle.v_ele_op        <= STALL_V_ELEMENT;
                assigned_op_bundle.v_reduct_op     <= STALL_V_REDUCT;
                assigned_op_bundle.s_fp_op         <= STALL_S_FP;
                assigned_op_bundle.s_fixed_op      <= COMP_ADDR;
                assigned_op_bundle.c_op            <= STALL_C;
                assigned_op_bundle.h_op            <= STALL_H;
                rs1             <= 'b0;
                rs2             <= 'b0;
                rd              <= 'b0;
                fps1            <= 'b0;
                fps2            <= 'b0;
                fpd             <= 'b0;
                imm             <= 'b0;
            end
            
            // Memory Req was set to be the highest priority. TODO
            assigned_op_bundle.stall_for_memory <= mem_stall_req;

        end else begin
            rd_operand_ready <= 1'b0;

            assigned_op_bundle.m_transposed_read   <= (decode_instr_info.opcode == M_TMV || decode_instr_info.opcode == M_TMV_O) ? 1'b1 : 1'b0;
            assigned_op_bundle.v_broadcast_en      <= (decode_instr_info.opcode == V_ADD_VF || decode_instr_info.opcode == V_SUB_VF || decode_instr_info.opcode == V_MUL_VF) ? 1'b1 : 1'b0;
            
            // Normal execution without stalls for memory.
            assigned_op_bundle.stall_for_memory <= mem_stall_req;

            case(decode_instr_info.instruction_type)
                M: begin
                    assigned_op_bundle.m_op        <= (decode_instr_info.opcode == M_MV || decode_instr_info.opcode == M_TMV) ? MV : MV_O;
                    assigned_op_bundle.v_ele_op    <= STALL_V_ELEMENT;
                    assigned_op_bundle.v_reduct_op <= STALL_V_REDUCT;
                    assigned_op_bundle.s_fp_op     <= STALL_S_FP;
                    assigned_op_bundle.s_fixed_op  <= COMP_ADDR;
                    assigned_op_bundle.c_op            <= STALL_C;
                    assigned_op_bundle.h_op            <= STALL_H;
                    fps1    <= {FP_OPERAND_WIDTH{1'b0}};
                    fps2    <= {FP_OPERAND_WIDTH{1'b0}};
                    fpd     <= {FP_OPERAND_WIDTH{1'b0}};
                    rs1     <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                    rs2     <= decode_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                    rd      <= decode_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
                    imm     <= 'b0;
                end

                V: begin
                    assigned_op_bundle.m_op <= STALL_M;
                    assigned_op_bundle.v_ele_op <= (decode_instr_info.opcode == V_ADD_VV || decode_instr_info.opcode == V_ADD_VF) ? ADD_V_ELEMENT :
                                            (decode_instr_info.opcode == V_SUB_VV || decode_instr_info.opcode == V_SUB_VF) ? SUB_V_ELEMENT :
                                            (decode_instr_info.opcode == V_MUL_VV || decode_instr_info.opcode == V_MUL_VF) ? MUL_V_ELEMENT :
                                            (decode_instr_info.opcode == V_EXP_VV)    ? EXP_V_ELEMENT : STALL_V_ELEMENT;

                    assigned_op_bundle.v_reduct_op <=  (decode_instr_info.opcode == V_RED_SUM)   ? SUM_V_REDUCT :
                                                (decode_instr_info.opcode == V_RED_MAX)   ? MAX_V_REDUCT : STALL_V_REDUCT;
                    
                    assigned_op_bundle.s_fixed_op   <= COMP_ADDR;
                    assigned_op_bundle.c_op            <= STALL_C;
                    assigned_op_bundle.h_op            <= STALL_H;
                    if (decode_instr_info.opcode == V_ADD_VF || decode_instr_info.opcode == V_SUB_VF || decode_instr_info.opcode == V_MUL_VF) begin
                        assigned_op_bundle.s_fp_op     <= LD_OUT_FP;
                        rs1             <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                        rs2             <= {FIXED_OPERAND_WIDTH{1'b0}};
                        rd              <= decode_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
                        fps1            <= {FP_OPERAND_WIDTH{1'b0}};
                        fps2            <= decode_instr_info.rs2[FP_OPERAND_WIDTH - 1 : 0];
                        fpd             <= {FP_OPERAND_WIDTH{1'b0}};
                        imm             <= {IMM_WIDTH{1'b0}};
                    end else begin
                        assigned_op_bundle.s_fp_op    <= STALL_S_FP;
                        rs1             <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                        rs2             <= decode_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                        rd              <= decode_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
                        imm             <= {IMM_WIDTH{1'b0}};
                    end
                end

                S: begin
                    assigned_op_bundle.m_op            <= STALL_M;
                    assigned_op_bundle.v_ele_op        <= STALL_V_ELEMENT;
                    assigned_op_bundle.v_reduct_op     <= STALL_V_REDUCT;
                    assigned_op_bundle.s_fp_op         <=   (decode_instr_info.opcode == S_ADD_FP )   ? ADD_FP    :
                                                            (decode_instr_info.opcode == S_SUB_FP )   ? SUB_FP    :
                                                            (decode_instr_info.opcode == S_MAX_FP )   ? MAX_FP    :
                                                            (decode_instr_info.opcode == S_MUL_FP )   ? MUL_FP    :
                                                            (decode_instr_info.opcode == S_EXP_FP )   ? EXP_FP    :
                                                            (decode_instr_info.opcode == S_RECI_FP)   ? RECI_FP   :
                                                            (decode_instr_info.opcode == S_SQRT_FP)   ? SQRT_FP   :
                                                            (decode_instr_info.opcode == S_LD_REG_FP) ? LD_REG_FP :
                                                            (decode_instr_info.opcode == S_ST_REG_FP) ? ST_REG_FP : STALL_S_FP;
                    
                    assigned_op_bundle.s_fixed_op      <=   (decode_instr_info.opcode == S_ADD_FIX)   ? ADD_FIX   :
                                                            (decode_instr_info.opcode == S_ADDI_FIX)  ? ADDI_FIX  :
                                                            (decode_instr_info.opcode == S_SUB_FIX)   ? SUB_FIX   : 
                                                            (decode_instr_info.opcode == S_MUL_FIX)   ? MUL_FIX   : 
                                                            (decode_instr_info.opcode == S_DIV_FIX)   ? DIV_FIX   :
                                                            (decode_instr_info.opcode == S_LUI_FIX)   ? LUI_FIX   :
                                                            (decode_instr_info.opcode == S_MV_FIX)    ? MV_FIX    : 
                                                            (decode_instr_info.opcode == S_LD_FIX)    ? LD_FIX    :
                                                            (decode_instr_info.opcode == S_ST_FIX)    ? ST_FIX    : STALL_S_FIXED;
                    assigned_op_bundle.c_op            <= STALL_C;
                    assigned_op_bundle.h_op            <= STALL_H;
                    if (decode_instr_info.opcode == S_ADD_FP || decode_instr_info.opcode == S_SUB_FP || decode_instr_info.opcode == S_MAX_FP || decode_instr_info.opcode == S_MUL_FP) begin
                        // Two FP source operands and one FP destination operand
                        rs1             <= {FIXED_OPERAND_WIDTH{1'b0}};
                        rs2             <= {FIXED_OPERAND_WIDTH{1'b0}};
                        rd              <= {FIXED_OPERAND_WIDTH{1'b0}};
                        fps1            <= decode_instr_info.rs1[FP_OPERAND_WIDTH - 1 : 0];
                        fps2            <= decode_instr_info.rs2[FP_OPERAND_WIDTH - 1 : 0];
                        fpd             <= decode_instr_info.rd[FP_OPERAND_WIDTH - 1 : 0];
                        imm             <= {IMM_WIDTH{1'b0}};
                    end else if (decode_instr_info.opcode == S_EXP_FP || decode_instr_info.opcode == S_RECI_FP || decode_instr_info.opcode == S_SQRT_FP) begin
                        // Single FP source operand and single FP destination operand
                        rs1             <= {FIXED_OPERAND_WIDTH{1'b0}};
                        rs2             <= {FIXED_OPERAND_WIDTH{1'b0}};
                        rd              <= {FIXED_OPERAND_WIDTH{1'b0}};
                        fps1            <= decode_instr_info.rs1[FP_OPERAND_WIDTH - 1 : 0];
                        fps2            <= {FP_OPERAND_WIDTH{1'b0}};
                        fpd             <= decode_instr_info.rd[FP_OPERAND_WIDTH - 1 : 0];
                        imm             <= {IMM_WIDTH{1'b0}};
                    end else if (decode_instr_info.opcode == S_LD_REG_FP || decode_instr_info.opcode == S_ST_REG_FP) begin
                        // Single FIXED Source operand (Storing Addr) and one IMM and one FP destination operand
                        rs1             <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                        rs2             <= {FIXED_OPERAND_WIDTH{1'b0}};
                        rd              <= {FIXED_OPERAND_WIDTH{1'b0}};
                        fps1            <= {FP_OPERAND_WIDTH{1'b0}};
                        fps2            <= {FP_OPERAND_WIDTH{1'b0}};
                        fpd             <= decode_instr_info.rd[FP_OPERAND_WIDTH - 1 : 0];
                        imm             <= decode_instr_info.imm; // Might require shifting
                    end else if (decode_instr_info.opcode == S_ADDI_FIX ) begin
                        // S_ADDI_FIX
                        rs1             <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                        rs2             <= decode_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                        rd              <= decode_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
                        fps1            <= {FP_OPERAND_WIDTH{1'b0}};
                        fps2            <= {FP_OPERAND_WIDTH{1'b0}};
                        fpd             <= {FP_OPERAND_WIDTH{1'b0}};
                        imm             <= {{IMM_WIDTH - FIXED_OPERAND_WIDTH {1'b0}}, decode_instr_info.imm[FIXED_OPERAND_WIDTH:0]}; // Might require shifting
                    end else begin
                        // FIXED
                        rs1             <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                        rs2             <= decode_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                        rd              <= decode_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
                        fps1            <= {FP_OPERAND_WIDTH{1'b0}};
                        fps2            <= {FP_OPERAND_WIDTH{1'b0}};
                        fpd             <= {FP_OPERAND_WIDTH{1'b0}};
                        imm             <= decode_instr_info.imm; // Might require shifting
                    end
                end

                C : begin
                    assigned_op_bundle.m_op            <= STALL_M;
                    assigned_op_bundle.v_ele_op        <= STALL_V_ELEMENT;
                    assigned_op_bundle.v_reduct_op     <= STALL_V_REDUCT;
                    assigned_op_bundle.s_fp_op         <= STALL_S_FP;
                    assigned_op_bundle.s_fixed_op      <= COMP_ADDR;
                    assigned_op_bundle.h_op            <= STALL_H;

                    if (decode_instr_info.opcode == C_SET_ADDR_REG) begin
                        assigned_op_bundle.c_op <= SET_ADDR_REG;
                    end
                    assigned_op_bundle.c_op <=  (decode_instr_info.opcode == C_SET_ADDR_REG)    ? SET_ADDR_REG :
                                                (decode_instr_info.opcode == C_SET_M_OFFSET)    ? SET_M_OFFSET :
                                                (decode_instr_info.opcode == C_SET_LUT)         ? SET_LUT : STALL_C; 

                    rs1             <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                    rs2             <= decode_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                    rd              <= decode_instr_info.rd [FIXED_OPERAND_WIDTH - 1 : 0];
                    fps1            <= {FP_OPERAND_WIDTH{1'b0}};
                    fps2            <= {FP_OPERAND_WIDTH{1'b0}};
                    fpd             <= {FP_OPERAND_WIDTH{1'b0}};
                    imm             <= {IMM_WIDTH{1'b0}};
                end

                H : begin
                    assigned_op_bundle.m_op            <= STALL_M;
                    assigned_op_bundle.v_ele_op        <= STALL_V_ELEMENT;
                    assigned_op_bundle.v_reduct_op     <= STALL_V_REDUCT;
                    assigned_op_bundle.s_fp_op         <= STALL_S_FP;
                    assigned_op_bundle.s_fixed_op      <= COMP_ADDR_2;
                    assigned_op_bundle.c_op            <= STALL_C;
                    assigned_op_bundle.h_op <=  (decode_instr_info.opcode == H_PREFETCH_M)    ? PREFETCH_M :
                                                (decode_instr_info.opcode == H_PREFETCH_V)    ? PREFETCH_V :
                                                (decode_instr_info.opcode == H_STORE_V)       ? STORE_V : STALL_H;



                    rs1             <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                    rs2             <= decode_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                    rd              <= decode_instr_info.rd [FIXED_OPERAND_WIDTH - 1 : 0];
                    fps1            <= {FP_OPERAND_WIDTH{1'b0}};
                    fps2            <= {FP_OPERAND_WIDTH{1'b0}};
                    fpd             <= {FP_OPERAND_WIDTH{1'b0}};
                    imm             <= {IMM_WIDTH{1'b0}};
                end

                default: begin
                    assigned_op_bundle.m_op            <= STALL_M;
                    assigned_op_bundle.v_ele_op        <= STALL_V_ELEMENT;
                    assigned_op_bundle.v_reduct_op     <= STALL_V_REDUCT;
                    assigned_op_bundle.s_fp_op         <= STALL_S_FP;
                    assigned_op_bundle.s_fixed_op      <= STALL_S_FIXED;
                    assigned_op_bundle.c_op            <= STALL_C;
                    assigned_op_bundle.h_op            <= STALL_H;

                    rs1             <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                    rs2             <= decode_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                    rd              <= decode_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
                    fps1            <= {FP_OPERAND_WIDTH{1'b0}};
                    fps2            <= {FP_OPERAND_WIDTH{1'b0}};
                    fpd             <= {FP_OPERAND_WIDTH{1'b0}};
                    imm             <= {IMM_WIDTH{1'b0}};
                end
            endcase
        end    
    end

    // Trace Registers in execution and decide on the pipeline stalls.


    // typedef struct packed {
    //     logic [FIXED_OPERAND_WIDTH - 1 : 0] operand_idx;
    //     logic valid;
    // } write_reg_tracked_content;
    
    
    // logic [FIXED_OPERAND_WIDTH - 1 : 0] tracked_write_fixed_reg [MAX_PIPELINE_STAGE - 1: 0];
    
    // always_ff @(posedge clk) begin
    //     if (!pipeline_stall) begin
    //         for (int i = 0; i < MAX_PIPELINE_STAGE; i++) begin
    //             tracked_write_fixed_reg[i] <= tracked_write_fixed_reg[i];
    //         end
    //     end 
    // end


endmodule