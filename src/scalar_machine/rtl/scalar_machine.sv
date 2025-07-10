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
    input   logic [IMM_WIDTH - 1 : 0] imm_in,
    output  logic [FIXED_DATA_WIDTH - 1 : 0] fixed_out_1,
    output  logic [FIXED_DATA_WIDTH - 1 : 0] fixed_out_2,

    // FP Value input
    input   logic [S_FP_EXP_WIDTH + S_FP_MANT_WIDTH : 0] external_fp_in,
    input   logic external_fp_in_valid,
    output  logic external_fp_in_ready,
    input   logic [FP_OPERAND_WIDTH - 1 : 0] external_fp_wtarget,
    output  logic [S_FP_EXP_WIDTH + S_FP_MANT_WIDTH : 0] fp_out,

    // Stall Detection
    output  logic sfu_in_use,
    output  logic fp_stall_req
);

    import pipeline_pkg::*;
    import configuration_pkg::*;
    localparam FP_SRAM_ADDR_WIDTH = $clog2(FP_SRAM_DEPTH);
    localparam FIXED_SRAM_ADDR_WIDTH = $clog2(FIXED_SRAM_DEPTH);

    //----------------------------//
    // FP Unit
    //----------------------------//

    struct {
        logic [FP_OPERAND_WIDTH-1:0] target_fp;
        S_FP_OP                      fp_op;
    } fp_track [SCALAR_FP_LONGEST_OPERATE_CYCLES];
    S_FP_OP fp_control, exe_fp_control;
    logic [FP_OPERAND_WIDTH - 1 : 0] fp_rs1;
    logic [FP_OPERAND_WIDTH - 1 : 0] fp_rs2;
    logic [FP_OPERAND_WIDTH - 1 : 0] fp_rd;
    logic fp_reg_we;
    logic general_fp_operation;
    logic [S_FP_EXP_WIDTH + S_FP_MANT_WIDTH : 0] fp_reg_1, fp_reg_2, fp_alu_out, fp_sfu_out, fp_reg_wdata, fp_ld_from_sram;
    logic sfu_out_valid, sfu_out_ready;
    logic write_data_from_external_fp;
    logic general_fp_alu_en;
    logic [FP_SRAM_ADDR_WIDTH - 1 : 0] fp_sram_addr;

    assign  fp_control = exe_stage_op.s_fp_op;

    // ------------------- Tracing Register for Stall Detection -------------------
    localparam int TRACE_SIZE = 2 << FP_OPERAND_WIDTH; // Number of FP registers
    logic tracing_fpreg_in_process [TRACE_SIZE - 1 : 0];
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
            for (int i = 0; i < TRACE_SIZE; i++) begin
                tracing_fpreg_in_process[i] <= 1'b0;
            end

            for (int i = 0; i < SCALAR_FP_LONGEST_OPERATE_CYCLES; i++) begin
                fp_track[i] <= '{
                    target_fp  :'b0,
                    fp_op      :STALL_S_FP
                };
            end
            exe_fp_control <= STALL_S_FP;
        end else begin
            exe_fp_control <= fp_control;
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

            for (int i = 0; i < SCALAR_FP_LONGEST_OPERATE_CYCLES - 1; i++) begin
                fp_track[i+1] <= fp_track[i];
            end
        end
    end


    /*
    Note: There is a case that fp_reg might be written from fp_alu and fp_sram at the same time, need to implement stall logic to prevent this.
    */

    assign  general_fp_alu_en = (exe_fp_control == ADD_FP || exe_fp_control == SUB_FP || exe_fp_control == MAX_FP || exe_fp_control == MUL_FP || exe_fp_control == MV_FP);

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
        end else if (fp_track[1].fp_op ==  LD_REG_FP) begin
            fp_reg_we       = 1'b1;
            fp_reg_wdata    = fp_ld_from_sram;
            fp_wtarget      = fp_track[1].target_fp;
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
        .clk            (clk),
        .rst            (rst),
        .data_in        (fp_reg_1),
        .sfu_in_use     (sfu_in_use),
        .operation      (fp_control),
        .data_out       (fp_sfu_out),
        .data_out_valid (sfu_out_valid),
        .data_out_ready (sfu_out_ready)
    );

    regfile_2p1w #(
        .BITWIDTH(S_FP_EXP_WIDTH + S_FP_MANT_WIDTH + 1),
        .DEPTH(1 << FP_OPERAND_WIDTH)
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

    always_ff @(posedge clk) begin
        if (rst) begin
            fp_out          <= 'b0;
            fp_sram_addr    <= 'b0;
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
            fp_sram_addr <= exe_stage_op.addr_1; 
        end
    end

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
        .req            ((exe_fp_control == LD_REG_FP) || (exe_fp_control == ST_REG_FP)),
        .write_en       ((exe_fp_control == ST_REG_FP)),
        .sram_addr      (fp_sram_addr),
        .sram_data_in   (fp_reg_2),
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
            end else begin
                fixed_out_1                 <= 'b0;
                fixed_out_2                 <= 'b0;
            end
        end
    end

    assign fixed_reg_addr_1 = rs1;
    assign fixed_reg_addr_2 = ((assigned_fixed_op == PASS_ADDR_2) || (assigned_fixed_op == ST_FIX)) ? rd : rs2;


    fixed_alu #(
        .BITWIDTH(FIXED_DATA_WIDTH)
    ) fixed_alu (
        .clk        (clk),
        .rst        (rst),
        .operand_a  (fixed_reg_1),
        .operand_b  (fixed_reg_2),
        .imm_value  ({{(FIXED_DATA_WIDTH - IMM_WIDTH){1'b0}}, recorded_imm_in}),
        .operation  (exe_fixed_op),
        .result_valid (fixed_alu_valid),
        .computed_address(computed_address),
        .result     (fixed_alu_out)
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
        .sram_data_in   (fixed_alu_operand_b),
        .sram_data_out  (fixed_ld_from_sram)
    );

endmodule