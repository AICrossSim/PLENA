`timescale 1ns / 1ps
`include "operation.svh"

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
    parameter  FIXED_SRAM_DEPTH = 32

    // Dimensions
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
    input   logic [FIXED_DATA_WIDTH - 1 : 0] imm_in,

    output  logic [FIXED_DATA_WIDTH - 1 : 0] fixed_out_1,
    output  logic [FIXED_DATA_WIDTH - 1 : 0] fixed_out_2,

    // FP Value input
    input   logic [FP_EXP_WIDTH + FP_MANT_WIDTH : 0] fp_in,
    output   logic [FP_EXP_WIDTH + FP_MANT_WIDTH : 0] fp_out
);

    // FP UNit

    logic fp_reg_we;
    logic [FP_EXP_WIDTH + FP_MANT_WIDTH : 0] fp_reg_1, fp_reg_2, fp_alu_out, fp_reg_wdata, fp_ld_from_sram;

    assign fp_reg_we    = (fp_control != STALL_S_FP && fp_control !=LD_OUT_FP && fp_control != ST_REG_FP) ? 1'b1 : 1'b0;
    assign fp_reg_wdata = (fp_control == ST_IN_FP)  ? fp_in : 
                          (fp_control == LD_REG_FP) ? fp_ld_from_sram : fp_alu_out;

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
        .waddr      (fp_rd),
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
            fp_out <= (fp_control == LD_OUT_FP) ? fp_reg_1 : 'b0;
        end
    end


    prim_generic_ram_1p #(
        .Width(FP_EXP_WIDTH + FP_MANT_WIDTH + 1),
        .Depth(FP_SRAM_DEPTH),
        .DataBitsPerMask(FP_EXP_WIDTH + FP_MANT_WIDTH + 1) // Do not need write mask
    ) fp_scalar_sram (
        .clk_i(clk),
        .rst_ni(!rst),
        .req_i((fp_control == LD_REG_FP) || (fp_control == ST_REG_FP)),
        .write_i((fp_control == ST_REG_FP)),
        .addr_i(fixed_reg_1),
        .wdata_i(fp_reg_2),
        .wmask_i(1'b1),
        .rdata_o(fp_ld_from_sram)
    );



    // Fixed Unit
    logic [FIXED_DATA_WIDTH - 1 : 0] fixed_reg_1, fixed_reg_2, fixed_alu_out, fixed_reg_wdata, fixed_ld_from_sram;
    logic fix_we;

    assign fix_we = (fixed_control != STALL_S_FIXED && fixed_control != COMP_ADDR &&fixed_control != COMP_ADDR_2 && fixed_control != ST_FIX) ? 1'b1 : 1'b0;
    assign fixed_reg_wdata = (fixed_control == LD_FIX) ? fixed_ld_from_sram : fixed_alu_out;

    // always_ff @(posedge clk or posedge rst) begin
    //     if (rst) begin
    //         fixed_out_1 <= 'b0;
    //         fixed_out_2 <= 'b0;
    //     end else begin
    //         fixed_out_1 <= (fixed_control == COMP_ADDR || fixed_control == COMP_ADDR_2) ? fixed_reg_1 : 'b0;
    //         fixed_out_2 <= (fixed_control == COMP_ADDR || fixed_control == COMP_ADDR_2) ? fixed_reg_2 : 'b0;
    //     end
    // end
    
    assign fixed_out_1 = (fixed_control == COMP_ADDR || fixed_control == COMP_ADDR_2) ? fixed_reg_1 : 'b0;
    assign fixed_out_2 = (fixed_control == COMP_ADDR || fixed_control == COMP_ADDR_2) ? fixed_reg_2 : 'b0;


    logic [FIXED_OPERAND_WIDTH - 1 : 0] fixed_reg_addr_1, fixed_reg_addr_2;
    assign fixed_reg_addr_1 = rs1;
    assign fixed_reg_addr_2 = (fixed_control == COMP_ADDR_2) ? rd : rs2;

    fixed_alu #(
        .BITWIDTH(FIXED_DATA_WIDTH),
        .IMM_WIDTH(IMM_WIDTH)
    ) fixed_alu (
        .operand_a  (fixed_reg_1),
        .operand_b  (fixed_reg_2),
        .imm_value  (imm_in),
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


    prim_generic_ram_1p #(
        .Width(FIXED_DATA_WIDTH),
        .Depth(FIXED_SRAM_DEPTH),
        .DataBitsPerMask(FIXED_DATA_WIDTH)
    ) fixed_scalar_sram (
        .clk_i(clk),
        .rst_ni(!rst),

        .req_i((fp_control == LD_FIX) || (fp_control == ST_FIX)),
        .write_i((fp_control == ST_FIX)),
        .addr_i(fixed_reg_1),
        .wdata_i(fixed_reg_2),
        .wmask_i(1'b1),
        .rdata_o(fixed_ld_from_sram)
    );

endmodule