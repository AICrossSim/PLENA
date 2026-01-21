`timescale 1ns / 1ps

/*
Module      : Processing Element (PE) in Systolic GEMM
Timing      : Sequential
Description :
Status      : Under Development
*/

module mxint_default_pe #(
    // MX-FP Data Format
    parameter MX_L_INT_WIDTH         = 4,
    parameter MX_T_INT_WIDTH         = 4,
    parameter MXINT_SCALE_WIDTH     = 8,
    // Accumulator Data Format
    parameter ACC_FP_EXP_WIDTH      = 8,
    parameter ACC_FP_MANT_WIDTH     = 7
)(

    input logic clk,
    input logic rst,
    input logic clear_accumulator,

    // Input from Top
    input  logic [MX_T_INT_WIDTH - 1 : 0] in_top_element,
    input  logic [MXINT_SCALE_WIDTH - 1 : 0] in_top_scale,
    input  logic system_top_valid,

    // Input from Left
    input  logic [MX_L_INT_WIDTH - 1 : 0] in_left_element,
    input  logic [MXINT_SCALE_WIDTH - 1 : 0] in_left_scale,
    input  logic system_left_valid,

    // Mult Control
    input   logic mult_valid,
    output  logic mult_ready,

    // Output to Bottom
    output logic [MX_T_INT_WIDTH - 1 : 0] out_bottom_element,
    output logic [MXINT_SCALE_WIDTH - 1 : 0] out_bottom_scale,

    // Output to Right
    output logic [MX_L_INT_WIDTH - 1 : 0] out_right_element,
    output logic [MXINT_SCALE_WIDTH - 1 : 0] out_right_scale,

    // Output Result
    // output logic [ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] out_fp,
    output logic [MX_L_INT_WIDTH - 1 : 0] out_int,
    output logic [MXINT_SCALE_WIDTH - 1 : 0] out_scale,
    output logic out_valid,
    input  logic out_ready
);

    // ==============================================================================================
    // Declaration : registers, wires
    // ==============================================================================================
    localparam SCALE_BIAS = (1 << (MXINT_SCALE_WIDTH - 1)) - 1;

    logic [MX_T_INT_WIDTH - 1 : 0]    reg_top_element;
    logic [MXINT_SCALE_WIDTH - 1 : 0]                    reg_top_scale;
    logic [MX_L_INT_WIDTH - 1 : 0]    reg_left_element;
    logic [MXINT_SCALE_WIDTH - 1 : 0]                    reg_left_scale;

    // ==============================================================================================
    // STAGE 1: Pass Data from Top and Left to the Bottom and Right
    // ==============================================================================================

    always_ff @(posedge clk) begin
        if (rst) begin
            reg_top_element  <= {MX_T_INT_WIDTH{1'b0}};
            reg_top_scale    <= {MXINT_SCALE_WIDTH{1'b0}};
            reg_left_element <= {MX_L_INT_WIDTH{1'b0}};
            reg_left_scale   <= {MXINT_SCALE_WIDTH{1'b0}};
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
    logic [MX_L_INT_WIDTH - 1 : 0] block_mult_result, reg_block_mul;
    logic [MXINT_SCALE_WIDTH - 1 : 0] scale_sum_result, reg_scale_sum;
    logic block_mult_in_valid, block_mult_out_valid;
    logic block_mult_in_ready, block_mult_out_ready;
    logic scale_sum_in_valid, scale_sum_in_ready;
    logic scale_sum_out_valid, scale_sum_out_ready;
    logic [MX_T_INT_WIDTH + MX_L_INT_WIDTH - 1 : 0] mult_result;

    split_n #(
        .N(2)
    ) split_mult_signal (
        .data_in_valid(mult_valid),
        .data_in_ready(mult_ready),
        .data_out_valid({block_mult_in_valid, scale_sum_in_valid}),
        .data_out_ready({block_mult_in_ready, scale_sum_in_ready})
    );

    // Multiplication result
    (* use_dsp = "yes" *) assign mult_result = $signed(reg_top_element) * $signed(reg_left_element);
    assign block_mult_out_valid = block_mult_in_valid;
    assign block_mult_in_ready = block_mult_out_ready;

    // Scale summation result
    assign scale_sum_result = reg_top_scale + reg_left_scale - SCALE_BIAS;
    assign scale_sum_out_valid = scale_sum_in_valid;
    assign scale_sum_in_ready = scale_sum_out_ready;

    // ==============================================================================================
    // STAGE 3: Shift the result according to the scale
    // ==============================================================================================

    logic [ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH : 0] shifted_result, rescaled_result;
    logic converted_result_valid, converted_result_ready;
    logic acc_mult_valid, acc_mult_ready;
    logic [MX_T_INT_WIDTH + MX_L_INT_WIDTH + 4 - 1 : 0] acc_result;
    logic acc_result_valid, acc_result_ready;

    join2 #() join_mxfp_mult_inst (
      .data_in_ready ({block_mult_out_ready, scale_sum_out_ready}),
      .data_in_valid ({block_mult_out_valid, scale_sum_out_valid}),
      .data_out_valid(acc_mult_valid),
      .data_out_ready(acc_mult_ready)
    );

    fix_accumulator #(
        .WIDTH (MX_T_INT_WIDTH + MX_L_INT_WIDTH),
        .EXPAND_WIDTH (4)
    ) acc_adder (
        .clk(clk),
        .rst(rst),
        .clear_accumulator(clear_accumulator),
        .data_in_valid  (acc_mult_valid),
        .data_in_ready  (acc_mult_ready),
        .data_in        (mult_result),
        .data_out       (acc_result),
        .data_out_valid (acc_result_valid),
        .data_out_ready (acc_result_ready)
    );

    // mx_int_2_fp_unary #(
    //     .MXINT_WIDTH        (MX_L_INT_WIDTH),
    //     .MXINT_FRAC_WIDTH   (MX_L_INT_WIDTH),
    //     .MXINT_SCALE_WIDTH  (MXINT_SCALE_WIDTH),
    //     .FP_EXP_WIDTH       (ACC_FP_EXP_WIDTH),
    //     .FP_MANT_WIDTH      (ACC_FP_MANT_WIDTH)
    // ) mx_fp_to_fp (
    //     .clk                (clk),
    //     .rst                (rst),
    //     .data_in_valid      (acc_result_valid),
    //     .data_in_ready      (acc_result_ready),
    //     .element_data_in    (acc_result),
    //     .scale_data_in      (scale_sum_result),
    //     .data_out_valid     (converted_result_valid),
    //     .data_out_ready     (converted_result_ready),
    //     .fp_out             (shifted_result)
    // );



    // ==============================================================================================
    // STAGE 4: Accumulation
    // ==============================================================================================
    assign out_int = acc_result;
    assign out_scale = scale_sum_result;
    assign out_valid = acc_result_valid;
    assign acc_result_ready = out_ready;

endmodule
