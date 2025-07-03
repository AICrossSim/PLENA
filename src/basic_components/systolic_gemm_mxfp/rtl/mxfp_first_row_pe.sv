`timescale 1ns / 1ps

/*
Module      : First Row of the Processing Element (PE) in Systolic GEMM, Supporting GEMV
Timing      : Sequential
Description : This module is used to specifically support GEMV operations.
*/

module mxfp_first_row_pe #(
    // MX-FP Data Format
    parameter MXFP_T_EXP_WIDTH      = 4,
    parameter MXFP_T_MANT_WIDTH     = 3,
    parameter MXFP_L_EXP_WIDTH      = 4,
    parameter MXFP_L_MANT_WIDTH     = 3,
    parameter MXFP_SCALE_WIDTH  = 8,
    // Accumulator Data Format
    parameter ACC_FP_EXP_WIDTH    = 8,
    parameter ACC_FP_MANT_WIDTH   = 7
)(

    input logic clk,
    input logic rst,

    input logic control, // 0 for GEMV, 1 for GEMM

    // Input from Top
    input  logic [MXFP_T_MANT_WIDTH + MXFP_T_EXP_WIDTH : 0] in_top_element,
    input  logic [MXFP_SCALE_WIDTH - 1 : 0] in_top_scale,
    input  logic system_top_valid,

    // Input from Vector
    input  logic [MXFP_L_MANT_WIDTH + MXFP_L_EXP_WIDTH : 0] in_left_v_element,
    input  logic [MXFP_SCALE_WIDTH - 1 : 0] in_left_v_scale,

    // Input from Left
    input  logic [MXFP_L_MANT_WIDTH + MXFP_L_EXP_WIDTH : 0] in_left_element,
    input  logic [MXFP_SCALE_WIDTH - 1 : 0] in_left_scale,
    input  logic system_left_valid,

    // Mult Control
    input   logic mult_valid,
    output  logic mult_ready,

    // Output to Bottom
    output logic [MXFP_T_MANT_WIDTH + MXFP_T_EXP_WIDTH : 0] out_bottom_element,
    output logic [MXFP_SCALE_WIDTH - 1 : 0] out_bottom_scale,

    // Output to Right
    output logic [MXFP_L_MANT_WIDTH + MXFP_L_EXP_WIDTH : 0] out_right_element,
    output logic [MXFP_SCALE_WIDTH - 1 : 0] out_right_scale,
    
    // Output Result
    output logic [ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] out_fp,
    input  logic out_result_ready
);

    // ==============================================================================================
    // Declaration : registers, wires
    // ==============================================================================================
    
    logic [MXFP_T_MANT_WIDTH + MXFP_T_EXP_WIDTH : 0] pe_in_top_element;
    logic [MXFP_SCALE_WIDTH - 1 : 0] pe_in_top_scale;

    logic [MXFP_L_MANT_WIDTH + MXFP_L_EXP_WIDTH : 0] pe_in_left_element;
    logic [MXFP_SCALE_WIDTH - 1 : 0] pe_in_left_scale; 

    logic [MXFP_T_MANT_WIDTH + MXFP_T_EXP_WIDTH : 0] pe_out_bottom_element;
    logic [MXFP_SCALE_WIDTH - 1 : 0] pe_out_bottom_scale;

    logic [MXFP_L_MANT_WIDTH + MXFP_L_EXP_WIDTH : 0] pe_out_right_element;
    logic [MXFP_SCALE_WIDTH - 1 : 0] pe_out_right_scale;

    logic [ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] pe_out_fp;
    logic pe_out_result_ready;

    always_comb begin
        // For Top level, Same as the default PE
        pe_in_top_element = in_top_element;
        pe_in_top_scale = in_top_scale;
        pe_out_result_ready = out_result_ready;
        if (control == 1'b0) begin
            // GEMM
            pe_in_left_element  = in_left_element;
            pe_in_left_scale    = in_left_scale;
            // Bottom
            out_bottom_element  = pe_out_bottom_element;
            out_bottom_scale    = pe_out_bottom_scale;
            // Right
            out_right_element   = pe_out_right_element;
            out_right_scale     = pe_out_right_scale;
            // Result
            out_fp              = pe_out_fp;
        end else begin
            // GEMV
            pe_in_left_element  = in_left_v_element;
            pe_in_left_scale    = in_left_v_scale;
            // Bottom
            out_bottom_element  = 'b0;
            out_bottom_scale    = 'b0;
            // Right
            out_right_element   = 'b0;
            out_right_scale     = 'b0;
            // Result
            out_fp              = pe_out_fp;
        end

    end

    // Declare the default PE
    mxfp_default_pe #(
        .MXFP_T_EXP_WIDTH   (MXFP_T_EXP_WIDTH),
        .MXFP_T_MANT_WIDTH  (MXFP_T_MANT_WIDTH),
        .MXFP_L_EXP_WIDTH   (MXFP_L_EXP_WIDTH),
        .MXFP_L_MANT_WIDTH  (MXFP_L_MANT_WIDTH),
        .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH),
        .ACC_FP_EXP_WIDTH   (ACC_FP_EXP_WIDTH),
        .ACC_FP_MANT_WIDTH  (ACC_FP_MANT_WIDTH)
    ) default_pe_inst (
        .clk(clk),
        .rst(rst),
        .in_top_element         (pe_in_top_element),
        .in_top_scale           (pe_in_top_scale),
        .system_top_valid       (system_top_valid),
        .in_left_element        (pe_in_left_element),
        .in_left_scale          (pe_in_left_scale),
        .system_left_valid      (system_left_valid),
        .mult_valid             (mult_valid),
        .mult_ready             (mult_ready),
        .out_bottom_element     (pe_out_bottom_element),
        .out_bottom_scale       (pe_out_bottom_scale),
        .out_right_element      (pe_out_right_element),
        .out_right_scale        (pe_out_right_scale),
        .out_fp                 (pe_out_fp),
        .out_result_ready       (pe_out_result_ready)
    );

endmodule