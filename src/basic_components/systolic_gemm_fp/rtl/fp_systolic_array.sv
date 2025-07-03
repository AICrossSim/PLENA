`timescale 1ns / 1ps

/*
Module      : FP Systolic Array
Timing      : Sequential
Description : It can be used for both GEMM and GEMV operations.
Status      : Under Development
*/

module fp_systolic_array #(
    parameter FP_EXP_WIDTH    = 8,
    parameter FP_MANT_WIDTH   = 7,
    parameter ACC_FP_EXP_WIDTH    = 8,
    parameter ACC_FP_MANT_WIDTH   = 7,
    parameter PROD_EXT_EXP_WIDTH  = 0,
    parameter PROD_EXT_MANT_WIDTH = 0, 
    // Dimension
    parameter COMPUTE_DIM           = 8
)(

    input   logic clk,
    input   logic rst,
    input   logic control,

    // Input from Top Array
    input   logic [COMPUTE_DIM - 1: 0][FP_EXP_WIDTH + FP_MANT_WIDTH : 0] in_top_data,
    input   logic in_top_valid,
    output  logic in_top_ready,

    // Input from Left Array
    input   logic [COMPUTE_DIM - 1: 0][FP_EXP_WIDTH + FP_MANT_WIDTH : 0] in_left_data,
    input   logic in_left_valid,
    output  logic in_left_ready,

    // Input from Vector Array
    input   logic [COMPUTE_DIM - 1: 0][FP_EXP_WIDTH + FP_MANT_WIDTH : 0] in_top_v_data,
    input   logic in_top_v_valid,
    output  logic in_top_v_ready,

    // Output GEMM
    output  logic [COMPUTE_DIM- 1: 0][COMPUTE_DIM - 1: 0] [ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] m_out_fp,
    input   logic m_out_ready,

    // Output GEMV
    output  logic [COMPUTE_DIM - 1: 0] [ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] v_out_fp,
    input   logic v_out_ready
);

    logic [FP_EXP_WIDTH + FP_MANT_WIDTH : 0]  rowwise_data_transfer_data       [COMPUTE_DIM - 1:0][COMPUTE_DIM :0];
    logic [FP_EXP_WIDTH + FP_MANT_WIDTH : 0]  columnwise_data_transfer_data    [COMPUTE_DIM : 0][COMPUTE_DIM - 1:0];

    logic [COMPUTE_DIM- 1: 0] [COMPUTE_DIM - 1: 0] [ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] result_values;
    logic [COMPUTE_DIM- 1: 0] [COMPUTE_DIM - 1: 0] result_ready;
    logic out_result_ready;
    logic mult_valid, mult_ready;
    logic system_right_shift_valid, system_down_shift_valid;
    logic [COMPUTE_DIM- 1: 0] [COMPUTE_DIM - 1: 0] pe_compute_ready;

    join2 #() mult_signal_join (
        .data_in_valid({in_top_valid, in_left_valid}),
        .data_in_ready({in_top_ready, in_left_ready}),
        .data_out_valid(mult_valid),
        .data_out_ready(mult_ready)
    );


    // Fill the Front Top Row and Left Column with the input data
    generate;
        for (genvar i = 0; i < COMPUTE_DIM; i = i + 1) begin : fill_with_input_data
            assign columnwise_data_transfer_data    [0][i]  = in_top_data[i];
            assign rowwise_data_transfer_data       [i][0]  = in_left_data[i];
        end
        assign mult_ready = &pe_compute_ready;
        assign system_down_shift_valid = in_top_valid & in_top_ready;
        assign system_right_shift_valid = in_left_valid & in_left_ready;
    endgenerate


    // Computation
    generate;
        for (genvar i = 0; i < COMPUTE_DIM; i = i + 1) begin : row_inx
            for (genvar j = 0; j < COMPUTE_DIM; j = j + 1) begin : col_idx
                if (i == 0) begin
                    fp_first_row_pe #(
                        .FP_EXP_WIDTH       (FP_EXP_WIDTH),
                        .FP_MANT_WIDTH      (FP_MANT_WIDTH),
                        .ACC_FP_EXP_WIDTH   (ACC_FP_EXP_WIDTH),
                        .ACC_FP_MANT_WIDTH  (ACC_FP_MANT_WIDTH),
                        .PROD_EXT_EXP_WIDTH (PROD_EXT_EXP_WIDTH),
                        .PROD_EXT_MANT_WIDTH(PROD_EXT_MANT_WIDTH)
                    ) first_row_pe_init (
                        .clk(clk),
                        .rst(rst),
                        .control(control),
                        .in_top_data        (columnwise_data_transfer_data[i][j]),
                        .system_top_valid   (system_down_shift_valid),
                        .in_left_data       (rowwise_data_transfer_data[i][j]),
                        .system_left_valid  (system_right_shift_valid),
                        .mult_valid         (mult_valid),
                        .mult_ready         (pe_compute_ready[i][j]),
                        .in_top_v_data      (in_top_v_data[j]),
                        .out_bottom_data    (columnwise_data_transfer_data[i+1][j]),
                        .out_right_data     (rowwise_data_transfer_data[i][j+1]),
                        .out_fp             (m_out_fp[i][j]),
                        .out_result_ready   (out_result_ready)
                    );
                end else begin
                    fp_default_pe #(
                        .FP_EXP_WIDTH       (FP_EXP_WIDTH),
                        .FP_MANT_WIDTH      (FP_MANT_WIDTH),
                        .ACC_FP_EXP_WIDTH   (ACC_FP_EXP_WIDTH),
                        .ACC_FP_MANT_WIDTH  (ACC_FP_MANT_WIDTH),
                        .PROD_EXT_EXP_WIDTH (PROD_EXT_EXP_WIDTH),
                        .PROD_EXT_MANT_WIDTH(PROD_EXT_MANT_WIDTH)
                    ) default_pe_init (
                        .clk(clk),
                        .rst(rst),
                        .in_top_data        (columnwise_data_transfer_data[i][j]),
                        .system_top_valid   (system_down_shift_valid),
                        .in_left_data       (rowwise_data_transfer_data[i][j]),
                        .system_left_valid  (system_right_shift_valid),
                        .mult_valid         (mult_valid),
                        .mult_ready         (pe_compute_ready[i][j]),
                        .out_bottom_data    (columnwise_data_transfer_data[i + 1][j]),
                        .out_right_data     (rowwise_data_transfer_data[i][j + 1]),
                        .out_fp             (m_out_fp[i][j]),
                        .out_result_ready   (out_result_ready)
                    );
                end
            end
        end
    endgenerate

    assign v_out_fp         = m_out_fp[0];
    assign out_result_ready = (control == 1'b0) ? m_out_ready : v_out_ready;

endmodule