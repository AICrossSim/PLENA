`timescale 1ns / 1ps
`include "operation.svh"
`include "configuration.svh"

/*
Module      : Pipeline Control
Timing      : Combinatorial
Description : This module monitors the execution stages of each module and decide whether the pipeline is stalled or not. 
            : This module will also control the overall execution of the coprocessor.
            ：Note: The pipeline stages are listed as follows:
            Control Flow Decode - > Register Read -> Check Address Dependencies -> Determine Stall -> Data Preparation -> Execute -> Write Back
            For Vect/Matrix     | Decode | Register Rd  | Check      | Determine Stall | Data Prep | Execute | Write Back |
            For FP Scalar       | Decode | Decision     | Execute    | Write Back |
            For Fixed Scalar    | Decode | Execute      | Write Back |
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
    input       OP_BUNDLE       decode_stage_op,

    // Address
    input       logic [FIXED_DATA_WIDTH - 1 : 0] fixed_addr_1,
    input       logic [FIXED_DATA_WIDTH - 1 : 0] fixed_addr_2,

    // Memory Monitor
    input       logic v_sram_wen_a,
    input       logic [FIXED_DATA_WIDTH - 1 : 0]    v_sram_addr_a,
    input       logic v_sram_wen_b,
    input       logic [FIXED_DATA_WIDTH - 1 : 0]    v_sram_addr_b,
    input       logic hbm_m_prefetch_in_progress,
    input       logic hbm_v_prefetch_in_progress,

    // Execution Monitor
    input       MEM_WREQ_INFO   mem_write_req,
    input       logic           hbm_in_used,            
    input       logic           fp_stall_req,
    input       logic           fixed_stall_req,
    input       logic           m_load_in_process,
    input       logic           v_load_in_process,
    input       logic           sfu_in_use,
    input       logic           m_complete_acc_writeback,

    // Current control operation
    output      logic           pipeline_stall_req,
    output      OP_BUNDLE       exe_stage_op,
    output      MEM_WEN_INFO    mem_write_control
);

    // Operation Control Decalration
    OP_BUNDLE   reg_rd_stage_op, check_stage_op, determine_stage_op, delayed_reg_rd_stage_op, invalid_op_bubble, recorded_check_stage_op;
    assign invalid_op_bubble = '{
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
        fixed_rs1           : '0,
        fixed_rs2           : '0,
        fixed_rd            : '0,
        addr_1              : '0,
        addr_2              : '0,
        update_m_waddr      : 1'b0,
        update_v_waddr      : 1'b0
    };

    import pipeline_pkg::*;
    logic pipeline_stall;
    logic stall_for_prefetch;


    logic m_accumulate_in_progress; // Flag to indicate if the accumulation in matrix machine is in progress.

    // Decision for pipeline stall
    always_comb begin
        if (hbm_m_prefetch_in_progress & ( determine_stage_op.h_op == PREFETCH_M)) begin
            // Condition 1: When prefetching instruction is in processed, another prefetching instruction is not allowed.
            pipeline_stall   = 1'b1;            
        end else if (hbm_v_prefetch_in_progress & (determine_stage_op.h_op == PREFETCH_V)) begin
            // Condition 1: When prefetching instruction is in processed, another prefetching instruction is not allowed.
            pipeline_stall   = 1'b1;            
        end else if ((m_load_in_process | m_accumulate_in_progress) & (determine_stage_op.m_op != STALL_M)) begin
            // Condition 2: When prefetching instruction is in processed or matrix at the loading stage / writing back, another matrix-related instruction is not allowed.
            pipeline_stall   = 1'b1;            
        end else if ((v_load_in_process) & ( determine_stage_op.v_ele_op != STALL_V_ELEMENT || determine_stage_op.v_reduct_op != STALL_V_REDUCT)) begin
            // Condition 3: When prefetching instruction is in processed or vector at the loading stage, another vector-related instruction is not allowed.
            pipeline_stall   = 1'b1;            
        end  else if (mem_write_req.wreq_s_sram_port_a & (determine_stage_op.v_ele_op != STALL_V_ELEMENT || determine_stage_op.v_reduct_op != STALL_V_REDUCT || determine_stage_op.m_op != STALL_M)) begin
            // Condition 4: Trying to access the vector sram port A while it is being written to.
            pipeline_stall   = 1'b1;            
        end else if (mem_write_req.wreq_s_sram_port_b & ( determine_stage_op.v_ele_op != STALL_V_ELEMENT || determine_stage_op.m_op != STALL_M)) begin
            // Condition 5: Trying to access the vector sram port B while it is being written to.
            pipeline_stall   = 1'b1;            
        end else if ((mem_write_req.wreq_m_sram == 1'b1) & (determine_stage_op.m_op != STALL_M) ) begin
            // Condition 6: Trying to access the matrix sram while it is being written to.
            pipeline_stall   = 1'b1;
        end else if (fp_stall_req & (determine_stage_op.s_fp_op != STALL_S_FP)) begin
            // Condition 7: FP unit requests a stall, but the current operation is another FP operation.
            pipeline_stall   = 1'b1;            
        end else if (sfu_in_use & (determine_stage_op.s_fp_op == SQRT_FP) || (determine_stage_op.s_fp_op == RECI_FP) || (determine_stage_op.s_fp_op == EXP_FP)) begin
            // Condition 8: SFU is in use, but the current operation is a another special floating point operation.
            pipeline_stall = 1'b1;
        end else if (mem_vwrite_stall_req) begin
            // Unconditionally stall the overall pipeline.
            pipeline_stall   = 1'b1;                
        end else begin
            pipeline_stall   = 1'b0;
        end
    end

    assign pipeline_stall_req = pipeline_stall || stall_in_process; // Extra stall cycle in order to execute the previously unexecuted operation.

    // Memory Monitor
    logic           mem_vwrite_stall_req;

    addr_monitor #(
        .ADDR_WIDTH(FIXED_DATA_WIDTH),
        .PIPELINE_STAGES(MAX_PIPELINE_STAGE)
    ) addr_monitor_inst (
        .clk(clk),
        .rst(rst),
        .determine_stage_op     (determine_stage_op),
        .exe_stage_op           (exe_stage_op),
        .v_sram_addr_a          (v_sram_addr_a),
        .v_sram_addr_b          (v_sram_addr_b),
        .v_sram_wen_a           (v_sram_wen_a),
        .v_sram_wen_b           (v_sram_wen_b),
        .stall_req              (mem_vwrite_stall_req),
        .sys_pipe_stall         (stall_in_process)
    );

    // Merge the decoded op with the register read outcome.
    always_comb begin
        check_stage_op.m_op            = delayed_reg_rd_stage_op.m_op;
        check_stage_op.v_ele_op        = delayed_reg_rd_stage_op.v_ele_op;
        check_stage_op.v_reduct_op     = delayed_reg_rd_stage_op.v_reduct_op;
        check_stage_op.s_fp_op         = delayed_reg_rd_stage_op.s_fp_op;
        check_stage_op.c_op            = delayed_reg_rd_stage_op.c_op;
        check_stage_op.h_op            = delayed_reg_rd_stage_op.h_op;
        check_stage_op.m_transposed_read = delayed_reg_rd_stage_op.m_transposed_read;
        check_stage_op.v_broadcast_en  = delayed_reg_rd_stage_op.v_broadcast_en;
        check_stage_op.fps1            = delayed_reg_rd_stage_op.fps1;
        check_stage_op.fps2            = delayed_reg_rd_stage_op.fps2;
        check_stage_op.fpd             = delayed_reg_rd_stage_op.fpd;
        check_stage_op.fixed_rs1       = delayed_reg_rd_stage_op.fixed_rs1;
        check_stage_op.fixed_rs2       = delayed_reg_rd_stage_op.fixed_rs2;
        check_stage_op.fixed_rd        = delayed_reg_rd_stage_op.fixed_rd;
        check_stage_op.addr_1          = fixed_addr_1;
        check_stage_op.addr_2          = fixed_addr_2; 
        check_stage_op.update_m_waddr  = delayed_reg_rd_stage_op.update_m_waddr;
        check_stage_op.update_v_waddr  = delayed_reg_rd_stage_op.update_v_waddr;
    end
    logic stall_in_process, recover_from_stall, start_of_stall;
    assign recover_from_stall = (!pipeline_stall) && stall_in_process;
    assign start_of_stall = pipeline_stall && !stall_in_process;


    always_ff @(posedge clk) begin
        if (rst) begin
            mem_write_control <= '{
                w_m_sram_en         : 1'b0,
                w_s_sram_port_a_en  : 1'b0,
                w_s_sram_port_b_en  : 1'b0,
                w_from_m            : 1'b0
            };
            stall_in_process            <= 1'b0;
            m_accumulate_in_progress    <= 1'b0;

        end else begin
            
            mem_write_control <= '{
                w_m_sram_en           : mem_write_req.wreq_m_sram,
                w_s_sram_port_a_en    : mem_write_req.wreq_s_sram_port_a,
                w_s_sram_port_b_en    : mem_write_req.wreq_s_sram_port_b,
                w_from_m              : mem_write_req.wreq_from_m
            };

            if (pipeline_stall) begin
                stall_in_process <= 1'b1;
            end else begin
                stall_in_process <= 1'b0;
            end

            if (recover_from_stall) begin
                // Recover from Stall
                determine_stage_op          <= recorded_check_stage_op;
                exe_stage_op                <= determine_stage_op;
            end else if (!pipeline_stall) begin
                // Normal Execution
                reg_rd_stage_op             <= decode_stage_op;
                delayed_reg_rd_stage_op     <= reg_rd_stage_op;
                determine_stage_op          <= check_stage_op;
                exe_stage_op                <= determine_stage_op;
            end else begin
                // Stall Execution
                exe_stage_op                <= invalid_op_bubble;
            end

            if (start_of_stall) begin
                recorded_check_stage_op <= check_stage_op;
                delayed_reg_rd_stage_op <= invalid_op_bubble;
            end else if (recover_from_stall) begin
                recorded_check_stage_op <= invalid_op_bubble;
            end

            // Accumulation in progress TODO
            if (exe_stage_op.m_op == MM_WO || exe_stage_op.m_op == MV_O) begin
                m_accumulate_in_progress <= 1'b1;
            end else if(m_complete_acc_writeback) begin
                m_accumulate_in_progress <= 1'b0;
            end
            
        end
    end

endmodule