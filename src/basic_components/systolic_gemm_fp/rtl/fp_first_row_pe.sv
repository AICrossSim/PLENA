`timescale 1ns / 1ps

/*
Module      : First Row of the Processing Element (PE) in Systolic GEMM, Supporting GEMV
Timing      : Sequential
Description : This module is used to specifically support GEMV operations.
*/

module fp_first_row_pe #(
    parameter FP_EXP_WIDTH    = 8,
    parameter FP_MANT_WIDTH   = 7,
    parameter ACC_FP_EXP_WIDTH    = 8,
    parameter ACC_FP_MANT_WIDTH   = 7,
    parameter PROD_EXT_EXP_WIDTH  = 0,
    parameter PROD_EXT_MANT_WIDTH = 0 
)(

    input logic clk,
    input logic rst,
    input logic control, // 0 for GEMV, 1 for GEMM

    // Input from Top
    input  logic [FP_MANT_WIDTH + FP_EXP_WIDTH : 0] in_top_data,
    input  logic system_top_valid,

    // Input from Vector
    input  logic [FP_MANT_WIDTH + FP_EXP_WIDTH  : 0] in_top_v_data,

    // Input from Left
    input  logic [FP_MANT_WIDTH + FP_EXP_WIDTH : 0] in_left_data,
    input  logic system_left_valid,

    // Mult Control
    input   logic mult_valid,
    output  logic mult_ready,

    // Output to Bottom
    output logic [FP_MANT_WIDTH + FP_EXP_WIDTH : 0] out_bottom_data,

    // Output to Right
    output logic [FP_MANT_WIDTH + FP_EXP_WIDTH : 0] out_right_data,

    // Output Result
    output logic [ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] out_fp,
    input  logic out_result_ready
);

    // ==============================================================================================
    // Declaration : registers, wires
    // ==============================================================================================
    
    logic [FP_MANT_WIDTH + FP_EXP_WIDTH : 0] pe_in_top_data;
    logic [FP_MANT_WIDTH + FP_EXP_WIDTH: 0] pe_in_left_data;

    logic [FP_MANT_WIDTH + FP_EXP_WIDTH : 0] pe_out_bottom_data;
    logic [FP_MANT_WIDTH + FP_EXP_WIDTH : 0] pe_out_right_data;

    logic [ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] pe_out_fp;
    logic pe_out_result_valid, pe_out_result_ready;

    always_comb begin
        // For Top level, Same as the default PE
        if (control == 1'b0) begin
            // GEMM
            pe_in_top_data      = in_top_data;
            pe_in_left_data     = in_left_data;

            // Bottom
            out_bottom_data     = pe_out_bottom_data;
            // Right
            out_right_data      = pe_out_right_data;
            // Result
            out_fp              = pe_out_fp;
            
        end else begin
            // GEMV
            pe_in_top_data      = in_top_v_data;
            pe_in_left_data     = in_left_data;
            // Bottom
            out_bottom_data     = 'b0;
            // Right
            out_right_data      = 'b0;
            // Result
            out_fp              = pe_out_fp;
        end

    end

    // Declare the default PE
    fp_default_pe #(
        .FP_EXP_WIDTH       (FP_EXP_WIDTH),
        .FP_MANT_WIDTH      (FP_MANT_WIDTH),
        .ACC_FP_EXP_WIDTH   (ACC_FP_EXP_WIDTH),
        .ACC_FP_MANT_WIDTH  (ACC_FP_MANT_WIDTH),
        .PROD_EXT_EXP_WIDTH (PROD_EXT_EXP_WIDTH),
        .PROD_EXT_MANT_WIDTH(PROD_EXT_MANT_WIDTH)
    ) default_pe_inst (
        .clk(clk),
        .rst(rst),
        .in_top_data        (pe_in_top_data),
        .system_top_valid   (system_top_valid),
        .in_left_data       (pe_in_left_data),
        .system_left_valid  (system_left_valid),
        .mult_valid         (mult_valid),
        .mult_ready         (mult_ready),
        .out_bottom_data    (pe_out_bottom_data),
        .out_right_data     (pe_out_right_data),
        .out_fp             (pe_out_fp),
        .out_result_ready   (pe_out_result_ready)
    );

endmodule