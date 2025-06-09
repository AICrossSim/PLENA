`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Decoder
Timing      : Sequential One Cycle
Description :
    Assuming the Instruction Format is as follows:
    [RS2]  [RS1] [RD] [OPCODE_WID]   
    [IMM2] [RS1] [RD] [OPCODE_WID]
    [IMM]        [RD] [OPCODE_WID]
*/

module decoder #(
    parameter INSTRUCTION_LENGTH = 16,
    parameter OPERAND_WIDTH = 5,
    parameter OPCODE_WIDTH = 4,
    parameter IMM_WIDTH = 32,
    parameter INST_BUFF_DEPTH = 8
)(
    input   logic clk,
    input   logic rst,
    
    // Decoder Control
    input   logic pipeline_stall,

    // Instruction Fetching
    input   logic [INSTRUCTION_LENGTH - 1 : 0] instruction,
    input   logic instruction_valid,
    output  logic instruction_ready,

    // Decoded Instruction
    output      OP_BUNDLE       decode_stage_op,
    output      S_FIXED_OP      exe_fixed_op,

    output      logic [FIXED_OPERAND_WIDTH - 1 : 0] rs1,
    output      logic [FIXED_OPERAND_WIDTH - 1 : 0] rs2,
    output      logic [FIXED_OPERAND_WIDTH - 1 : 0] rd,
    output      logic [IMM_WIDTH - 1 : 0] imm
);


logic   stall_for_read_rd;
logic [INSTRUCTION_LENGTH - 1 : 0] loaded_instr;
logic   read_instr_from_fifo, decode_instr_valid;
assign  read_instr_from_fifo = !pipeline_stall & !stall_for_read_rd & decode_instr_valid;
OP_BUNDLE       recorded_op_bundle;
// Note: When the buffer is empty, there is one last instruction in the buffer
fifo #(
    .DATA_WIDTH(INSTRUCTION_LENGTH), 
    .DEPTH(INST_BUFF_DEPTH)
) fifo_inst (
    .clk(clk),
    .rst(rst),
    .data_in        (instruction),
    .data_in_valid  (instruction_valid),
    .data_in_ready  (instruction_ready),
    .data_out       (loaded_instr),
    .data_out_valid (decode_instr_valid),
    .data_out_ready (read_instr_from_fifo)
);


// Operand Assignments
logic [OPCODE_WIDTH - 1 : 0]    loaded_opcode;
logic [OPERAND_WIDTH:0]         loaded_rs1;
logic [OPERAND_WIDTH:0]         loaded_rs2;
logic [OPERAND_WIDTH:0]         loaded_rd;
logic [IMM_WIDTH - 1 : 0]       loaded_imm;



assign loaded_imm       = ((loaded_opcode == S_ADDI_FIX) || (loaded_opcode == S_LD_FP)  || (loaded_opcode == S_ST_FP)
                                                         || (loaded_opcode == S_LD_FIX) || (loaded_opcode == S_ST_FIX) ) ? 
                                                         {{(IMM_WIDTH - IMM_2_WIDTH){1'b0}} , loaded_instr[INSTRUCTION_LENGTH - 1 -: IMM_2_WIDTH]} :
                                                         loaded_instr[INSTRUCTION_LENGTH - 1 -: IMM_WIDTH];
assign loaded_rs2       = loaded_instr[INSTRUCTION_LENGTH - 2 -: OPERAND_WIDTH];
assign loaded_rs1       = loaded_instr[(INSTRUCTION_LENGTH - OPERAND_WIDTH - 2) -: OPERAND_WIDTH];
assign loaded_rd        = loaded_instr[(INSTRUCTION_LENGTH - 2 * OPERAND_WIDTH - 2) -: OPERAND_WIDTH];
assign loaded_opcode    = loaded_instr[OPCODE_WIDTH - 1 : 0];

CUSTOM_ISA_TYPE decode_instruction_type;
INSTR_INFO decode_instr_info;

always_comb begin
    case (loaded_opcode)
        // Matrix Operations
        M_BMM, M_BMM_O, M_TMM, M_TMM_O, M_MV, M_MV_O, M_TMV, M_TMV_O: begin
            decode_instruction_type = M;
        end

        // Vector Operations
        V_ADD_VV, V_ADD_VF, V_SUB_VV, V_SUB_VF, V_MUL_VV, V_MUL_VF, V_EXP_VV, V_LD_F, V_RED_SUM, V_RED_MAX : begin
            decode_instruction_type = V;
        end

        // Scalar FIX Operations
        S_ADD_FIX, S_ADDI_FIX, S_SUB_FIX, S_MUL_FIX, S_DIV_FIX, S_LUI_FIX, S_MV_FIX, S_LD_FIX, S_ST_FIX: begin
            decode_instruction_type = S_FIX;
        end

        // Scalar FP Operations
        S_ADD_FP, S_SUB_FP, S_MAX_FP, S_MUL_FP, S_EXP_FP, S_RECI_FP, S_SQRT_FP, S_LD_FP, S_ST_FP, S_MV_FP: begin
            decode_instruction_type = S_FP;
        end

        // Memory Operations
        H_PREFETCH_M, H_PREFETCH_V, H_STORE_V: begin
            decode_instruction_type = H;
        end

        // CSR Setting
        C_SET_ADDR_REG, C_SET_M_OFFSET, C_SET_LUT: begin
            decode_instruction_type = C;
        end

        default: begin
            decode_instruction_type = INVALID_TYPE;
        end

    endcase
end

assign decode_instr_info = read_instr_from_fifo ? '{opcode: loaded_opcode, rs1: loaded_rs1, rs2: loaded_rs2, rd: loaded_rd, imm: loaded_imm, instruction_type: decode_instruction_type} : '{opcode: '0, rs1: '0, rs2: '0, rd: '0, imm: '0, instruction_type: INVALID_TYPE};


// Decoding
logic rd_operand_ready; // The stall is for loading the third operand from the register files.
logic m_update_waddr, v_update_waddr;
logic recorded_m_update_waddr, recorded_v_update_waddr;
logic pass_m_update_waddr, pass_v_update_waddr;
logic [FIXED_OPERAND_WIDTH - 1 : 0] rd_to_load;
logic [FIXED_OPERAND_WIDTH - 1 : 0] recorded_rd_to_load;
logic [FIXED_OPERAND_WIDTH - 1 : 0] pass_rd_to_load;

logic stall_for_read_rd_flag;
logic recorded_stall_for_read_rd_flag;

always_ff @(posedge clk or posedge rst) begin
    if (rst) begin
        recorded_stall_for_read_rd_flag <= 1'b0;
        recorded_m_update_waddr <= 1'b0;
        recorded_v_update_waddr <= 1'b0;
        recorded_rd_to_load <= {FIXED_OPERAND_WIDTH{1'b0}};
    end else begin
        recorded_stall_for_read_rd_flag <= stall_for_read_rd_flag;
        recorded_m_update_waddr <= m_update_waddr;
        recorded_v_update_waddr <= v_update_waddr;
        recorded_rd_to_load <= rd_to_load;


    end
end

always_comb begin
    // Instructions that requires three operands. Insert additionally operation to load the third operand, the insertion takes place only when the pipeline is not stalled.
    if (pipeline_stall & recorded_stall_for_read_rd_flag) begin
        stall_for_read_rd   = 1'b1;
    end else if (rd_operand_ready == 1'b0 & (decode_stage_op.m_op == M_BMM_O || decode_stage_op.m_op == M_TMM_O || decode_stage_op.m_op == M_MV_O || decode_stage_op.m_op == M_TMV_O)) begin
        m_update_waddr          = 1'b1;
        v_update_waddr          = 1'b0;
        stall_for_read_rd_flag  = 1'b1;
        rd_to_load              = rd;
    end else if (rd_operand_ready == 1'b0 & (decode_stage_op.v_ele_op != STALL_V_ELEMENT)) begin
        m_update_waddr          = 1'b0;
        v_update_waddr          = 1'b1;
        stall_for_read_rd_flag  = 1'b1;
        rd_to_load              = rd;
    end else begin
        m_update_waddr          = 1'b0;
        v_update_waddr          = 1'b0;
        stall_for_read_rd_flag  = 1'b0;
        rd_to_load              = {FIXED_OPERAND_WIDTH{1'b0}};
    end

    if (!pipeline_stall & !recorded_stall_for_read_rd_flag) begin
        stall_for_read_rd = stall_for_read_rd_flag;
        pass_m_update_waddr = m_update_waddr;
        pass_v_update_waddr = v_update_waddr;
        pass_rd_to_load = rd_to_load;
    end else if (!pipeline_stall & recorded_stall_for_read_rd_flag) begin
        stall_for_read_rd = 1'b1;
        pass_m_update_waddr = recorded_m_update_waddr;
        pass_v_update_waddr = recorded_v_update_waddr;
        pass_rd_to_load = recorded_rd_to_load;
    end else begin
        stall_for_read_rd = 1'b0;
        pass_m_update_waddr = 1'b0;
        pass_v_update_waddr = 1'b0;
        pass_rd_to_load = {FIXED_OPERAND_WIDTH{1'b0}};
    end
end


always_ff @(posedge clk) begin
    if (stall_for_read_rd) begin
        // Stall Condition 1: When the three oprands both pointer for addresses, need 2 cycles to obtain the address for the two port regfile.
        rd_operand_ready <= 1'b1;
        decode_stage_op.m_op            <= STALL_M;
        decode_stage_op.v_ele_op        <= STALL_V_ELEMENT;
        decode_stage_op.v_reduct_op     <= STALL_V_REDUCT;
        decode_stage_op.s_fp_op         <= STALL_S_FP;
        exe_fixed_op                      <= PASS_ADDR_2;
        decode_stage_op.c_op            <= STALL_C;
        decode_stage_op.h_op            <= STALL_H;
        decode_stage_op.m_transposed_read   <= 1'b0;
        decode_stage_op.v_broadcast_en  <= 1'b0;
        decode_stage_op.fps1            <= 'b0;
        decode_stage_op.fps2            <= 'b0;
        decode_stage_op.fpd             <= 'b0;
        decode_stage_op.fixed_rs1       <= 'b0;
        decode_stage_op.fixed_rs2       <= 'b0;
        decode_stage_op.fixed_rd        <= 'b0;
        decode_stage_op.update_m_waddr  <= pass_m_update_waddr;
        decode_stage_op.update_v_waddr  <= pass_v_update_waddr;
        
        rs1                               <= 'b0;
        rs2                               <= 'b0;
        rd                                <= pass_rd_to_load;
        imm                               <= 'b0;
    end else begin
        rd_operand_ready <= 1'b0;
        decode_stage_op.m_transposed_read     <= (decode_instr_info.opcode == M_TMV || decode_instr_info.opcode == M_TMV_O || decode_instr_info.opcode == M_TMM || decode_instr_info.opcode == M_TMM_O) ? 1'b1 : 1'b0;
        decode_stage_op.v_broadcast_en        <= (decode_instr_info.opcode == V_ADD_VF || decode_instr_info.opcode == V_SUB_VF || decode_instr_info.opcode == V_MUL_VF || decode_instr_info.opcode == V_LD_F) ? 1'b1 : 1'b0;
        decode_stage_op.update_m_waddr        <= 1'b0;
        decode_stage_op.update_v_waddr        <= 1'b0;
        decode_stage_op.fixed_rs1             <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
        decode_stage_op.fixed_rs2             <= decode_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
        decode_stage_op.fixed_rd              <= decode_instr_info.rd [FIXED_OPERAND_WIDTH - 1 : 0];

        case(decode_instr_info.instruction_type)
            M: begin
                decode_stage_op.m_op          <=  (decode_instr_info.opcode == M_BMM  || decode_instr_info.opcode == M_TMM)       ? MM   :
                                                    (decode_instr_info.opcode == M_BMM_O || decode_instr_info.opcode == M_TMM_O)    ? MM_O :
                                                    (decode_instr_info.opcode == M_MV   || decode_instr_info.opcode == M_TMV)       ? MV   :
                                                    (decode_instr_info.opcode == M_MV_O || decode_instr_info.opcode == M_TMV_O)     ? MV_O : STALL_M;
                decode_stage_op.v_ele_op      <= STALL_V_ELEMENT;
                decode_stage_op.v_reduct_op   <= STALL_V_REDUCT;
                decode_stage_op.s_fp_op       <= STALL_S_FP;
                exe_fixed_op                    <= PASS_ADDR;
                decode_stage_op.c_op          <= STALL_C;
                decode_stage_op.h_op          <= STALL_H;
                decode_stage_op.fps1          <= 'b0;
                decode_stage_op.fps2          <= 'b0;
                decode_stage_op.fpd           <= 'b0;
                rs1                             <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                rs2                             <= decode_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                rd                              <= decode_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
                imm     <= 'b0;
            end

            V: begin
                decode_stage_op.m_op <= STALL_M;
                decode_stage_op.v_ele_op <=   (decode_instr_info.opcode == V_ADD_VV || decode_instr_info.opcode == V_ADD_VF) ? ADD_V_ELEMENT :
                                                (decode_instr_info.opcode == V_SUB_VV || decode_instr_info.opcode == V_SUB_VF) ? SUB_V_ELEMENT :
                                                (decode_instr_info.opcode == V_MUL_VV || decode_instr_info.opcode == V_MUL_VF) ? MUL_V_ELEMENT :
                                                (decode_instr_info.opcode == V_EXP_VV)                                         ? EXP_V_ELEMENT : 
                                                (decode_instr_info.opcode == V_LD_F)                                           ? LD_V_ELEMENT  : STALL_V_ELEMENT;

                decode_stage_op.v_reduct_op <=    (decode_instr_info.opcode == V_RED_SUM)   ? SUM_V_REDUCT :
                                                    (decode_instr_info.opcode == V_RED_MAX)   ? MAX_V_REDUCT : STALL_V_REDUCT;
                
                exe_fixed_op                      <= PASS_ADDR;
                decode_stage_op.c_op            <= STALL_C;
                decode_stage_op.h_op            <= STALL_H;
                if (decode_instr_info.opcode == V_ADD_VF || decode_instr_info.opcode == V_SUB_VF || decode_instr_info.opcode == V_MUL_VF) begin
                    decode_stage_op.s_fp_op           <= LD_OUT_FP;
                    decode_stage_op.fps1              <= 'b0;
                    decode_stage_op.fps2              <= decode_instr_info.rs2[FP_OPERAND_WIDTH - 1 : 0];
                    decode_stage_op.fpd               <= 'b0;
                    rs1                                 <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                    rs2                                 <= {FIXED_OPERAND_WIDTH{1'b0}};
                    rd                                  <= decode_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
                    imm                                 <= {IMM_WIDTH{1'b0}};
                end else if (decode_instr_info.opcode == V_LD_F) begin
                    decode_stage_op.s_fp_op           <= LD_OUT_FP;
                    decode_stage_op.fps1              <= 'b0;
                    decode_stage_op.fps2              <= decode_instr_info.rs2[FP_OPERAND_WIDTH - 1 : 0];
                    decode_stage_op.fpd               <= 'b0;
                    rs1                                 <= {FIXED_OPERAND_WIDTH{1'b0}};
                    rs2                                 <= {FIXED_OPERAND_WIDTH{1'b0}};
                    rd                                  <= decode_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
                    imm                                 <= {IMM_WIDTH{1'b0}};
                end else if (decode_instr_info.opcode == V_RED_SUM || decode_instr_info.opcode == V_RED_MAX) begin
                    decode_stage_op.s_fp_op           <= LD_OUT_FP;
                    decode_stage_op.fps1              <= 'b0;
                    decode_stage_op.fps2              <= decode_instr_info.rd[FP_OPERAND_WIDTH - 1 : 0];
                    decode_stage_op.fpd               <= 'b0;
                    rs1                                 <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                    rs2                                 <= decode_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                    rd                                  <= {FP_OPERAND_WIDTH{1'b0}};
                    imm                                 <= {IMM_WIDTH{1'b0}};
                end else begin
                    decode_stage_op.s_fp_op           <= STALL_S_FP;
                    decode_stage_op.fps1              <= 'b0;
                    decode_stage_op.fps2              <= 'b0;
                    decode_stage_op.fpd               <= 'b0;
                    rs1                                 <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                    rs2                                 <= decode_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                    rd                                  <= decode_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
                    imm                                 <= {IMM_WIDTH{1'b0}};
                end
            end

            S_FIX: begin
                decode_stage_op.m_op            <= STALL_M;
                decode_stage_op.v_ele_op        <= STALL_V_ELEMENT;
                decode_stage_op.v_reduct_op     <= STALL_V_REDUCT;
                decode_stage_op.s_fp_op         <= STALL_S_FP;
                exe_fixed_op                      <=    (decode_instr_info.opcode == S_ADD_FIX)   ? ADD_FIX   :
                                                        (decode_instr_info.opcode == S_ADDI_FIX)  ? ADDI_FIX  :
                                                        (decode_instr_info.opcode == S_SUB_FIX)   ? SUB_FIX   : 
                                                        (decode_instr_info.opcode == S_MUL_FIX)   ? MUL_FIX   : 
                                                        (decode_instr_info.opcode == S_DIV_FIX)   ? DIV_FIX   :
                                                        (decode_instr_info.opcode == S_LUI_FIX)   ? LUI_FIX   :
                                                        (decode_instr_info.opcode == S_MV_FIX)    ? MV_FIX    : 
                                                        (decode_instr_info.opcode == S_LD_FIX)    ? LD_FIX    :
                                                        (decode_instr_info.opcode == S_ST_FIX)    ? ST_FIX    : STALL_S_FIXED;
                decode_stage_op.c_op            <= STALL_C;
                decode_stage_op.h_op            <= STALL_H;
                if (decode_instr_info.opcode == S_ADDI_FIX ) begin
                    // S_ADDI_FIX
                    decode_stage_op.fps1            <= 'b0;
                    decode_stage_op.fps2            <= 'b0;
                    decode_stage_op.fpd             <= 'b0;
                    rs1             <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                    rs2             <= {FIXED_OPERAND_WIDTH{1'b0}};
                    rd              <= decode_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
                    imm             <= {{IMM_WIDTH - IMM_2_WIDTH {1'b0}}, decode_instr_info.imm[IMM_2_WIDTH:0]}; 
                end else begin
                    // Other FIXED Instructions
                    decode_stage_op.fps1            <= 'b0;
                    decode_stage_op.fps2            <= 'b0;
                    decode_stage_op.fpd             <= 'b0;
                    rs1             <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                    rs2             <= decode_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                    rd              <= decode_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
                    imm             <= decode_instr_info.imm; // Might require shifting
                end
            end

            S_FP: begin
                decode_stage_op.m_op            <= STALL_M;
                decode_stage_op.v_ele_op        <= STALL_V_ELEMENT;
                decode_stage_op.v_reduct_op     <= STALL_V_REDUCT;
                decode_stage_op.s_fp_op         <=   (decode_instr_info.opcode == S_ADD_FP )   ? ADD_FP    :
                                                        (decode_instr_info.opcode == S_SUB_FP )   ? SUB_FP    :
                                                        (decode_instr_info.opcode == S_MAX_FP )   ? MAX_FP    :
                                                        (decode_instr_info.opcode == S_MUL_FP )   ? MUL_FP    :
                                                        (decode_instr_info.opcode == S_EXP_FP )   ? EXP_FP    :
                                                        (decode_instr_info.opcode == S_RECI_FP)   ? RECI_FP   :
                                                        (decode_instr_info.opcode == S_SQRT_FP)   ? SQRT_FP   :
                                                        (decode_instr_info.opcode == S_MV_FP)     ? MV_FP     :
                                                        (decode_instr_info.opcode == S_LD_FP)     ? LD_REG_FP :
                                                        (decode_instr_info.opcode == S_ST_FP)     ? ST_REG_FP : STALL_S_FP;
                
                decode_stage_op.c_op              <= STALL_C;
                decode_stage_op.h_op              <= STALL_H;
                if (decode_instr_info.opcode == S_ADD_FP || decode_instr_info.opcode == S_SUB_FP || decode_instr_info.opcode == S_MAX_FP || decode_instr_info.opcode == S_MUL_FP) begin
                    // Two FP source operands and one FP destination operand
                    exe_fixed_op                    <= STALL_S_FIXED;
                    decode_stage_op.fps1          <= decode_instr_info.rs1[FP_OPERAND_WIDTH - 1 : 0];
                    decode_stage_op.fps2          <= decode_instr_info.rs2[FP_OPERAND_WIDTH - 1 : 0];
                    decode_stage_op.fpd           <= decode_instr_info.rd[FP_OPERAND_WIDTH - 1 : 0];
                    rs1                             <= {FIXED_OPERAND_WIDTH{1'b0}};
                    rs2                             <= {FIXED_OPERAND_WIDTH{1'b0}};
                    rd                              <= {FIXED_OPERAND_WIDTH{1'b0}};
                    imm                             <= {IMM_WIDTH{1'b0}};
                end else if (decode_instr_info.opcode == S_EXP_FP || decode_instr_info.opcode == S_RECI_FP || decode_instr_info.opcode == S_SQRT_FP || decode_instr_info.opcode == S_MV_FP) begin
                    // Single FP source operand and single FP destination operand
                    exe_fixed_op                    <= STALL_S_FIXED;
                    decode_stage_op.fps1          <= decode_instr_info.rs1[FP_OPERAND_WIDTH - 1 : 0];
                    decode_stage_op.fps2          <= {FP_OPERAND_WIDTH{1'b0}};
                    decode_stage_op.fpd           <= decode_instr_info.rd[FP_OPERAND_WIDTH - 1 : 0];
                    rs1                             <= {FIXED_OPERAND_WIDTH{1'b0}};
                    rs2                             <= {FIXED_OPERAND_WIDTH{1'b0}};
                    rd                              <= {FIXED_OPERAND_WIDTH{1'b0}};
                    imm                             <= {IMM_WIDTH{1'b0}};
                end else if (decode_instr_info.opcode == S_LD_FP || decode_instr_info.opcode == S_ST_FP) begin
                    // Single FIXED Source operand (Storing Addr) and one IMM and one FP destination operand
                    exe_fixed_op                    <= COMP_ADDR;
                    decode_stage_op.fps1          <= {FP_OPERAND_WIDTH{1'b0}};
                    decode_stage_op.fps2          <= {FP_OPERAND_WIDTH{1'b0}};
                    decode_stage_op.fpd           <= decode_instr_info.rd[FP_OPERAND_WIDTH - 1 : 0];
                    rs1                             <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                    rs2                             <= {FIXED_OPERAND_WIDTH{1'b0}};
                    rd                              <= {FIXED_OPERAND_WIDTH{1'b0}};
                    imm                             <= decode_instr_info.imm; // Might require shifting
                end else begin
                    // Not Defined 
                    exe_fixed_op                    <= STALL_S_FIXED;
                    decode_stage_op.fps1          <= {FP_OPERAND_WIDTH{1'b0}};
                    decode_stage_op.fps2          <= {FP_OPERAND_WIDTH{1'b0}};
                    decode_stage_op.fpd           <= decode_instr_info.rd[FP_OPERAND_WIDTH - 1 : 0];
                    rs1                             <= {FIXED_OPERAND_WIDTH{1'b0}};
                    rs2                             <= {FIXED_OPERAND_WIDTH{1'b0}};
                    rd                              <= {FIXED_OPERAND_WIDTH{1'b0}};
                    imm                             <= {IMM_WIDTH{1'b0}};
                end
            end



            C : begin
                decode_stage_op.m_op            <= STALL_M;
                decode_stage_op.v_ele_op        <= STALL_V_ELEMENT;
                decode_stage_op.v_reduct_op     <= STALL_V_REDUCT;
                decode_stage_op.s_fp_op         <= STALL_S_FP;
                
                decode_stage_op.h_op            <= STALL_H;
                if(decode_instr_info.opcode == C_SET_ADDR_REG) begin
                    exe_fixed_op                    <= PASS_ADDR;
                    decode_stage_op.c_op            <= SET_ADDR_REG;
                end else if (decode_instr_info.opcode == C_SET_M_OFFSET) begin
                    exe_fixed_op                    <= PASS_ADDR_2;
                    decode_stage_op.c_op            <= SET_M_OFFSET;
                end else if (decode_instr_info.opcode == C_SET_LUT) begin
                    exe_fixed_op                    <= STALL_S_FIXED;
                    decode_stage_op.c_op            <= SET_LUT; // TODO: Left for Cano
                end else begin
                    exe_fixed_op                    <= STALL_S_FIXED;
                    decode_stage_op.c_op            <= STALL_C;
                end
                decode_stage_op.fps1              <= 'b0;
                decode_stage_op.fps2              <= 'b0;
                decode_stage_op.fpd               <= 'b0;
                rs1             <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                rs2             <= decode_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                rd              <= decode_instr_info.rd [FIXED_OPERAND_WIDTH - 1 : 0];
                imm             <= {IMM_WIDTH{1'b0}};
            end

            H : begin
                decode_stage_op.m_op            <= STALL_M;
                decode_stage_op.v_ele_op        <= STALL_V_ELEMENT;
                decode_stage_op.v_reduct_op     <= STALL_V_REDUCT;
                decode_stage_op.s_fp_op         <= STALL_S_FP;
                exe_fixed_op                      <= PASS_ADDR_2;
                decode_stage_op.c_op            <= STALL_C;
                decode_stage_op.h_op <=   (decode_instr_info.opcode == H_PREFETCH_M)      ? PREFETCH_M    :
                                            (decode_instr_info.opcode == H_PREFETCH_V)      ? PREFETCH_V    :
                                            (decode_instr_info.opcode == H_STORE_V)         ? STORE_V       : STALL_H;
                decode_stage_op.fps1              <= 'b0;
                decode_stage_op.fps2              <= 'b0;
                decode_stage_op.fpd               <= 'b0;
                rs1             <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                rs2             <= decode_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                rd              <= decode_instr_info.rd [FIXED_OPERAND_WIDTH - 1 : 0];
                imm             <= {IMM_WIDTH{1'b0}};
            end

            default: begin
                decode_stage_op.m_op              <= STALL_M;
                decode_stage_op.v_ele_op          <= STALL_V_ELEMENT;
                decode_stage_op.v_reduct_op       <= STALL_V_REDUCT;
                decode_stage_op.s_fp_op           <= STALL_S_FP;
                exe_fixed_op                        <= STALL_S_FIXED;
                decode_stage_op.c_op              <= STALL_C;
                decode_stage_op.h_op              <= STALL_H;
                
                decode_stage_op.fps1              <= 'b0;
                decode_stage_op.fps2              <= 'b0;
                decode_stage_op.fpd               <= 'b0;
                rs1             <= decode_instr_info.rs1[FIXED_OPERAND_WIDTH - 1 : 0];
                rs2             <= decode_instr_info.rs2[FIXED_OPERAND_WIDTH - 1 : 0];
                rd              <= decode_instr_info.rd[FIXED_OPERAND_WIDTH - 1 : 0];
                imm             <= {IMM_WIDTH{1'b0}};
            end
        endcase
    end 
end

endmodule