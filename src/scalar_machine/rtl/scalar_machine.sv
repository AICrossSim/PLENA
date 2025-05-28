`timescale 1ns / 1ps
`include "operation.svh"
`include "configuration.svh"
`include "Global_Define.vh"
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
    // Simulation Purpose
    `ifdef SIMULATION
        parameter string FP_MEM_INIT_FILE = "",
        parameter string FIXED_MEM_INIT_FILE = ""
    `endif
) (
    input   logic clk,
    input   logic rst,

    // Control
    input   OP_BUNDLE  assigned_op_bundle,
    input   S_FIXED_OP assigned_fixed_op,

    // Fixed Register Control
    input   logic [FIXED_OPERAND_WIDTH - 1 : 0] rs1,
    input   logic [FIXED_OPERAND_WIDTH - 1 : 0] rs2,
    input   logic [FIXED_OPERAND_WIDTH - 1 : 0] rd,

    // Fixed Value input
    input   logic [FIXED_DATA_WIDTH - 1 : 0] fixed_in,
    input   logic [IMM_WIDTH - 1 : 0] imm_in,

    output  logic [FIXED_DATA_WIDTH - 1 : 0] fixed_out_1,
    output  logic [FIXED_DATA_WIDTH - 1 : 0] fixed_out_2,

    // FP Value input
    input   logic [FP_EXP_WIDTH + FP_MANT_WIDTH : 0] external_fp_in,
    input   logic external_fp_in_valid,
    output  logic external_fp_in_ready,
    input   logic [FP_OPERAND_WIDTH - 1 : 0] external_fp_wtarget,
    
    output  logic [FP_EXP_WIDTH + FP_MANT_WIDTH : 0] fp_out,

    // Stall Detection
    output  logic sfu_in_use,
    output  logic fp_stall_req,
    output  logic fixed_stall_req
);

    import pipeline_pkg::*;
    import configuration_pkg::*;

    //----------------------------//
    // FP Unit
    //----------------------------//
    S_FP_OP fp_control;
    assign fp_control = assigned_op_bundle.s_fp_op;
    logic general_fp_operation;
    assign general_fp_alu_en = (fp_control == ADD_FP || fp_control == SUB_FP || fp_control == MAX_FP || fp_control == MUL_FP || fp_control == MV_FP);

    struct {
        logic [FP_OPERAND_WIDTH-1:0] target_fp;
        S_FP_OP                      fp_op;
    } fp_track [SCALAR_FP_MAX_CYCLES];

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

            if (fp_stall_req == 1'b0) begin
                // Check if the fp rd is already in process
                fp_track[0] <= '{
                    target_fp  :fp_rd,
                    fp_op      :fp_control
                };
                if (fp_rd != fp_wtarget)
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
    logic [FP_EXP_WIDTH + FP_MANT_WIDTH : 0] fp_reg_1, fp_reg_2, fp_alu_out, fp_sfu_out, fp_reg_wdata, fp_ld_from_sram;
    logic sfu_out_valid, sfu_out_ready;
    logic write_data_from_external_fp;


    always_comb begin
        if (general_fp_alu_en) begin
            // From ALU
            fp_reg_we       = 1'b1;
            fp_reg_wdata    = fp_alu_out; 
            fp_wtarget      = fp_rd;
            write_data_from_external_fp = 1'b0;
        end else if ((fp_track[SCALAR_FP_SQRT_CYCLES - 1].fp_op == SQRT_FP) && (fp_track[SCALAR_FP_SQRT_CYCLES - 1].target_fp != fp_rd)) begin
            // From SFU
            if (sfu_out_valid) begin
                fp_reg_we       = 1'b1;
                fp_reg_wdata    = fp_sfu_out;
                fp_wtarget      = fp_track[SCALAR_FP_SQRT_CYCLES - 1].target_fp;
                write_data_from_external_fp = 1'b0;                
            end
        end else if (fp_track[0].fp_op ==  LD_REG_FP) begin
            fp_reg_we       = 1'b1;
            fp_reg_wdata    = fp_ld_from_sram;
            fp_wtarget      = fp_track[0].target_fp;
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


    // FP Register Control
    logic [FP_OPERAND_WIDTH - 1 : 0] fp_rs1;
    logic [FP_OPERAND_WIDTH - 1 : 0] fp_rs2;
    logic [FP_OPERAND_WIDTH - 1 : 0] fp_rd;

    assign fp_rs1 = assigned_op_bundle.fps1;
    assign fp_rs2 = assigned_op_bundle.fps2;
    assign fp_rd  = assigned_op_bundle.fpd;

    fp_alu #(
        .EXP_WIDTH(FP_EXP_WIDTH),
        .MANT_WIDTH(FP_MANT_WIDTH)
    ) fp_alu_init (
        .data_a(fp_reg_1),
        .data_b(fp_reg_2),
        .operation(fp_control),
        .data_out(fp_alu_out)
    );

    fp_sfu #(
        .EXP_WIDTH(FP_EXP_WIDTH),
        .MANT_WIDTH(FP_MANT_WIDTH)      
    ) fp_sfu_init (
        .clk(clk),
        .rst(rst),
        .data_in(fp_reg_1),
        .sfu_in_use(sfu_in_use),
        .operation(fp_control),
        .data_out(fp_sfu_out),
        .data_out_valid(sfu_out_valid),
        .data_out_ready(sfu_out_ready)
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
        .DEPTH(FP_SRAM_DEPTH)
        `ifdef SIMULATION
            ,
            .MemInitFile(FP_MEM_INIT_FILE)
        `endif
    ) fp_scalar_sram (
        .clk(clk),
        .rst(rst),
        .req((fp_control == LD_REG_FP) || (fp_control == ST_REG_FP)),
        .write_en((fp_control == ST_REG_FP)),
        .sram_addr(assigned_op_bundle.addr_1),
        .sram_data_in(fp_reg_2),
        .sram_data_out(fp_ld_from_sram)
    );

    //----------------------------//
    // Fixed Unit
    //----------------------------//

    logic [FIXED_DATA_WIDTH - 1 : 0] fixed_reg_1, fixed_reg_2, fixed_alu_out, fixed_reg_wdata, fixed_ld_from_sram, recorded_alu_out;
    logic [FIXED_DATA_WIDTH - 1 : 0] fixed_alu_operand_a, fixed_alu_operand_b;
    logic fixed_reg_wen, fixed_write_from_sram_req, fixed_stall_status;
    logic [FIXED_OPERAND_WIDTH - 1 : 0] fixed_reg_waddr, recorded_fixed_reg_waddr;
    logic [FIXED_DATA_WIDTH - 1 : 0] recorded_write_data;
    S_FIXED_OP exe_fixed_op;

    always_comb begin
        if (fixed_write_from_sram_req) begin
            fixed_reg_waddr = recorded_fixed_reg_waddr;
            fixed_reg_wdata = fixed_ld_from_sram;
            fixed_reg_wen   = 1'b1;
            // When the write port is required from two different sources, the stall signal should be set to 1
            fixed_stall_req = (exe_fixed_op != STALL_S_FIXED) && (exe_fixed_op != PASS_ADDR) && (exe_fixed_op != PASS_ADDR_2) && (exe_fixed_op != ST_FIX) && (exe_fixed_op != LD_FIX);
        end else if (fixed_stall_status) begin
            fixed_reg_waddr = recorded_fixed_reg_waddr;
            fixed_reg_wdata = recorded_alu_out;
            fixed_reg_wen   = 1'b1;
            // When the write port is required from two different sources, the stall signal should be set to 1
            fixed_stall_req = (exe_fixed_op != STALL_S_FIXED) && (exe_fixed_op != PASS_ADDR) && (exe_fixed_op != PASS_ADDR_2) && (exe_fixed_op != ST_FIX) && (exe_fixed_op != LD_FIX);
        end else begin
            fixed_reg_waddr = rd;
            fixed_reg_wdata = fixed_alu_out;
            fixed_reg_wen   = (exe_fixed_op != STALL_S_FIXED) && (exe_fixed_op != PASS_ADDR) && (exe_fixed_op != PASS_ADDR_2) && (exe_fixed_op != ST_FIX) && (exe_fixed_op != LD_FIX);
        end
    end

    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            recorded_fixed_reg_waddr    <= 'b0;
            recorded_write_data         <= 'b0;
            fixed_write_from_sram_req   <= 1'b0;
            fixed_stall_status          <= 1'b0;
            exe_fixed_op                <= STALL_S_FIXED;
        end else begin
            exe_fixed_op                <= assigned_fixed_op;
            if (exe_fixed_op == LD_FIX) begin
                recorded_fixed_reg_waddr    <= rd;
                fixed_write_from_sram_req   <= 1'b1;
                fixed_stall_status          <= 1'b0;
            end else if (fixed_stall_req) begin
                fixed_write_from_sram_req   <= 1'b0;
                recorded_alu_out            <= fixed_alu_out;
                recorded_fixed_reg_waddr    <= rd;
                fixed_stall_status          <= 1'b1;
            end else begin
                fixed_write_from_sram_req   <= 1'b0;
                fixed_stall_status          <= 1'b0;
            end
        end
    end

    assign fixed_out_1 =    (exe_fixed_op == PASS_ADDR || exe_fixed_op == PASS_ADDR_2) ? fixed_reg_1    :
                            (exe_fixed_op == COMP_ADDR)                                ? fixed_alu_out  : 'b0;
    assign fixed_out_2 =    (exe_fixed_op == PASS_ADDR || exe_fixed_op == PASS_ADDR_2) ? fixed_reg_2    : 'b0;

    logic [FIXED_OPERAND_WIDTH - 1 : 0] fixed_reg_addr_1, fixed_reg_addr_2;
    assign fixed_reg_addr_1 = rs1;
    assign fixed_reg_addr_2 = ((exe_fixed_op == PASS_ADDR_2) || (exe_fixed_op == ST_FIX)) ? rd : rs2;

    fixed_alu #(
        .BITWIDTH(FIXED_DATA_WIDTH)
    ) fixed_alu (
        .operand_a  (fixed_reg_1),
        .operand_b  (fixed_reg_2),
        .imm_value  ({{(FIXED_DATA_WIDTH - IMM_WIDTH){1'b0}}, imm_in}),
        .operation  (exe_fixed_op),
        .result     (fixed_alu_out)
    );

    regfile_2p1w #(
        .BITWIDTH(FIXED_DATA_WIDTH),
        .DEPTH(2 << FIXED_OPERAND_WIDTH)
    ) fixed_reg_file (
        .clk        (clk),
        .we         (fixed_reg_wen),
        .waddr      (fixed_reg_waddr),
        .wdata      (fixed_reg_wdata),
        .raddr1     (fixed_reg_addr_1),
        .raddr2     (fixed_reg_addr_2),
        .rdata1     (fixed_reg_1),
        .rdata2     (fixed_reg_2)
    );

    scalar_sram #(
        .DATA_WIDTH(FIXED_DATA_WIDTH),
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
        .sram_addr      (fixed_alu_out),
        .sram_data_in   (fixed_alu_operand_b),
        .sram_data_out  (fixed_ld_from_sram)
    );

endmodule