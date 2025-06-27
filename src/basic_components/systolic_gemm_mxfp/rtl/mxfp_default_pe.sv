`timescale 1ns / 1ps

/*
Module      : Processing Element (PE) in Systolic GEMM
Timing      : Sequential
Description : 
Status      : Under Development
*/

module mxfp_default_pe #(
    // MX-FP Data Format
    parameter MXFP_T_EXP_WIDTH      = 4,
    parameter MXFP_T_MANT_WIDTH     = 3,
    parameter MXFP_L_EXP_WIDTH      = 4,
    parameter MXFP_L_MANT_WIDTH     = 3,
    parameter MXFP_SCALE_WIDTH      = 8,

    // Accumulator Data Format
    parameter ACC_FP_EXP_WIDTH      = 8,
    parameter ACC_FP_MANT_WIDTH     = 7,
    parameter PROD_EXT_EXP_WIDTH    = 0,
    parameter PROD_EXT_MANT_WIDTH   = 0 
)(

    input logic clk,
    input logic rst,

    // Input from Top
    input  logic [MXFP_T_MANT_WIDTH + MXFP_T_EXP_WIDTH : 0] in_top_element,
    input  logic [MXFP_SCALE_WIDTH - 1 : 0] in_top_scale,
    input  logic system_top_valid,

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
    localparam SCALE_BIAS = (1 << (MXFP_SCALE_WIDTH - 1)) - 1;

    logic [MXFP_T_MANT_WIDTH + MXFP_T_EXP_WIDTH : 0]    reg_top_element;
    logic [MXFP_SCALE_WIDTH - 1 : 0]                    reg_top_scale;            
    logic [MXFP_L_MANT_WIDTH + MXFP_L_EXP_WIDTH : 0]    reg_left_element;
    logic [MXFP_SCALE_WIDTH - 1 : 0]                    reg_left_scale;

    // ==============================================================================================
    // STAGE 1: Pass Data from Top and Left to the Bottom and Right
    // ==============================================================================================

    always_ff @(posedge clk) begin
        if (rst) begin
            reg_top_element  <= {MXFP_T_MANT_WIDTH + MXFP_T_EXP_WIDTH + 1{1'b0}};
            reg_top_scale    <= {MXFP_SCALE_WIDTH{1'b0}};
            reg_left_element <= {MXFP_L_MANT_WIDTH + MXFP_L_EXP_WIDTH + 1{1'b0}};
            reg_left_scale   <= {MXFP_SCALE_WIDTH{1'b0}};
        end else begin
            if (system_top_valid) begin
                reg_top_element <= in_top_element;
                reg_top_scale   <= in_top_scale;
            end 

            if (system_left_valid) begin
                reg_left_element <= in_left_element;
                reg_left_scale   <= in_left_scale;
            end
        end
    end

    assign out_bottom_element   =   reg_top_element;
    assign out_bottom_scale     =   reg_top_scale;

    assign out_right_element    =   reg_left_element;
    assign out_right_scale      =   reg_left_scale; 

    // ==============================================================================================
    // STAGE 2: Multiplication of the elements from Top and Left, Scale Summation
    // ==============================================================================================
    // Note: Here we assum Left is higher precision.
    logic [MXFP_L_EXP_WIDTH + MXFP_L_MANT_WIDTH : 0] mul_result, reg_mul_result;
    logic reg_mul_in_valid;
    logic reg_mul_out_valid;
    logic [MXFP_SCALE_WIDTH - 1 : 0] reg_mul_scale;

    assign reg_mul_in_valid = mult_valid;

    fp_cp_asym_mult #(
        .EXP_WIDTH_A    (MXFP_T_EXP_WIDTH),
        .MANT_WIDTH_A   (MXFP_T_MANT_WIDTH),
        .EXP_WIDTH_B    (MXFP_L_EXP_WIDTH),
        .MANT_WIDTH_B   (MXFP_L_MANT_WIDTH)
    ) element_mult (
        .data_a (reg_top_element),
        .data_b (reg_left_element),
        .data_out(mul_result)
    );

    always @(posedge clk) begin
        if (rst) begin
            reg_mul_result <= {MXFP_L_EXP_WIDTH + MXFP_L_MANT_WIDTH + 1{1'b0}};
            reg_mul_scale <= {MXFP_SCALE_WIDTH{1'b0}};
        end else begin
            if (reg_mul_in_valid) begin
                // Scale addition
                reg_mul_scale <= reg_top_scale + reg_left_scale - SCALE_BIAS;
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

    mx_fp_2_fp_unary #(
        .MXFP_EXP_WIDTH     (MXFP_L_EXP_WIDTH),
        .MXFP_MANT_WIDTH    (MXFP_L_MANT_WIDTH),
        .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH),
        .FP_EXP_WIDTH       (ACC_FP_EXP_WIDTH),
        .FP_MANT_WIDTH      (ACC_FP_MANT_WIDTH)
    ) mx_fp_to_fp (
        .element_data_in    (reg_mul_result),
        .scale_data_in      (reg_mul_scale),
        .fp_out             (shifted_result)
    );

    skid_buffer #(
        .DATA_WIDTH         (ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH + 1)
    ) skid_buffer_dequantised (
        .clk(clk),
        .rst(rst),
        .data_in            (shifted_result),
        .data_in_valid      (reg_mul_out_valid),
        .data_in_ready      (reg_mul_out_ready),
        .data_out           (rescaled_result),
        .data_out_valid     (shifted_result_valid),
        .data_out_ready     (shifted_result_ready)
    );

    // ==============================================================================================
    // STAGE 4: Accumulation
    // ==============================================================================================

    logic [ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH : 0] stored_result;
    logic [ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH : 0] acc_result;
    logic acc_valid;

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
