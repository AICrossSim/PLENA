`timescale 1ns / 1ps
`include "operation.svh"
`include "configuration.svh"
`include "Global_Define.vh"
/*
Module      : Scalar Machine Module
Timing      : Sequential, all the operations completed in 1 cycle
Description : This module contains two modules:
            : FP ALU for all the fp computation related operations
            : Fixed ALU, only have addition and subtraction operations for address manipulation
Status      : Under Testing
*/

module scalar_machine #(

    // MX-FP Data Format
    parameter   MXFP_MANT_WIDTH   = 8,
    parameter   MXFP_EXP_WIDTH    = 4,
    parameter   MXFP_SCALE_WIDTH = 8,

    // FP Data Format
    parameter   FP_EXP_WIDTH = 5,
    parameter   FP_MANT_WIDTH = 10,

    // Fixed Data Format
    parameter   FIXED_DATA_WIDTH = 32,

    // Memory Storage
    parameter  FP_SRAM_DEPTH = 32,
    parameter  FIXED_SRAM_DEPTH = 32,

    // Simulation Purpose
    parameter string FP_MEM_INIT_FILE = "",
    parameter string FIXED_MEM_INIT_FILE = ""


) (
    input   logic clk,
    input   logic rst,

    // Control
    input   S_FP_OP fp_control,
    input   S_FIXED_OP fixed_control,

    // Fixed Register Control
    input   logic [FIXED_OPERAND_WIDTH - 1 : 0] rs1,
    input   logic [FIXED_OPERAND_WIDTH - 1 : 0] rs2,
    input   logic [FIXED_OPERAND_WIDTH - 1 : 0] rd,

    // FP Register Control
    input   logic [FP_OPERAND_WIDTH - 1 : 0] fp_rs1,
    input   logic [FP_OPERAND_WIDTH - 1 : 0] fp_rs2,
    input   logic [FP_OPERAND_WIDTH - 1 : 0] fp_rd,

    // Fixed Value input
    input   logic [FIXED_DATA_WIDTH - 1 : 0] fixed_in,
    input   logic [IMM_WIDTH - 1 : 0] imm_in,

    output  logic [FIXED_DATA_WIDTH - 1 : 0] fixed_out_1,
    output  logic [FIXED_DATA_WIDTH - 1 : 0] fixed_out_2,

    // FP Value input
    input   logic [FP_EXP_WIDTH + FP_MANT_WIDTH : 0] fp_in,
    output  logic [FP_EXP_WIDTH + FP_MANT_WIDTH : 0] fp_out,

    // Stall Detection
    output  logic fp_stall_req
);
    import pipeline_pkg::*;
    // FP UNit
    // Keep Operation in Pipe
    typedef struct {
        logic [FP_OPERAND_WIDTH-1:0]        target_fp;
        S_FP_OP                             fp_op;
    } TRACK_FP;
    TRACK_FP fp_track [SCALAR_FP_MAX_CYCLES - 1 : 0];

    // ------------------- Tracing Register for Stall Detection -------------------
    logic tracing_fpreg_in_process [2 << FP_OPERAND_WIDTH - 1 : 0];
    logic [FP_OPERAND_WIDTH - 1 : 0] fp_wtarget;

    // Dependency Detection
    always_comb begin
        if (fp_control == ADD_FP || fp_control == SUB_FP || fp_control == MAX_FP || fp_control == MUL_FP) begin
            // Two read ports
            fp_stall_req = (tracing_fpreg_in_process[fp_rs1] || tracing_fpreg_in_process[fp_rs2]) ? 1'b1 : 1'b0;
        end else if (fp_control == EXP_FP || fp_control == RECI_FP || fp_control == SQRT_FP ) begin
            // One read port
            fp_stall_req = (tracing_fpreg_in_process[fp_rs1]) ? 1'b1 : 1'b0;
        end
    end

    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            for (int i = 0; i < 2 << FP_OPERAND_WIDTH; i++) begin
                tracing_fpreg_in_process[i] <= 1'b0;
            end

            for (int i = 0; i < SCALAR_FP_MAX_CYCLES; i++) begin
                fp_track[i] <= '{
                    target_fp  :'b0,
                    fp_op      :STALL_S_FP
                };
            end
        end else begin
            // Note: Here involving write to the same variable from the two conditions
            if (fp_reg_we) begin
                tracing_fpreg_in_process[fp_wtarget] <= 1'b0;
            end

            if (fp_stall_req == 1'b0 & (fp_wtarget != fp_rd)) begin
                // Check if the fp rd is already in process
                fp_track[0] <= '{
                    target_fp  :fp_rd,
                    fp_op      :fp_control
                };
                tracing_fpreg_in_process[fp_rd] <= 1'b1;
            end

            for (int i = 0; i < SCALAR_FP_MAX_CYCLES - 1; i++) begin
                fp_track[i+1] <= fp_track[i];
            end
        end
    end


    /*
    Note: There is a case that fp_reg might be written from fp_alu and fp_sram at the same time, need to implement stall logic to prevent this.
    */
    logic fp_reg_we;
    logic [FP_EXP_WIDTH + FP_MANT_WIDTH : 0] fp_reg_1, fp_reg_2, fp_alu_out, fp_reg_wdata, fp_ld_from_sram;

    always_comb begin
        if ((fp_track[SCALAR_FP_SQRT_CYCLES - 1].fp_op == SQRT_FP) && (fp_track[SCALAR_FP_SQRT_CYCLES - 1].target_fp != fp_rd)) begin
            fp_reg_we = 1'b1;
            fp_reg_wdata = fp_alu_out;
            fp_wtarget = fp_track[SCALAR_FP_SQRT_CYCLES - 1].target_fp;
        end else if (fp_track[0].fp_op ==  LD_REG_FP) begin
            fp_reg_we = 1'b1;
            fp_reg_wdata = fp_ld_from_sram;
            fp_wtarget = fp_track[0].target_fp;
        end else begin
            fp_reg_we = 1'b0;
            fp_reg_wdata = 'b0;
        end
    end


    fp_alu #(
        .EXP_WIDTH(FP_EXP_WIDTH),
        .MANT_WIDTH(FP_MANT_WIDTH)
    ) fp_alu (
        .data_a(fp_reg_1),
        .data_b(fp_reg_2),
        .operation(fp_control),
        .data_out(fp_alu_out)
    );

    regfile_2p1w #(
        .BITWIDTH(FP_EXP_WIDTH + FP_MANT_WIDTH + 1),
        .DEPTH(2 << FP_OPERAND_WIDTH)
    ) fp_reg_file (
        .clk        (clk),
        .we         (fp_reg_we),
        .waddr      (fp_wtarget),
        .wdata      (fp_reg_wdata),
        .raddr1     (fp_rs1),
        .raddr2     (fp_rs2),
        .rdata1     (fp_reg_1),
        .rdata2     (fp_reg_2)
    );

    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            fp_out <= 'b0;
        end else begin
            if (fp_control == LD_OUT_FP) begin
                if (fp_rs2 == fp_wtarget) begin
                    fp_out <= fp_reg_wdata;
                end else begin
                    fp_out <= fp_reg_2;
                end
            end else if (fp_control == ST_REG_FP) begin
                fp_out <= 'b0;
            end 
        end
    end



    // SRAM for FP
    scalar_sram #(
        .DATA_WIDTH(FP_EXP_WIDTH + FP_MANT_WIDTH + 1),
        .DEPTH(FP_SRAM_DEPTH),
        .MemInitFile(FP_MEM_INIT_FILE)
    ) fp_scalar_sram (
        .clk(clk),
        .rst(rst),
        .req((fp_control == LD_REG_FP) || (fp_control == ST_REG_FP)),
        .write_en((fp_control == ST_REG_FP)),
        .sram_addr(fixed_alu_out),
        .sram_data_in(fp_reg_2),
        .sram_data_out(fp_ld_from_sram)
    );

    // Fixed Unit
    logic [FIXED_DATA_WIDTH - 1 : 0] fixed_reg_1, fixed_reg_2, fixed_alu_out, fixed_reg_wdata, fixed_ld_from_sram;
    logic fix_we;

    assign fix_we = (fixed_control != STALL_S_FIXED && fixed_control != PASS_ADDR &&fixed_control != PASS_ADDR_2 && fixed_control != ST_FIX) ? 1'b1 : 1'b0;
    assign fixed_reg_wdata = (fixed_control == LD_FIX) ? fixed_ld_from_sram : fixed_alu_out;

    assign fixed_out_1 = (fixed_control == PASS_ADDR || fixed_control == PASS_ADDR_2) ? fixed_reg_1 : 'b0;
    assign fixed_out_2 = (fixed_control == PASS_ADDR || fixed_control == PASS_ADDR_2) ? fixed_reg_2 : 'b0;


    logic [FIXED_OPERAND_WIDTH - 1 : 0] fixed_reg_addr_1, fixed_reg_addr_2;
    assign fixed_reg_addr_1 = rs1;
    assign fixed_reg_addr_2 = (fixed_control == PASS_ADDR_2) ? rd : rs2;

    fixed_alu #(
        .BITWIDTH(FIXED_DATA_WIDTH),
        .IMM_WIDTH(IMM_WIDTH)
    ) fixed_alu (
        .operand_a  (fixed_reg_1),
        .operand_b  (fixed_reg_2),
        .imm_value  ({{(FIXED_DATA_WIDTH - IMM_WIDTH){1'b0}}, imm_in}),
        .operation  (fixed_control),
        .result     (fixed_alu_out)
    );

    regfile_2p1w #(
        .BITWIDTH(FIXED_DATA_WIDTH),
        .DEPTH(2 << FIXED_OPERAND_WIDTH)
    ) fixed_reg_file (
        .clk        (clk),
        .we         (fix_we),
        .waddr      (rd),
        .wdata      (fixed_reg_wdata),
        .raddr1     (fixed_reg_addr_1),
        .raddr2     (fixed_reg_addr_2),
        .rdata1     (fixed_reg_1),
        .rdata2     (fixed_reg_2)
    );

    scalar_sram #(
        .DATA_WIDTH(FIXED_DATA_WIDTH),
        .DEPTH(FIXED_SRAM_DEPTH),
        .MemInitFile(FIXED_MEM_INIT_FILE)
    ) fixed_scalar_sram (
        .clk(clk),
        .rst(rst),
        .req            ((fixed_control == LD_FIX) || (fixed_control == ST_FIX)),
        .write_en       ((fixed_control == ST_FIX)),
        .sram_addr      (fixed_reg_1),
        .sram_data_in   (fixed_reg_2),
        .sram_data_out  (fixed_ld_from_sram)
    );

endmodule