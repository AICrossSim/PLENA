`timescale 1ns / 1ps

/*
Module      : Processing Element (PE) in Systolic GEMM
Timing      : Sequential
Description : 
Status      : Under Development
*/

(* dont_touch = "true" *)
module mx_default_pe #(
    // MX-FP Data Format
    parameter MX_T_EXP_WIDTH        = 4,
    parameter MX_T_MANT_WIDTH       = 3,
    parameter MX_L_EXP_WIDTH        = 4,
    parameter MX_L_MANT_WIDTH       = 3,
    parameter MX_SCALE_WIDTH        = 8,

    // Accumulator Data Format
    parameter ACC_FP_EXP_WIDTH      = 8,
    parameter ACC_FP_MANT_WIDTH     = 7,
    parameter PROD_EXT_EXP_WIDTH    = 0,
    parameter PROD_EXT_MANT_WIDTH   = 0,

    // Data Type Control
    parameter L_MX_INT_EN           = 0,
    parameter T_MX_INT_EN           = 0 // Not implemented yet
)(

    input logic clk,
    input logic rst,
    input logic clear_accumulator,

    // Input from Top
    input  logic [MX_T_MANT_WIDTH + MX_T_EXP_WIDTH : 0] in_top_element,
    input  logic [MX_SCALE_WIDTH - 1 : 0] in_top_scale,
    input  logic system_top_valid,

    // Input from Left
    input  logic [MX_L_MANT_WIDTH + MX_L_EXP_WIDTH : 0] in_left_element,
    input  logic [MX_SCALE_WIDTH - 1 : 0] in_left_scale,
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
    localparam SCALE_BIAS = (1 << (MX_SCALE_WIDTH - 1)) - 1;

    logic [MX_T_MANT_WIDTH + MX_T_EXP_WIDTH : 0]    reg_top_element;
    logic [MX_SCALE_WIDTH - 1 : 0]                    reg_top_scale;            
    logic [MX_L_MANT_WIDTH + MX_L_EXP_WIDTH : 0]    reg_left_element;
    logic [MX_SCALE_WIDTH - 1 : 0]                    reg_left_scale;

    // ==============================================================================================
    // STAGE 1: Pass Data from Top and Left to the Bottom and Right
    // ==============================================================================================

    always_ff @(posedge clk) begin
        if (rst) begin
            reg_top_element  <= {MX_T_MANT_WIDTH + MX_T_EXP_WIDTH + 1{1'b0}};
            reg_top_scale    <= {MX_SCALE_WIDTH{1'b0}};
            reg_left_element <= {MX_L_MANT_WIDTH + MX_L_EXP_WIDTH + 1{1'b0}};
            reg_left_scale   <= {MX_SCALE_WIDTH{1'b0}};
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
    // STAGE 2-4: Conditional FP or INT MAC based on L_MX_INT_EN
    // ==============================================================================================

    generate
        if (L_MX_INT_EN == 1) begin : gen_int_mac
            // ======================================================================================
            // INTEGER MAC MODE - DSP-friendly pattern for synthesis experiment
            // ======================================================================================
            // Extract mantissa bits and treat as signed integers for DSP inference
            localparam INT_T_WIDTH = MX_T_MANT_WIDTH + 1; // +1 for sign
            localparam INT_L_WIDTH = MX_L_MANT_WIDTH + 1; // +1 for sign
            localparam INT_PROD_WIDTH = INT_T_WIDTH + INT_L_WIDTH;
            localparam INT_ACC_WIDTH = INT_PROD_WIDTH + 8; // Extra bits for accumulation headroom

            // Input operand registers - keep these to prevent removal
            (* keep = "true" *) logic signed [INT_T_WIDTH - 1 : 0] int_top;
            (* keep = "true" *) logic signed [INT_L_WIDTH - 1 : 0] int_left;

            // Accumulator register - NO dont_touch to allow DSP inference
            (* use_dsp = "simd" *) logic signed [INT_ACC_WIDTH - 1 : 0] int_acc_reg;

            // Extract mantissa and sign, treat as signed integer
            // Sign bit is MSB, mantissa is LSBs
            assign int_top = {reg_top_element[MX_T_EXP_WIDTH + MX_T_MANT_WIDTH],
                              reg_top_element[MX_T_MANT_WIDTH - 1 : 0]};
            assign int_left = {reg_left_element[MX_L_EXP_WIDTH + MX_L_MANT_WIDTH],
                               reg_left_element[MX_L_MANT_WIDTH - 1 : 0]};

            // Simple handshake
            assign mult_ready = out_result_ready;

            // DSP48E1-friendly MAC pattern: P <= P + A * B in single always block
            // This is the canonical pattern that Vivado infers as MACC_MACRO
            always_ff @(posedge clk) begin
                if (rst || clear_accumulator) begin
                    int_acc_reg <= '0;
                end else if (mult_valid) begin
                    // Full MAC in one statement - optimal for DSP inference
                    (* use_dsp = "yes" *) int_acc_reg <= int_acc_reg + (int_top * int_left);
                end
            end

            // Pack integer result into FP output format (bit reinterpretation for synthesis test)
            (* keep = "true" *) logic [ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] int_out_fp;
            assign int_out_fp = {{(ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH + 1 - INT_ACC_WIDTH){int_acc_reg[INT_ACC_WIDTH-1]}},
                             int_acc_reg};
            assign out_fp = int_out_fp;

        end else begin : gen_fp_mac
            // ======================================================================================
            // ORIGINAL FP MAC MODE
            // ======================================================================================
            logic [MX_L_EXP_WIDTH + MX_L_MANT_WIDTH : 0] block_mult_result, reg_block_mul;
            logic [MX_SCALE_WIDTH - 1 : 0] scale_sum_result, reg_scale_sum;
            logic block_mult_in_valid, block_mult_out_valid;
            logic block_mult_in_ready, block_mult_out_ready;
            logic scale_sum_in_valid, scale_sum_in_ready;
            logic scale_sum_out_valid, scale_sum_out_ready;

            split_n #(
                .N(2)
            ) split_mult_signal (
                .data_in_valid(mult_valid),
                .data_in_ready(mult_ready),
                .data_out_valid({block_mult_in_valid, scale_sum_in_valid}),
                .data_out_ready({block_mult_in_ready, scale_sum_in_ready})
            );

            fp_cp_asym_mult #(
                .EXP_WIDTH_A    (MX_T_EXP_WIDTH),
                .MANT_WIDTH_A   (MX_T_MANT_WIDTH),
                .EXP_WIDTH_B    (MX_L_EXP_WIDTH),
                .MANT_WIDTH_B   (MX_L_MANT_WIDTH)
            ) element_mult (
                .clk(clk),
                .rst(rst),
                .data_in_valid  (block_mult_in_valid),
                .data_in_ready  (block_mult_in_ready),
                .data_a         (reg_top_element),
                .data_b         (reg_left_element),
                .data_out       (block_mult_result),
                .data_out_valid (block_mult_out_valid),
                .data_out_ready (block_mult_out_ready)
            );

            assign scale_sum_result = reg_top_scale + reg_left_scale - SCALE_BIAS;

            fifo #(
                .DATA_WIDTH(MX_SCALE_WIDTH),
                .DEPTH(3)
            ) buffer_scale_sum (
                .clk(clk),
                .rst(rst),
                .data_in        (scale_sum_result),
                .data_in_valid  (scale_sum_in_valid),
                .data_in_ready  (scale_sum_in_ready),
                .data_out       (reg_scale_sum),
                .data_out_valid (scale_sum_out_valid),
                .data_out_ready (scale_sum_out_ready)
            );

            // STAGE 3: Shift the result according to the scale
            logic [ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH : 0] shifted_result, rescaled_result;
            logic converted_result_valid, converted_result_ready;
            logic mxfp_mult_valid, mxfp_mult_ready;

            join2 #() join_mxfp_mult_inst (
              .data_in_ready ({block_mult_out_ready, scale_sum_out_ready}),
              .data_in_valid ({block_mult_out_valid, scale_sum_out_valid}),
              .data_out_valid(mxfp_mult_valid),
              .data_out_ready(mxfp_mult_ready)
            );

            mx_fp_2_fp_unary #(
                .MXFP_EXP_WIDTH     (MX_L_EXP_WIDTH),
                .MXFP_MANT_WIDTH    (MX_L_MANT_WIDTH),
                .MXFP_SCALE_WIDTH   (MX_SCALE_WIDTH),
                .FP_EXP_WIDTH       (ACC_FP_EXP_WIDTH),
                .FP_MANT_WIDTH      (ACC_FP_MANT_WIDTH)
            ) mx_fp_to_fp (
                .clk                (clk),
                .rst                (rst),
                .data_in_valid      (mxfp_mult_valid),
                .data_in_ready      (mxfp_mult_ready),
                .element_data_in    (block_mult_result),
                .scale_data_in      (reg_scale_sum),
                .data_out_valid     (converted_result_valid),
                .data_out_ready     (converted_result_ready),
                .fp_out             (shifted_result)
            );

            // STAGE 4: Accumulation
            logic [ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH : 0] stored_result;
            logic [ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH : 0] acc_result;
            logic acc_result_valid, acc_result_ready;

            fp_fix_accumulator #(
                .MANT_WIDTH (ACC_FP_MANT_WIDTH),
                .EXP_WIDTH  (ACC_FP_EXP_WIDTH)
            ) acc_adder (
                .clk(clk),
                .rst(rst),
                .clear_accumulator(clear_accumulator),
                .data_in_valid  (converted_result_valid),
                .data_in_ready  (converted_result_ready),
                .data_in        (shifted_result),
                .data_out       (out_fp),
                .data_out_valid (),
                .data_out_ready (out_result_ready)
            );
        end
    endgenerate

endmodule