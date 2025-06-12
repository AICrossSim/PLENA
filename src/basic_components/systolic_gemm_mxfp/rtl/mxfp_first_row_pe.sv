`timescale 1ns / 1ps

/*
Module      : First Row of the Processing Element (PE) in Systolic GEMM, Supporting GEMV
Timing      : Sequential
Description : This module is used to specifically support GEMV operations.
*/

module first_row_pe #(
    // MX-FP Data Format
    parameter MXFP_EXP_WIDTH    = 4,
    parameter MXFP_MANT_WIDTH   = 3,
    parameter MXFP_SCALE_WIDTH  = 8,
    // Accumulator Data Format
    parameter ACC_FP_EXP_WIDTH    = 8,
    parameter ACC_FP_MANT_WIDTH   = 7
)(

    input logic clk,
    input logic rst,

    input logic control, // 0 for GEMV, 1 for GEMM

    // Input from Top
    input  logic [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] in_top_element,
    input  logic [MXFP_SCALE_WIDTH - 1 : 0] in_top_scale,
    input  logic in_top_valid,
    output logic in_top_ready,

    // Input from Vector
    input  logic [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] in_top_v_element,
    input  logic [MXFP_SCALE_WIDTH - 1 : 0] in_top_v_scale,
    input  logic in_top_v_valid,
    output logic in_top_v_ready,

    // Input from Left
    input  logic [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] in_left_element,
    input  logic [MXFP_SCALE_WIDTH - 1 : 0] in_left_scale,
    input  logic in_left_valid,
    output logic in_left_ready,

    // Output to Bottom
    output logic [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] out_bottom_element,
    output logic [MXFP_SCALE_WIDTH - 1 : 0] out_bottom_scale,
    output logic out_bottom_valid,
    input  logic out_bottom_ready,

    // Output to Right
    output logic [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] out_right_element,
    output logic [MXFP_SCALE_WIDTH - 1 : 0] out_right_scale,
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
    
    logic [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] pe_in_top_element;
    logic [MXFP_SCALE_WIDTH - 1 : 0] pe_in_top_scale;
    logic pe_in_top_valid, pe_in_top_ready;

    logic [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] pe_in_left_element;
    logic [MXFP_SCALE_WIDTH - 1 : 0] pe_in_left_scale; 
    logic pe_in_left_valid, pe_in_left_ready;

    logic [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] pe_out_bottom_element;
    logic [MXFP_SCALE_WIDTH - 1 : 0] pe_out_bottom_scale;
    logic pe_out_bottom_valid, pe_out_bottom_ready;

    logic [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] pe_out_right_element;
    logic [MXFP_SCALE_WIDTH - 1 : 0] pe_out_right_scale;
    logic pe_out_right_valid, pe_out_right_ready;

    logic [ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] pe_out_fp;
    logic pe_out_result_valid, pe_out_result_ready;

    always_comb begin
        // For Top level, Same as the default PE
        pe_in_top_element = in_top_element;
        pe_in_top_scale = in_top_scale;
        pe_in_top_valid = in_top_valid;
        in_top_ready = pe_in_top_ready;
        
        if (control == 1'b1) begin
            // GEMM
            pe_in_left_element  = in_left_element;
            pe_in_left_scale    = in_left_scale;
            pe_in_left_valid    = in_left_valid;
            in_left_ready       = pe_in_left_ready;
            // Bottom
            out_bottom_element  = pe_out_bottom_element;
            out_bottom_scale    = pe_out_bottom_scale;
            out_bottom_valid    = pe_out_bottom_valid;
            pe_out_bottom_ready = out_bottom_ready;
            // Right
            out_right_element   = pe_out_right_element;
            out_right_scale     = pe_out_right_scale;
            out_right_valid     = pe_out_right_valid;
            pe_out_right_ready  = out_right_ready;
            // Result
            out_fp              = pe_out_fp;
            out_result_valid    = pe_out_result_valid;
            pe_out_result_ready = out_result_ready;
        end else begin
            // GEMV
            pe_in_left_element  = in_top_v_element;
            pe_in_left_scale    = in_top_v_scale;
            pe_in_left_valid    = in_top_v_valid;
            in_top_v_ready      = pe_in_left_ready;
            // Bottom
            out_bottom_element  = 'b0;
            out_bottom_scale    = 'b0;
            out_bottom_valid    = 1'b0;
            pe_out_bottom_ready = 1'b1;
            // Right
            out_right_element   = 'b0;
            out_right_scale     = 'b0;
            out_right_valid     = 1'b0;
            pe_out_right_ready  = 1'b1;
            // Result
            out_fp              = pe_out_fp;
            out_result_valid    = pe_out_result_valid;
            pe_out_result_ready = out_result_ready;
        end

    end

    // Declare the default PE
    default_pe #(
        .MXFP_EXP_WIDTH     (MXFP_EXP_WIDTH),
        .MXFP_MANT_WIDTH    (MXFP_MANT_WIDTH),
        .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH),
        .ACC_FP_EXP_WIDTH   (ACC_FP_EXP_WIDTH),
        .ACC_FP_MANT_WIDTH  (ACC_FP_MANT_WIDTH)
    ) default_pe_inst (
        .clk(clk),
        .rst(rst),
        .in_top_element     (pe_in_top_element),
        .in_top_scale       (pe_in_top_scale),
        .in_top_valid       (pe_in_top_valid),
        .in_top_ready       (pe_in_top_ready),
        .in_left_element    (pe_in_left_element),
        .in_left_scale      (pe_in_left_scale),
        .in_left_valid      (pe_in_left_valid),
        .in_left_ready      (pe_in_left_ready),
        .out_bottom_element (pe_out_bottom_element),
        .out_bottom_scale   (pe_out_bottom_scale),
        .out_bottom_valid   (pe_out_bottom_valid),
        .out_bottom_ready   (pe_out_bottom_ready),
        .out_right_element  (pe_out_right_element),
        .out_right_scale    (pe_out_right_scale),
        .out_right_valid    (pe_out_right_valid),
        .out_right_ready    (pe_out_right_ready),
        .out_fp             (pe_out_fp),
        .out_result_valid   (pe_out_result_valid),
        .out_result_ready   (pe_out_result_ready)
    );



endmodule