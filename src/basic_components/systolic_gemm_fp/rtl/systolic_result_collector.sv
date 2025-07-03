`timescale 1ns / 1ps

/*
Module      : GEMM Systolic Array Result Collector
Timing      : Sequential
Description : 
Status      : Under Development
*/

module systolic_result_collector #(
    // Accumulator Data Format
    parameter ACC_FP_EXP_WIDTH      = 8,
    parameter ACC_FP_MANT_WIDTH     = 7,
    // Dimension
    parameter SYS_ARRAY_AMOUNT      = 2,
    parameter COMPUTE_DIM           = 8
)(
    input   logic clk,
    input   logic rst,
    //  Control
    input   logic control, // 0 for GEMV, 1 for GEMM
    //  GEMM
    input   logic [SYS_ARRAY_AMOUNT - 1 : 0][COMPUTE_DIM- 1: 0][COMPUTE_DIM- 1: 0][ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] gemm_result,
    input   logic [SYS_ARRAY_AMOUNT - 1 : 0]gemm_result_valid,
    output  logic [SYS_ARRAY_AMOUNT - 1 : 0]gemm_result_ready,
    //  GEMV
    input   logic [SYS_ARRAY_AMOUNT - 1 : 0][COMPUTE_DIM- 1: 0][ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] gemv_result,
    input   logic [SYS_ARRAY_AMOUNT - 1 : 0]gemv_result_valid,
    output  logic [SYS_ARRAY_AMOUNT - 1 : 0]gemv_result_ready,
    //  Output Result
    output  logic [SYS_ARRAY_AMOUNT * COMPUTE_DIM - 1: 0][ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] out_fp,
    output  logic out_result_valid,
    input   logic out_result_fetch
);

    logic gemm_valid, gemm_ready;
    logic gemv_valid, gemv_ready;

    join_n #(
        .NUM_HANDSHAKES(SYS_ARRAY_AMOUNT)
    ) join_gemm (
        .data_in_ready (gemm_result_ready),
        .data_in_valid (gemm_result_valid),
        .data_out_valid (gemm_valid),
        .data_out_ready (gemm_ready)
    );
    join_n #(
        .NUM_HANDSHAKES(SYS_ARRAY_AMOUNT)
    ) join_gemv (
        .data_in_ready (gemv_result_ready),
        .data_in_valid (gemv_result_valid),
        .data_out_valid (gemv_valid),
        .data_out_ready (gemv_ready)
    );
    
    logic fifo_in_valid;
    logic fifo_in_ready;

    assign gemm_ready = fifo_in_ready;
    assign gemv_ready = fifo_in_ready;

    logic [SYS_ARRAY_AMOUNT - 1 : 0][COMPUTE_DIM - 1: 0][ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] fifo_in_data;
    logic [$clog2(COMPUTE_DIM) : 0] gemm_store_count;
    logic [SYS_ARRAY_AMOUNT - 1 : 0][COMPUTE_DIM- 1: 0][COMPUTE_DIM- 1: 0][ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] stored_gemm_result;
    logic load_gemm_result;


    always_ff @(posedge clk) begin
        if (rst) begin
            gemm_store_count <= 0;
            load_gemm_result <= 1'b0;
        end else if (gemm_valid) begin
            stored_gemm_result <= gemm_result;
            gemm_store_count <= 0;
            load_gemm_result <= 1'b1;
        end else if (gemm_store_count < COMPUTE_DIM - 1 & fifo_in_ready & load_gemm_result) begin
                gemm_store_count <= gemm_store_count + 1;
                load_gemm_result <= 1'b1;
        end else if (gemm_store_count == COMPUTE_DIM - 1 & load_gemm_result) begin
                load_gemm_result <= 1'b0;
                gemm_store_count <= 0; // Reset after reaching the limit
        end

    end
    
    always_comb begin
        if (load_gemm_result) begin
            // GEMM
            for (int i = 0; i < SYS_ARRAY_AMOUNT; i++) begin
                fifo_in_data[i] = stored_gemm_result[i][gemm_store_count];
            end
            fifo_in_valid = 1'b1;
        end else if (control == 1'b0) begin
            // GEMV
            fifo_in_data = gemv_result;
            fifo_in_valid = gemv_result_valid;
        end else begin
            // Default case, no data to fetch
            fifo_in_data = '0;
            fifo_in_valid = 1'b0;
        end
    end

    // Keep fetching data until the output is valid

    fifo #(
        .DATA_WIDTH((ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH + 1) * SYS_ARRAY_AMOUNT * COMPUTE_DIM),
        .DEPTH(COMPUTE_DIM)
    ) fifo_inst (
        .clk(clk),
        .rst(rst),
        .data_in(fifo_in_data),
        .data_in_valid(fifo_in_valid),
        .data_in_ready(fifo_in_ready),
        .data_out(out_fp),
        .data_out_valid(out_result_valid),
        .data_out_ready(out_result_fetch)
    );



endmodule