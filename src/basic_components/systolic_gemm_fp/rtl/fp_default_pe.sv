`timescale 1ns / 1ps

/*
Module      : Processing Element (PE) in Systolic GEMM
Timing      : Sequential
Description : 
Status      : Under Development
*/

module fp_default_pe #(
    parameter FP_EXP_WIDTH    = 8,
    parameter FP_MANT_WIDTH   = 7,
    parameter ACC_FP_EXP_WIDTH    = 8,
    parameter ACC_FP_MANT_WIDTH   = 7,
    parameter PROD_EXT_EXP_WIDTH  = 0,
    parameter PROD_EXT_MANT_WIDTH = 0 
)(

    input logic clk,
    input logic rst,

    // Input from Top
    input  logic [FP_MANT_WIDTH + FP_EXP_WIDTH : 0] in_top_data,
    input  logic in_top_valid,
    output logic in_top_ready,
    
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
    input  logic out_result_ready
);

    // ==============================================================================================
    // Declaration : registers, wires
    // ==============================================================================================

    logic [FP_MANT_WIDTH + FP_EXP_WIDTH : 0]    reg_top_data;      
    logic [FP_MANT_WIDTH + FP_EXP_WIDTH : 0]    reg_left_data;
    logic stored_top_valid, stored_left_valid;
    logic stored_top_ready, stored_left_ready;
    logic mult_in_a_valid, mult_in_b_valid;
    logic mult_in_a_ready, mult_in_b_ready;

    // ==============================================================================================
    // STAGE 1: Pass Data from Top and Left to the Bottom and Right
    // ==============================================================================================

    skid_buffer #(
        .DATA_WIDTH(FP_MANT_WIDTH + FP_EXP_WIDTH + 1)
    ) skid_buffer_top (
        .clk(clk),
        .rst(rst),
        .data_in        (in_top_data),
        .data_in_valid  (in_top_valid),
        .data_in_ready  (in_top_ready),
        .data_out       (reg_top_data),
        .data_out_valid (stored_top_valid),
        .data_out_ready (stored_top_ready)
    );

    skid_buffer #(
        .DATA_WIDTH(FP_MANT_WIDTH + FP_EXP_WIDTH + 1)
    ) skid_buffer_left (
        .clk(clk),
        .rst(rst),
        .data_in        (in_left_data),
        .data_in_valid  (in_left_valid),
        .data_in_ready  (in_left_ready),
        .data_out       (reg_left_data),
        .data_out_valid (stored_left_valid),
        .data_out_ready (stored_left_ready)
    );

    split_n #(
        .N(2)
    ) split_top (
        .data_in_valid(stored_top_valid),
        .data_in_ready(stored_top_ready),
        .data_out_valid({out_bottom_valid, mult_in_a_valid}),
        .data_out_ready({out_bottom_ready, mult_in_a_ready})
    );

    split_n #(
        .N(2)
    ) split_left (
        .data_in_valid(stored_left_valid),
        .data_in_ready(stored_left_ready),
        .data_out_valid({out_right_valid, mult_in_b_valid}),
        .data_out_ready({out_right_ready, mult_in_b_ready})
    );

    assign out_bottom_data      = reg_top_data;
    assign out_right_data       = reg_left_data;

    // ==============================================================================================
    // STAGE 2: Multiplication of the elements from Top and Left, Scale Summation
    // ==============================================================================================

    logic [FP_MANT_WIDTH + FP_EXP_WIDTH + PROD_EXT_EXP_WIDTH + PROD_EXT_MANT_WIDTH : 0] mul_result, reg_mul_result;
    logic reg_mul_in_valid, reg_mul_in_ready;
    logic reg_mul_out_valid, reg_mul_out_ready;
    
    join2 #() join_mult (
        .data_in_valid({mult_in_a_valid, mult_in_b_valid}),
        .data_in_ready({mult_in_a_ready, mult_in_b_ready}),
        .data_out_valid(reg_mul_in_valid),
        .data_out_ready(reg_mul_in_ready)
    );

    fp_cp_mult #(
        .MANT_WIDTH     (FP_MANT_WIDTH),
        .EXP_WIDTH      (FP_EXP_WIDTH),
        .EXT_MANT_WIDTH (PROD_EXT_MANT_WIDTH),
        .EXT_EXP_WIDTH  (PROD_EXT_EXP_WIDTH)
    ) element_mult (
        .data_a     (reg_top_data),
        .data_b     (reg_left_data),
        .data_out   (mul_result)
    );


    skid_buffer #(
        .DATA_WIDTH(FP_MANT_WIDTH + FP_EXP_WIDTH + 1)
    ) skid_buffer_mult (
        .clk(clk),
        .rst(rst),
        .data_in        (mul_result),
        .data_in_valid  (reg_mul_in_valid),
        .data_in_ready  (reg_mul_in_ready),
        .data_out       (reg_mul_result),
        .data_out_valid (reg_mul_out_valid),
        .data_out_ready (reg_mul_out_ready)
    );

    // ==============================================================================================
    // STAGE 3: Shift the result according to the scale
    // ==============================================================================================

    logic [ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH : 0] shifted_result, rescaled_result;
    logic shifted_result_valid, shifted_result_ready;

    fp_dequantizer #(
        .IN_EXP_WIDTH       (FP_EXP_WIDTH + PROD_EXT_EXP_WIDTH),
        .IN_MANT_WIDTH      (FP_MANT_WIDTH + PROD_EXT_MANT_WIDTH),
        .OUT_EXP_WIDTH      (ACC_FP_EXP_WIDTH),
        .OUT_MANT_WIDTH     (ACC_FP_MANT_WIDTH)
    ) mx_fp_to_fp (
        .in_fp          (reg_mul_result),
        .out_fp         (shifted_result)
    );


    skid_buffer #(
        .DATA_WIDTH(ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH + 1)
    ) skid_buffer_dequantised (
        .clk(clk),
        .rst(rst),
        .data_in        (shifted_result),
        .data_in_valid  (reg_mul_out_valid),
        .data_in_ready  (reg_mul_out_ready),
        .data_out       (rescaled_result),
        .data_out_valid (shifted_result_valid),
        .data_out_ready (shifted_result_ready)
    );

    // ==============================================================================================
    // STAGE 4: Accumulation
    // ==============================================================================================

    logic [ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH : 0] stored_result;
    logic [ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH : 0] acc_result;

    fp_cp_adder_v2 #(
        .MANT_WIDTH(ACC_FP_MANT_WIDTH),
        .EXP_WIDTH(ACC_FP_EXP_WIDTH),
        .EXT_MANT_WIDTH(0),
        .EXT_EXP_WIDTH(0)
    ) acc_adder (
        .data_a     (stored_result),
        .data_b     (rescaled_result),
        .data_out   (acc_result)
    );

    assign shifted_result_ready = 1'b1; // Always ready to accept shifted result / TODO: Might need to change this

    always_ff @(posedge clk) begin
        if (rst) begin
            stored_result <= 'b0;
        end else begin
            if (shifted_result_valid) begin
                stored_result <= acc_result;
            end
            if (out_result_ready) begin 
                out_fp <= stored_result;
            end else begin
                out_fp <= {(ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH + 1){1'b0}};
            end
        end
    end

endmodule
