`timescale 1ns / 1ps

/*
Module      : Processing Element (PE) in Systolic GEMM
Timing      : Sequential
Description : 
Status      : Under Development
*/

module default_pe #(
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

    // Input from Top
    input  logic [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] in_top_element,
    input  logic [MXFP_SCALE_WIDTH - 1 : 0] in_top_scale,
    input  logic in_top_valid,
    output logic in_top_ready,
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
    localparam SCALE_BIAS = (1 << (MXFP_SCALE_WIDTH - 1)) - 1;

    logic [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0]    reg_top_element;
    logic [MXFP_SCALE_WIDTH - 1 : 0]                reg_top_scale;            
    logic [MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0]    reg_left_element;
    logic [MXFP_SCALE_WIDTH - 1 : 0]                reg_left_scale;
    logic stored_top_valid, stored_left_valid;
    logic stored_top_ready, stored_left_ready;

    // ==============================================================================================
    // STAGE 1: Pass Data from Top and Left to the Bottom and Right
    // ==============================================================================================

    always_ff @(posedge clk) begin
        if (rst) begin
            reg_top_element <= {MXFP_MANT_WIDTH + MXFP_EXP_WIDTH + 1{1'b0}};
            reg_top_scale   <= {MXFP_SCALE_WIDTH{1'b0}};
            reg_left_element <= {MXFP_MANT_WIDTH + MXFP_EXP_WIDTH + 1{1'b0}};
            reg_left_scale   <= {MXFP_SCALE_WIDTH{1'b0}};
        end else begin
            if (in_top_valid) begin
                reg_top_element <= in_top_element;
                reg_top_scale   <= in_top_scale;
                stored_top_valid <= 1'b1;
            end else begin
                stored_top_valid <= 1'b0;
            end

            if (in_left_valid) begin
                reg_left_element <= in_left_element;
                reg_left_scale   <= in_left_scale;
                stored_left_valid <= 1'b1;
            end else begin
                stored_left_valid <= 1'b0;
            end
        end
    end

    assign in_top_ready  = out_bottom_ready;
    assign in_left_ready = out_right_ready; // Directly Connect to avoid unnecessary stalling for the PE the middle of the array, where the valid signals not arrived together.

    assign out_bottom_element   = reg_top_element;
    assign out_bottom_scale     = reg_top_scale;
    assign out_bottom_valid     = stored_top_valid;

    assign out_right_element    = reg_left_element;
    assign out_right_scale      = reg_left_scale;
    assign out_right_valid      = stored_left_valid;


    // ==============================================================================================
    // STAGE 2: Multiplication of the elements from Top and Left, Scale Summation
    // ==============================================================================================

    logic [ACC_FP_EXP_WIDTH + ACC_FP_EXP_WIDTH : 0] mul_result, reg_mul_result;
    logic reg_mul_in_valid, reg_mul_in_ready;
    logic reg_mul_out_valid, reg_mul_out_ready;
    logic [MXFP_SCALE_WIDTH - 1 : 0] reg_mul_scale;
    localparam EXT_MANT_WIDTH = ACC_FP_MANT_WIDTH - MXFP_MANT_WIDTH;
    localparam EXT_EXP_WIDTH = ACC_FP_EXP_WIDTH - MXFP_EXP_WIDTH;

    join2 #() join_mult (
        .data_in_ready ({stored_top_ready, stored_left_ready}),
        .data_in_valid ({stored_top_valid, stored_left_valid}),
        .data_out_valid (reg_mul_in_valid),
        .data_out_ready (reg_mul_in_ready)
    );

    fp_cp_mult #(
        .MANT_WIDTH(MXFP_MANT_WIDTH),
        .EXP_WIDTH(MXFP_EXP_WIDTH),
        .EXT_MANT_WIDTH(EXT_MANT_WIDTH),
        .EXT_EXP_WIDTH(EXT_EXP_WIDTH)
    ) element_mult (
        .data_a (reg_top_element),
        .data_b (reg_left_element),
        .data_out(mul_result)
    );


    always @(posedge clk) begin
        if (rst) begin
            reg_mul_result <= {ACC_FP_EXP_WIDTH + ACC_FP_EXP_WIDTH + 1{1'b0}};
            reg_mul_scale <= {MXFP_SCALE_WIDTH{1'b0}};
        end else begin
            if (reg_mul_in_valid & reg_mul_out_ready) begin
                // Scale addition
                reg_mul_scale <= reg_top_scale + reg_left_scale - SCALE_BIAS;
                reg_mul_result <= mul_result;
                reg_mul_out_valid <= 1'b1;
            end else begin
                reg_mul_out_valid <= 1'b0;
            end
        end
    end

    assign reg_mul_in_ready = reg_mul_out_ready;

    // ==============================================================================================
    // STAGE 3: Shift the result according to the scale
    // ==============================================================================================

    logic [ACC_FP_EXP_WIDTH + ACC_FP_EXP_WIDTH : 0] shifted_result, rescaled_result;
    logic shifted_result_valid, shifted_result_ready;

    mx_fp_2_fp_unary #(
        .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
        .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
        .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
        .FP_EXP_WIDTH(ACC_FP_EXP_WIDTH),
        .FP_MANT_WIDTH(ACC_FP_MANT_WIDTH)
    ) mx_fp_to_fp (
        .element_data_in(reg_mul_result),
        .scale_data_in  (reg_mul_scale),
        .fp_out         (shifted_result)
    );

    skid_buffer #(
        .DATA_WIDTH(ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH + 1)
    ) shift_buffer (
        .clk           (clk),
        .rst           (rst),
        .data_in       (shifted_result),
        .data_in_valid (reg_mul_out_valid),
        .data_in_ready (reg_mul_out_ready),
        .data_out      (rescaled_result),
        .data_out_valid(shifted_result_valid),
        .data_out_ready(shifted_result_ready)
    );

    // ==============================================================================================
    // STAGE 4: Accumulation
    // ==============================================================================================

    logic [ACC_FP_EXP_WIDTH + ACC_FP_EXP_WIDTH : 0] stored_result;
    logic [ACC_FP_EXP_WIDTH + ACC_FP_EXP_WIDTH : 0] acc_result;

    fp_cp_adder #(
        .MANT_WIDTH(ACC_FP_MANT_WIDTH),
        .EXP_WIDTH(ACC_FP_EXP_WIDTH),
        .EXT_MANT_WIDTH(0),
        .EXT_EXP_WIDTH(0)
    ) acc_adder (
        .data_a (stored_result),
        .data_b (rescaled_result),
        .data_out (acc_result)
    );

    always_ff @(posedge clk) begin
        if (rst) begin
            stored_result <= {ACC_FP_EXP_WIDTH + ACC_FP_EXP_WIDTH + 1'b0};
        end else begin
            if (shifted_result_valid & out_result_ready) begin
                stored_result <= acc_result;
            end
        end
    end

    // ==============================================================================================
    // REG_ADD  -> OUT
    // ==============================================================================================

    skid_buffer #(
        .DATA_WIDTH(ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH + 1)
    ) acc_buffer (
        .clk           (clk),
        .rst           (rst),
        .data_in       (acc_result),
        .data_in_valid (shifted_result_valid),
        .data_in_ready (shifted_result_ready),
        .data_out      (out_fp),
        .data_out_valid(out_result_valid),
        .data_out_ready(out_result_ready)
    );

endmodule
