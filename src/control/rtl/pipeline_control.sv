`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Pipeline Control
Timing      : Combinatorial
Description : This module monitors the execution stages of each module and decide whether the pipeline is stalled or not. 
            : This module will also control the overall execution of the coprocessor.
*/

module pipeline_control #(
    parameter   OPERAND_WIDTH           = 5,
    parameter   FIXED_DATA_WIDTH        = 32
) (
    input       logic clk,
    input       logic rst,

    // Decoded Instruction
    input       INSTR_INFO decode_instr_info,
    input       logic decode_instr_valid,
    output      logic fetch_next_instr,

    // Execution Monitor
    input       logic memory_load_failed,
    input       logic v_write_request,            // One clock earlier than the vector output get valid.
    input       logic m_write_request,

    // Current control operation
    output      logic       pipeline_stall,
    output      OP_BUNDLE   assigned_op_bundle,
    output      logic       m_update_waddr,
    output      logic       v_update_waddr,

    output      logic       m_write_en,
    output      logic       v_write_en,

    output      logic [FIXED_DATA_WIDTH - 1 : 0] rs1,
    output      logic [FIXED_DATA_WIDTH - 1 : 0] rs2,
    output      logic [FIXED_DATA_WIDTH - 1 : 0] rd,
    output      logic [FP_OPERAND_WIDTH - 1 : 0] fps1,
    output      logic [FP_OPERAND_WIDTH - 1 : 0] fps2,
    output      logic [FP_OPERAND_WIDTH - 1 : 0] fpd,
    output      logic [IMM_WIDTH - 1 : 0] imm
);

    // Pipeline Control
 
    // Decision for pipeline stall
    always_comb begin
        // If the current decoded instruction is Memory/Vector that required access to thress operands values, stall the pipeline for single cycle to read the rd content.
        if(decode_instr_info.opcode == M_MV || decode_instr_info.opcode == M_TMV ) begin
            m_update_waddr   = 1'b1;
            v_update_waddr   = 1'b0;
            pipeline_stall  = 1'b1;
        end else if (decode_instr_info.opcode == V_ADD_VV || decode_instr_info.opcode == V_SUB_VV || decode_instr_info.opcode == V_MUL_VV) begin
            m_update_waddr   = 1'b0;
            v_update_waddr   = 1'b1;
            pipeline_stall  = 1'b1;
        end else if (memory_load_failed) begin
            m_update_waddr   = 1'b0;
            v_update_waddr   = 1'b0;
            pipeline_stall = 1'b1;
        end else begin
            m_update_waddr   = 1'b0;
            v_update_waddr   = 1'b0;
            pipeline_stall = 1'b0;
        end

    end



always_ff @(posedge clk) begin
    if (pipeline_stall) begin
        
        if (m_update_waddr || v_update_waddr) begin
            assigned_op_bundle.m_op            <= STALL_M;
            assigned_op_bundle.v_ele_op        <= STALL_V_ELEMENT;
            assigned_op_bundle.v_reduct_op     <= STALL_V_REDUCT;
            assigned_op_bundle.s_fp_op         <= STALL_S_FP;
            assigned_op_bundle.s_fixed_op      <= COMP_ADDR;

            rs1             <= rd;
            rs2             <= 'b0;
            rd              <= 'b0;
            fps1            <= 'b0;
            fps2            <= 'b0;
            fpd             <= 'b0;
            imm             <= 'b0;
        end else begin
            
        end

    end else begin

        assigned_op_bundle.m_transposed_read   <= (decode_instr_info.opcode == M_TMV || decode_instr_info.opcode == M_TMV_O) ? 1'b1 : 1'b0;
        assigned_op_bundle.v_broadcast_en      <= (decode_instr_info.opcode == V_ADD_VF || decode_instr_info.opcode == V_SUB_VF || decode_instr_info.opcode == V_MUL_VF) ? 1'b1 : 1'b0;
        
        case(decode_instr_info.opcode)
            M: begin
                assigned_op_bundle.m_op        <= (decode_instr_info.opcode == M_MV || decode_instr_info.opcode == M_TMV) ? MV : MV_O;
                assigned_op_bundle.v_ele_op    <= STALL_V_ELEMENT;
                assigned_op_bundle.v_reduct_op <= STALL_V_REDUCT;
                assigned_op_bundle.s_fp_op     <= STALL_S_FP;
                assigned_op_bundle.s_fixed_op  <= COMP_ADDR;

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
                assigned_op_bundle.s_fp_op         <=  (decode_instr_info.opcode == S_ADD_FP )   ? ADD_FP    :
                                                (decode_instr_info.opcode == S_SUB_FP )   ? SUB_FP    :
                                                (decode_instr_info.opcode == S_MUL_FP )   ? MUL_FP    :
                                                (decode_instr_info.opcode == S_EXP_FP )   ? EXP_FP    :
                                                (decode_instr_info.opcode == S_ISQRT_FP)  ? ISQRT_FP  :
                                                (decode_instr_info.opcode == S_LOG_FP  )  ? LOG_FP    : STALL_S_FP;
                
                assigned_op_bundle.s_fixed_op      <=  (decode_instr_info.opcode == S_ADD_FIX)   ? ADD_FIX   :
                                                (decode_instr_info.opcode == S_ADDI_FIX)  ? ADDI_FIX  :
                                                (decode_instr_info.opcode == S_SUB_FIX)   ? SUB_FIX   : 
                                                (decode_instr_info.opcode == S_MUL_FIX)   ? MUL_FIX   : 
                                                (decode_instr_info.opcode == S_DIV_FIX)   ? DIV_FIX   :
                                                (decode_instr_info.opcode == S_LUI_FIX)   ? LUI_FIX   :
                                                (decode_instr_info.opcode == S_MV_FIX)    ? MV_FIX    : STALL_S_FIXED;
                
                if (decode_instr_info.opcode == S_ADD_FP || decode_instr_info.opcode == S_SUB_FP || decode_instr_info.opcode == S_MUL_FP) begin
                    rs1             <= {FIXED_OPERAND_WIDTH{1'b0}};
                    rs2             <= {FIXED_OPERAND_WIDTH{1'b0}};
                    rd              <= {FIXED_OPERAND_WIDTH{1'b0}};
                    fps1            <= decode_instr_info.rs1[FP_OPERAND_WIDTH - 1 : 0];
                    fps2            <= decode_instr_info.rs2[FP_OPERAND_WIDTH - 1 : 0];
                    fpd             <= decode_instr_info.rd[FP_OPERAND_WIDTH - 1 : 0];
                    imm             <= {IMM_WIDTH{1'b0}};
                end else if (decode_instr_info.opcode == S_EXP_FP || decode_instr_info.opcode == S_ISQRT_FP || decode_instr_info.opcode == S_LOG_FP) begin
                    rs1             <= {FIXED_OPERAND_WIDTH{1'b0}};
                    rs2             <= {FIXED_OPERAND_WIDTH{1'b0}};
                    rd              <= {FIXED_OPERAND_WIDTH{1'b0}};
                    fps1            <= decode_instr_info.rs1[FP_OPERAND_WIDTH - 1 : 0];
                    fps2            <= {FP_OPERAND_WIDTH{1'b0}};
                    fpd             <= decode_instr_info.rd[FP_OPERAND_WIDTH - 1 : 0];
                    imm             <= {IMM_WIDTH{1'b0}};
                end else if ( decode_instr_info.opcode == S_ADDI_FIX) begin
                    rs1             <= decode_instr_info.rs1;
                    rs2             <= {FIXED_OPERAND_WIDTH{1'b0}};;
                    rd              <= decode_instr_info.rd;
                    fps1            <= {FP_OPERAND_WIDTH{1'b0}};
                    fps2            <= {FP_OPERAND_WIDTH{1'b0}};
                    fpd             <= {FP_OPERAND_WIDTH{1'b0}};
                    imm             <= {{(IMM_WIDTH - FIXED_OPERAND_WIDTH){1'b0}}, decode_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0]};
                end else begin
                    rs1             <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                    rs2             <= decode_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                    rd              <= decode_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
                    fps1            <= {FP_OPERAND_WIDTH{1'b0}};
                    fps2            <= {FP_OPERAND_WIDTH{1'b0}};
                    fpd             <= {FP_OPERAND_WIDTH{1'b0}};
                    imm             <= {IMM_WIDTH{1'b0}};
                end
            end

            C : begin
                assigned_op_bundle.m_op            <= STALL_M;
                assigned_op_bundle.v_ele_op        <= STALL_V_ELEMENT;
                assigned_op_bundle.v_reduct_op     <= STALL_V_REDUCT;
                assigned_op_bundle.s_fp_op         <= STALL_S_FP;
                assigned_op_bundle.s_fixed_op      <= COMP_ADDR;
                if (decode_instr_info.opcode == C_SET_ADDR_REG) begin
                    
                end

                rs1             <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                rs2             <= decode_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                rd              <= decode_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
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
                assigned_op_bundle.s_fixed_op      <= COMP_ADDR;

                rs1             <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                rs2             <= decode_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                rd              <= decode_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
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



endmodule