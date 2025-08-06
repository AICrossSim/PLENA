`timescale 1ns / 1ps

/*
Module      : First Row of the Processing Element (PE) in Systolic GEMM, Supporting GEMV
Timing      : Sequential
Description : This module is used to specifically support GEMV operations.
*/

module mxfp_first_row_pe #(
    // MX-FP Data Format
    parameter MX_T_EXP_WIDTH      = 4,
    parameter MX_T_MANT_WIDTH     = 3,
    parameter MX_L_EXP_WIDTH      = 4,
    parameter MX_L_MANT_WIDTH     = 3,
    parameter MX_SCALE_WIDTH  = 8,
    // Accumulator Data Format
    parameter ACC_FP_EXP_WIDTH    = 8,
    parameter ACC_FP_MANT_WIDTH   = 7,
    // Data Type Control
    parameter L_MX_INT_EN         = 0,
    parameter T_MX_INT_EN         = 0 // Not implemented yet
)(

    input logic clk,
    input logic rst,
    input logic clear_accumulator,
    input logic control, // 0 for GEMV, 1 for GEMM
    

    // Input from Top
    input  logic [MX_T_MANT_WIDTH + MX_T_EXP_WIDTH : 0] in_top_element,
    input  logic [MX_SCALE_WIDTH - 1 : 0] in_top_scale,

    // Input from top vector
    input  logic [MX_T_MANT_WIDTH + MX_T_EXP_WIDTH : 0] in_top_v_element,
    input  logic [MX_SCALE_WIDTH - 1 : 0] in_top_v_scale,

    input  logic system_top_valid,

    // Input from Left
    input  logic [MX_L_MANT_WIDTH + MX_L_EXP_WIDTH : 0] in_left_element,
    input  logic [MX_SCALE_WIDTH - 1 : 0] in_left_scale,

    // Input from left vector
    input  logic [MX_L_MANT_WIDTH + MX_L_EXP_WIDTH : 0] in_left_v_element,
    input  logic [MX_SCALE_WIDTH - 1 : 0] in_left_v_scale,
    
    input  logic system_left_valid,

    // Mult Control
    input   logic mult_valid,
    output  logic mult_ready,

    // Output to Bottom
    output logic [MX_T_MANT_WIDTH + MX_T_EXP_WIDTH : 0] out_bottom_element,
    output logic [MX_SCALE_WIDTH - 1 : 0] out_bottom_scale,

    // Output to Right
    output logic [MX_L_MANT_WIDTH + MX_L_EXP_WIDTH : 0] out_right_element,
    output logic [MX_SCALE_WIDTH - 1 : 0] out_right_scale,
    
    // Output Result
    output logic [ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] out_fp,
    input  logic out_result_ready
);

    // ==============================================================================================
    // Declaration : registers, wires
    // ==============================================================================================
    
    logic [MX_T_MANT_WIDTH + MX_T_EXP_WIDTH : 0] pe_in_top_element;
    logic [MX_SCALE_WIDTH - 1 : 0] pe_in_top_scale;

    logic [MX_L_MANT_WIDTH + MX_L_EXP_WIDTH : 0] pe_in_left_element;
    logic [MX_SCALE_WIDTH - 1 : 0] pe_in_left_scale; 

    logic [MX_T_MANT_WIDTH + MX_T_EXP_WIDTH : 0] pe_out_bottom_element;
    logic [MX_SCALE_WIDTH - 1 : 0] pe_out_bottom_scale;

    logic [MX_L_MANT_WIDTH + MX_L_EXP_WIDTH : 0] pe_out_right_element;
    logic [MX_SCALE_WIDTH - 1 : 0] pe_out_right_scale;

    logic [ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] pe_out_fp;
    logic pe_out_result_ready;

    always_comb begin
        pe_out_result_ready = out_result_ready;
        if (control == 1'b0) begin
            // GEMM
            pe_in_top_element   = in_top_element;
            pe_in_top_scale     = in_top_scale;
            pe_in_left_element  = in_left_element;
            pe_in_left_scale    = in_left_scale;
            out_bottom_element  = pe_out_bottom_element;
            out_bottom_scale    = pe_out_bottom_scale;
            out_right_element   = pe_out_right_element;
            out_right_scale     = pe_out_right_scale;
            out_fp              = pe_out_fp;
        end else begin
            // GEMV
            pe_in_top_element   = in_top_v_element;
            pe_in_top_scale     = in_top_v_scale;
            pe_in_left_element  = in_left_v_element;
            pe_in_left_scale    = in_left_v_scale;
            out_bottom_element  = 'b0;
            out_bottom_scale    = 'b0;
            out_right_element   = 'b0;
            out_right_scale     = 'b0;
            out_fp              = pe_out_fp;
        end
    end

    // Declare the default PE
    mx_default_pe #(
        .MX_T_EXP_WIDTH     (MX_T_EXP_WIDTH),
        .MX_T_MANT_WIDTH    (MX_T_MANT_WIDTH),
        .MX_L_EXP_WIDTH     (MX_L_EXP_WIDTH),
        .MX_L_MANT_WIDTH    (MX_L_MANT_WIDTH),
        .MX_SCALE_WIDTH     (MX_SCALE_WIDTH),
        .ACC_FP_EXP_WIDTH   (ACC_FP_EXP_WIDTH),
        .ACC_FP_MANT_WIDTH  (ACC_FP_MANT_WIDTH),
        .L_MX_INT_EN        (L_MX_INT_EN),
        .T_MX_INT_EN        (T_MX_INT_EN)
    ) default_pe_inst (
        .clk(clk),
        .rst(rst),
        .clear_accumulator      (clear_accumulator),
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