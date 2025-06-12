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
    output logic out_result_valid,
    input  logic out_result_ready
);

    // ==============================================================================================
    // Declaration : registers, wires
    // ==============================================================================================

    logic [FP_MANT_WIDTH + FP_EXP_WIDTH : 0]    reg_top_data;      
    logic [FP_MANT_WIDTH + FP_EXP_WIDTH : 0]    reg_left_data;
    logic stored_top_valid, stored_left_valid;

    // ==============================================================================================
    // STAGE 1: Pass Data from Top and Left to the Bottom and Right
    // ==============================================================================================

    always_ff @(posedge clk) begin
        if (rst) begin
            reg_top_data    <= {FP_MANT_WIDTH + FP_EXP_WIDTH + 1{1'b0}};
            reg_left_data   <= {FP_MANT_WIDTH + FP_EXP_WIDTH + 1{1'b0}};
        end else begin
            if (in_top_valid) begin
                reg_top_data <= in_top_data;
                stored_top_valid <= 1'b1;
            end else begin
                stored_top_valid <= 1'b0;
            end

            if (in_left_valid) begin
                reg_left_data <= in_left_data;
                stored_left_valid <= 1'b1;
            end else begin
                stored_left_valid <= 1'b0;
            end
        end
    end

    assign in_top_ready  = out_bottom_ready;
    assign in_left_ready = out_right_ready; // Directly Connect to avoid unnecessary stalling for the PE the middle of the array, where the valid signals not arrived together.

    assign out_bottom_data      = out_bottom_ready ? reg_top_data : {FP_MANT_WIDTH + FP_EXP_WIDTH + 1{1'b0}};
    assign out_bottom_valid     = stored_top_valid;

    assign out_right_element    = out_right_ready ? reg_left_data : {FP_MANT_WIDTH + FP_EXP_WIDTH + 1{1'b0}};
    assign out_right_valid      = stored_left_valid;


    // ==============================================================================================
    // STAGE 2: Multiplication of the elements from Top and Left, Scale Summation
    // ==============================================================================================

    logic [FP_MANT_WIDTH + FP_EXP_WIDTH + PROD_EXT_EXP_WIDTH + PROD_EXT_MANT_WIDTH : 0] mul_result, reg_mul_result;
    logic reg_mul_in_valid;
    logic reg_mul_out_valid;

    assign reg_mul_in_valid = stored_top_valid & stored_left_valid;

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

    always @(posedge clk) begin
        if (rst) begin
            reg_mul_result <= 'b0;
        end else begin
            if (reg_mul_in_valid) begin
                reg_mul_result <= mul_result;
                reg_mul_out_valid <= 1'b1;
            end else begin
                reg_mul_out_valid <= 1'b0;
            end
        end
    end

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


    always_ff @(posedge clk) begin
        if (rst) begin
            shifted_result_valid <= 1'b0;
            rescaled_result <= {(ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH + 1){1'b0}};
        end else begin
            if (reg_mul_out_valid) begin
                rescaled_result <= shifted_result; // Keep the value from the previous stage
                shifted_result_valid <= 1'b1;
            end else begin
                shifted_result_valid <= 1'b0;
            end
        end
    end

    // ==============================================================================================
    // STAGE 4: Accumulation
    // ==============================================================================================

    logic [ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH : 0] stored_result;
    logic [ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH : 0] acc_result;
    logic acc_valid;

    fp_cp_adder #(
        .MANT_WIDTH(ACC_FP_MANT_WIDTH),
        .EXP_WIDTH(ACC_FP_EXP_WIDTH),
        .EXT_MANT_WIDTH(0),
        .EXT_EXP_WIDTH(0)
    ) acc_adder (
        .data_a     (stored_result),
        .data_b     (reg_mul_result),
        .data_out   (acc_result)
    );

    always_ff @(posedge clk) begin
        if (rst) begin
            stored_result <= 'b0;
            acc_valid <= 1'b0;
        end else begin
            if (shifted_result_valid) begin
                stored_result <= acc_result;
                acc_valid <= 1'b1;
            end

            if (out_result_ready & acc_valid) begin
                out_result_valid <= 1'b1;
                out_fp <= stored_result;
            end else begin
                out_result_valid <= 1'b0;
                out_fp <= {(ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH + 1){1'b0}};
            end
        end
    end

endmodule
