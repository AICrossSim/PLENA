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
    input  logic in_top_valid,
    output logic in_top_ready,

    // Input from Vector
    input  logic [FP_MANT_WIDTH + FP_EXP_WIDTH  : 0] in_top_v_data,
    input  logic in_top_v_valid,
    output logic in_top_v_ready,

    // Input from Left
    input  logic [FP_MANT_WIDTH + FP_EXP_WIDTH : 0] in_left_data,
    input  logic in_left_valid,
    output logic in_left_ready,

    // Output to Bottom
    output logic [FP_MANT_WIDTH + FP_EXP_WIDTH : 0] out_bottom_data,
    output logic out_bottom_valid,
    input  logic out_bottom_ready,

    // Output to Right
    output logic [FP_MANT_WIDTH + FP_EXP_WIDTH : 0] out_right_data,
    output logic out_right_valid,
    input  logic out_right_ready,

    // Output Result
    output logic [ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] out_fp,
    output logic out_result_valid,
    input  logic out_result_ready
);

    // ==============================================================================================
    // Declaration : registers, wires
    // ==============================================================================================
    
    logic [FP_MANT_WIDTH + FP_EXP_WIDTH : 0] pe_in_top_data;
    logic pe_in_top_valid, pe_in_top_ready;

    logic [FP_MANT_WIDTH + FP_EXP_WIDTH: 0] pe_in_left_data;
    logic pe_in_left_valid, pe_in_left_ready;

    logic [FP_MANT_WIDTH + FP_EXP_WIDTH : 0] pe_out_bottom_data;
    logic pe_out_bottom_valid, pe_out_bottom_ready;

    logic [FP_MANT_WIDTH + FP_EXP_WIDTH : 0] pe_out_right_data;
    logic pe_out_right_valid, pe_out_right_ready;

    logic [ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] pe_out_fp;
    logic pe_out_result_valid, pe_out_result_ready;

    always_comb begin
        // For Top level, Same as the default PE
        pe_in_top_data = in_top_data;
        pe_in_top_valid = in_top_valid;
        in_top_ready = pe_in_top_ready;
        
        if (control == 1'b1) begin
            // GEMM
            pe_in_left_data     = in_left_data;
            pe_in_left_valid    = in_left_valid;
            in_left_ready       = pe_in_left_ready;
            // Bottom
            out_bottom_data     = pe_out_bottom_data;
            out_bottom_valid    = pe_out_bottom_valid;
            pe_out_bottom_ready = out_bottom_ready;
            // Right
            out_right_data      = pe_out_right_data;
            out_right_valid     = pe_out_right_valid;
            pe_out_right_ready  = out_right_ready;
            // Result
            out_fp              = pe_out_fp;
            out_result_valid    = pe_out_result_valid;
            pe_out_result_ready = out_result_ready;
        end else begin
            // GEMV
            pe_in_left_data     = in_top_v_data;
            pe_in_left_valid    = in_top_v_valid;
            in_top_v_ready      = pe_in_left_ready;
            // Bottom
            out_bottom_data     = 'b0;
            out_bottom_valid    = 1'b0;
            pe_out_bottom_ready = 1'b1;
            // Right
            out_right_data      = 'b0;
            out_right_valid     = 1'b0;
            pe_out_right_ready  = 1'b1;
            // Result
            out_fp              = pe_out_fp;
            out_result_valid    = pe_out_result_valid;
            pe_out_result_ready = out_result_ready;
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
        .in_top_valid       (pe_in_top_valid),
        .in_top_ready       (pe_in_top_ready),
        .in_left_data       (pe_in_left_data),
        .in_left_valid      (pe_in_left_valid),
        .in_left_ready      (pe_in_left_ready),
        .out_bottom_data    (pe_out_bottom_data),
        .out_bottom_valid   (pe_out_bottom_valid),
        .out_bottom_ready   (pe_out_bottom_ready),
        .out_right_data     (pe_out_right_data),
        .out_right_valid    (pe_out_right_valid),
        .out_right_ready    (pe_out_right_ready),
        .out_fp             (pe_out_fp),
        .out_result_valid   (pe_out_result_valid),
        .out_result_ready   (pe_out_result_ready)
    );

endmodule