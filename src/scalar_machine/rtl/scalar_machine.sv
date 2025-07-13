`timescale 1ns / 1ps
`include "operation.svh"
`include "configuration.svh"
`include "precision.svh"

/*
Module      : Scalar Machine Module
Timing      : Sequential, all the operations completed in 1 cycle
Description : This module contains two modules:
            : FP ALU for all the fp computation related operations
            : Fixed ALU, only have addition and subtraction operations for address manipulation
Status      : Under Testing
*/

module scalar_machine import precision_pkg::*;  #(
    `ifdef SIMULATION
        // Simulation Purpose
        parameter string FP_MEM_INIT_FILE = "",
        parameter string FIXED_MEM_INIT_FILE = ""
    `endif
) (
    input   logic clk,
    input   logic rst,

    // Control
    input   OP_BUNDLE  exe_stage_op,
    input   S_FIXED_OP assigned_fixed_op,

    // Fixed Register Control
    input   logic [FIXED_OPERAND_WIDTH - 1 : 0] rs1,
    input   logic [FIXED_OPERAND_WIDTH - 1 : 0] rs2,
    input   logic [FIXED_OPERAND_WIDTH - 1 : 0] rd,

    // Fixed Value input
    input   logic [IMM_WIDTH - 1 : 0]           imm_in,
    output  logic [FIXED_DATA_WIDTH - 1 : 0]    fixed_out_1,
    output  logic [FIXED_DATA_WIDTH - 1 : 0]    fixed_out_2,

    // FP Value input
    input   logic [S_FP_EXP_WIDTH + S_FP_MANT_WIDTH : 0] external_fp_in,
    input   logic external_fp_in_valid,
    output  logic external_fp_in_ready,
    input   logic [FP_OPERAND_WIDTH - 1 : 0]                            external_fp_wtarget,
    output  logic [S_FP_EXP_WIDTH + S_FP_MANT_WIDTH : 0]                fp_out,
    output  logic [VLEN - 1 : 0] [S_FP_EXP_WIDTH + S_FP_MANT_WIDTH : 0] fp_vector_out,
    input   logic fp_vector_out_ready,
    output  logic fp_vector_out_valid,

    // Stall Detection
    output  logic received_v_reduct_result,
    output  logic fp_stall_req,
    output  logic fp_sram_stall_req
);

    import pipeline_pkg::*;
    import configuration_pkg::*;
    localparam FP_SRAM_ADDR_WIDTH       = $clog2(FP_SRAM_DEPTH);
    localparam FIXED_SRAM_ADDR_WIDTH    = $clog2(FIXED_SRAM_DEPTH);
    localparam VLEN_COUNTER_WIDTH       = $clog2(VLEN);

    //----------------------------//
    // FP Unit
    //----------------------------//

    S_FP_OP fp_control, exe_fp_control;
    logic [FP_OPERAND_WIDTH - 1 : 0] fp_rs1;
    logic [FP_OPERAND_WIDTH - 1 : 0] fp_rs2;
    logic [FP_OPERAND_WIDTH - 1 : 0] fp_rd, p1_fp_rd;
    logic [FP_OPERAND_WIDTH - 1 : 0] fp_reg_addr_1, fp_reg_addr_2;
    logic fp_reg_we;
    logic general_fp_operation;
    logic [S_FP_EXP_WIDTH + S_FP_MANT_WIDTH : 0] fp_reg_1, fp_reg_2, fp_alu_out, fp_sfu_out, fp_reg_wdata, fp_ld_from_sram;
    logic [FP_OPERAND_WIDTH - 1 : 0] recorded_fp_waddr_sfu, recorded_fp_waddr_alu, recorded_fp_waddr_sram;
    logic sfu_out_valid, sfu_out_ready;
    logic load_fp_sram_valid, fp_sram_req, fp_sram_wen;
    logic [VLEN_COUNTER_WIDTH : 0] acc_vec_counter;
    logic continuous_load_fp_sram;
    logic write_data_from_external_fp;
    logic fp_alu_valid;
    logic [FP_SRAM_ADDR_WIDTH - 1 : 0] fp_sram_addr, recorded_fp_sram_addr;
    logic [MLEN - 1 : 0] [S_FP_EXP_WIDTH + S_FP_MANT_WIDTH : 0] fp_vector_buffer;

    assign  fp_control = exe_stage_op.s_fp_op;

    // ------------------- Tracing Register for Stall Detection -------------------
    localparam int TRACE_SIZE = 2 << FP_OPERAND_WIDTH; // Number of FP registers
    logic [FP_OPERAND_WIDTH - 1 : 0] fp_wtarget;

    assign fp_vector_out = fp_vector_buffer;

    always_ff @(posedge clk) begin
        if (rst) begin
            exe_fp_control          <= STALL_S_FP;
            load_fp_sram_valid      <= 1'b0;
            recorded_fp_waddr_alu   <= 'b0;
            recorded_fp_waddr_sram  <= 'b0;
            p1_fp_rd                <= 'b0;
            fp_stall_req            <= 1'b0;
            fp_sram_stall_req       <= 1'b0;
            fp_vector_buffer        <= 'b0;
            continuous_load_fp_sram <= 1'b0;
            acc_vec_counter         <= 'b0;
            fp_out                  <= 'b0;
            fp_sram_addr            <= 'b0;
            fp_sram_req             <= 1'b0;
            fp_sram_wen             <= 1'b0;

        end else begin

            p1_fp_rd                <= fp_rd;
            exe_fp_control          <= fp_control;
            load_fp_sram_valid      <= (exe_fp_control == LD_REG_FP) ? 1'b1 : 1'b0;
            recorded_fp_waddr_sram  <= p1_fp_rd;
            recorded_fp_waddr_alu   <= p1_fp_rd;

            if (fp_control == RECI_FP || fp_control == EXP_FP) begin
                fp_stall_req <= 1'b1; // SFU is busy
            end else if (sfu_out_valid) begin
                fp_stall_req <= 1'b0; // SFU process completed
            end 

            if (fp_control == MAP_V_FP) begin
                continuous_load_fp_sram <= 1'b1;
                recorded_fp_sram_addr   <= exe_stage_op.addr_1[FP_SRAM_ADDR_WIDTH - 1 : 0];
                fp_sram_addr            <= exe_stage_op.addr_1[FP_SRAM_ADDR_WIDTH - 1 : 0];
                acc_vec_counter         <= 'b1;
                fp_sram_req             <= 1'b1;
                fp_sram_stall_req       <= 1'b1;
                fp_vector_out_valid     <= 1'b0;  
            end else if (acc_vec_counter == VLEN + 1) begin
                acc_vec_counter         <=  'b0;
                continuous_load_fp_sram <= 1'b0;
                fp_sram_req             <= 1'b0;
                fp_vector_buffer[acc_vec_counter - 2]   <= fp_ld_from_sram;
                fp_vector_out_valid     <= 1'b1;
            end else if (continuous_load_fp_sram) begin
                acc_vec_counter <= acc_vec_counter + 1'b1;
                fp_sram_addr    <= recorded_fp_sram_addr + acc_vec_counter;
                if (acc_vec_counter > 'b1) begin
                    fp_vector_buffer[acc_vec_counter - 2]   <= fp_ld_from_sram;
                end
                fp_sram_req                                 <= 1'b1;
            end else if (fp_vector_out_valid & fp_vector_out_ready) begin
                fp_sram_stall_req           <= 1'b0;
                fp_vector_buffer            <= 'b0;
                fp_vector_out_valid         <= 1'b0;
            end else begin
                fp_sram_addr <= exe_stage_op.addr_1[FP_SRAM_ADDR_WIDTH - 1 : 0];
                fp_sram_req  <= (fp_control == LD_REG_FP) || (fp_control == ST_REG_FP);
            end

            fp_sram_wen <= (fp_control == ST_REG_FP);

            // Loading fp reg data out.
            if (exe_fp_control == LD_OUT_FP) begin
                if (fp_reg_addr_2 == fp_wtarget) begin
                    // Forwarding
                    fp_out <= fp_reg_wdata;
                end else begin
                    fp_out <= fp_reg_2;
                end
            end else begin
                fp_out <= 'b0;
            end
        end
    end

    /*
    Note: There is a case that fp_reg might be written from fp_alu and fp_sram at the same time, need to implement stall logic to prevent this.
    */
    // Delay a clk due to fp_alu takes one clk to compute the result
    assign  fp_alu_valid = (exe_fp_control == ADD_FP || exe_fp_control == SUB_FP || exe_fp_control == MAX_FP || exe_fp_control == MUL_FP || exe_fp_control == MV_FP);

    always_comb begin
        if (fp_alu_valid) begin
            // From ALU
            fp_reg_we       = 1'b1;
            fp_reg_wdata    = fp_alu_out; 
            fp_wtarget      = recorded_fp_waddr_alu;
            write_data_from_external_fp = 1'b0;
        end if (sfu_out_valid) begin
            fp_reg_we       = 1'b1;
            fp_reg_wdata    = fp_sfu_out;
            fp_wtarget      = recorded_fp_waddr_sfu;
            write_data_from_external_fp = 1'b0;                
        end else if (load_fp_sram_valid) begin
            fp_reg_we       = 1'b1;
            fp_reg_wdata    = fp_ld_from_sram;
            fp_wtarget      = recorded_fp_waddr_sram;
            write_data_from_external_fp = 1'b0;
        end else if (external_fp_in_valid) begin
            fp_reg_we       = 1'b1;
            fp_reg_wdata    = external_fp_in;
            fp_wtarget      = external_fp_wtarget;
            write_data_from_external_fp = 1'b1;
        end else begin
            fp_reg_we       = 1'b0;
            fp_reg_wdata    = 'b0;
            fp_wtarget      = 'b0;
            write_data_from_external_fp = 1'b0;
        end
    end

    // Decide external_fp_in_ready. If the external_fp is ready to write (external_fp_in_valid == 1'b1 ) but fp_sram is busy, then the external_fp_in_ready should be 0.
    assign external_fp_in_ready = (external_fp_in_valid & write_data_from_external_fp);
    assign fp_rs1 = exe_stage_op.fps1;
    assign fp_rs2 = exe_stage_op.fps2;
    assign fp_rd  = exe_stage_op.fpd;
    assign fp_reg_addr_1 = (fp_control == ST_REG_FP) ? fp_rd : fp_rs1;
    assign fp_reg_addr_2 = fp_rs2;
    assign received_v_reduct_result = external_fp_in_ready;

    fp_alu #(
        .EXP_WIDTH(S_FP_EXP_WIDTH),
        .MANT_WIDTH(S_FP_MANT_WIDTH)
    ) fp_alu_init (
        .clk        (clk),
        .data_a     (fp_reg_1),
        .data_b     (fp_reg_2),
        .operation  (exe_fp_control),
        .data_out   (fp_alu_out)
    );

    fp_sfu #(
        .EXP_WIDTH  (S_FP_EXP_WIDTH),
        .MANT_WIDTH (S_FP_MANT_WIDTH)      
    ) fp_sfu_init (
        .clk                (clk),
        .rst                (rst),
        .data_in            (fp_reg_1),
        .reg_waddr          (p1_fp_rd),
        .operation          (fp_control),
        .data_out           (fp_sfu_out),
        .stored_reg_waddr   (recorded_fp_waddr_sfu),
        .data_out_valid     (sfu_out_valid),
        .data_out_ready     (sfu_out_ready)
    );

    regfile_2p1w #(
        .BITWIDTH(S_FP_EXP_WIDTH + S_FP_MANT_WIDTH + 1),
        .DEPTH(1 << FP_OPERAND_WIDTH)
    ) fp_reg_file (
        .clk        (clk),
        .we         (fp_reg_we),
        .waddr      (fp_wtarget),
        .wdata      (fp_reg_wdata),
        .raddr1     (fp_reg_addr_1),
        .raddr2     (fp_reg_addr_2),
        .rdata1     (fp_reg_1),
        .rdata2     (fp_reg_2)
    );
    

    // SRAM for FP
    scalar_sram #(
        .DATA_WIDTH(FP_SRAM_WIDTH),
        .DEPTH(FP_SRAM_DEPTH)
        `ifdef SIMULATION
        , .MemInitFile(FP_MEM_INIT_FILE)
        `endif
    ) fp_scalar_sram (
        .clk            (clk),
        .rst            (rst),
        .req            (fp_sram_req),
        .write_en       (fp_sram_wen),
        .sram_addr      (fp_sram_addr),
        .sram_data_in   (fp_reg_1),
        .sram_data_out  (fp_ld_from_sram)
    );

    //----------------------------//
    // Fixed Unit
    //----------------------------//

    logic [FIXED_DATA_WIDTH - 1 : 0] fixed_reg_1, fixed_reg_2, fixed_alu_out, fixed_reg_wdata, fixed_ld_from_sram, recorded_alu_out, computed_address;
    logic [FIXED_DATA_WIDTH - 1 : 0] fixed_loaded_reg_1, fixed_loaded_reg_2;
    logic fixed_reg_wen, fixed_write_from_sram_req, p1_fixed_write_from_sram_req, fixed_alu_valid;
    logic [FIXED_OPERAND_WIDTH - 1 : 0] fixed_reg_waddr, recorded_fixed_reg_exe_waddr, p1_recorded_fixed_reg_exe_waddr;
    S_FIXED_OP exe_fixed_op;
    logic [FIXED_OPERAND_WIDTH - 1 : 0] p1_rd, p1_rs1, p1_rs2, p2_rd;
    logic [IMM_WIDTH - 1 : 0] recorded_imm_in;
    logic [FIXED_OPERAND_WIDTH - 1 : 0] fixed_reg_addr_1, fixed_reg_addr_2;
    
    always_comb begin
        if (p1_fixed_write_from_sram_req) begin
            fixed_reg_waddr = p1_recorded_fixed_reg_exe_waddr;
            fixed_reg_wdata = fixed_ld_from_sram;
            fixed_reg_wen   = 1'b1;
        end  else begin
            fixed_reg_waddr = p2_rd;
            fixed_reg_wdata = fixed_alu_out;
            fixed_reg_wen   = fixed_alu_valid;
        end

        // Level-2 Forwarding
        fixed_reg_1 = ((p1_rs1 == p2_rd) & fixed_reg_wen) ? fixed_reg_wdata : fixed_loaded_reg_1;
        fixed_reg_2 = ((p1_rs2 == p2_rd) & fixed_reg_wen) ? fixed_reg_wdata : fixed_loaded_reg_2;
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            recorded_fixed_reg_exe_waddr    <= 'b0;
            fixed_write_from_sram_req       <= 1'b0;
            p1_fixed_write_from_sram_req    <= 1'b0;
            p1_recorded_fixed_reg_exe_waddr <= 'b0;
            exe_fixed_op                    <= STALL_S_FIXED;
            p1_rd                           <= 'b0;
            p2_rd                           <= 'b0;
            p1_rs1                          <= 'b0;
            p1_rs2                          <= 'b0;
            recorded_alu_out                <= 'b0;
            fixed_out_1                     <= 'b0;
            fixed_out_2                     <= 'b0;
            recorded_imm_in                 <= 'b0;

        end else begin
            exe_fixed_op                <= assigned_fixed_op;
            recorded_imm_in             <= imm_in;
            if ((assigned_fixed_op != STALL_S_FIXED) & (assigned_fixed_op != PASS_ADDR) & (assigned_fixed_op != PASS_ADDR_2) & (assigned_fixed_op != COMP_ADDR)) begin
                p1_rd                   <= rd;
            end 
            p2_rd                       <= p1_rd;
            p1_rs1                      <= rs1;
            p1_rs2                      <= rs2;
            p1_fixed_write_from_sram_req <= fixed_write_from_sram_req;
            p1_recorded_fixed_reg_exe_waddr <= recorded_fixed_reg_exe_waddr;

            if (assigned_fixed_op == LD_FIX) begin
                recorded_fixed_reg_exe_waddr    <= rd;
                fixed_write_from_sram_req       <= 1'b1;
            end else begin
                fixed_write_from_sram_req       <= 1'b0;
            end


            if (exe_fixed_op == PASS_ADDR || exe_fixed_op == PASS_ADDR_2) begin
                fixed_out_1                 <= fixed_reg_1;
                fixed_out_2                 <= fixed_reg_2;
            end else if (exe_fixed_op == COMP_ADDR) begin
                fixed_out_1                 <= computed_address;
                fixed_out_2                 <= 'b0;
            end else if (exe_fixed_op == COMP_ADDR_2) begin
                fixed_out_1                 <= computed_address;
                fixed_out_2                 <= fixed_reg_2;
            end else begin
                fixed_out_1                 <= 'b0;
                fixed_out_2                 <= 'b0;
            end
        end
    end

    assign fixed_reg_addr_1 = rs1;
    assign fixed_reg_addr_2 = ((assigned_fixed_op == PASS_ADDR_2) || (assigned_fixed_op == ST_FIX) || (assigned_fixed_op == MAP_V_FP)) ? rd : rs2;


    fixed_alu #(
        .BITWIDTH(FIXED_DATA_WIDTH)
    ) fixed_alu (
        .clk            (clk),
        .rst            (rst),
        .operand_a      (fixed_reg_1),
        .operand_b      (fixed_reg_2),
        .imm_value      ({{(FIXED_DATA_WIDTH - IMM_WIDTH){1'b0}}, recorded_imm_in}),
        .operation      (exe_fixed_op),
        .result_valid   (fixed_alu_valid),
        .computed_address(computed_address),
        .result         (fixed_alu_out)
    );

    regfile_2p1w #(
        .BITWIDTH(FIXED_DATA_WIDTH),
        .DEPTH(1 << FIXED_OPERAND_WIDTH)
    ) fixed_reg_file (
        .clk        (clk),
        .we         (fixed_reg_wen),
        .waddr      (fixed_reg_waddr),
        .wdata      (fixed_reg_wdata),
        .raddr1     (fixed_reg_addr_1),
        .raddr2     (fixed_reg_addr_2),
        .rdata1     (fixed_loaded_reg_1),
        .rdata2     (fixed_loaded_reg_2)
    );

    scalar_sram #(
        .DATA_WIDTH(FIXED_SRAM_WIDTH),
        .DEPTH(FIXED_SRAM_DEPTH)
        `ifdef SIMULATION
            ,
            .MemInitFile(FIXED_MEM_INIT_FILE)
        `endif
    ) fixed_scalar_sram (
        .clk(clk),
        .rst(rst),
        .req            ((exe_fixed_op == LD_FIX) || (exe_fixed_op == ST_FIX)),
        .write_en       ((exe_fixed_op == ST_FIX)),
        .sram_addr      (computed_address[FIXED_SRAM_ADDR_WIDTH - 1 : 0]),
        .sram_data_in   (fixed_loaded_reg_2),
        .sram_data_out  (fixed_ld_from_sram)
    );

endmodule