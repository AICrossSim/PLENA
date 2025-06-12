`timescale 1ns / 1ps

/*
Module      : Systolic Array Based Matrix Compute Unit (MCU)
Timing      : Sequential
Description : It supports both for GEMM and GEMV operations.
            : (M, K) x (K, N) = (M, N)
            : (M, K) x (K, 1) = (M, 1)
            :  where M and N is the Batch_Size , K is the MLEN 
            : Every CLK, it will receive (K) vector as multiplicand and (K) vector as multiplier.
            : During the write process, output single row per clk.
Status      : Under Development
*/

module systolic_mcu #(
    // MX-FP Data Format
    parameter   MXFP_EXP_WIDTH        = 4,
    parameter   MXFP_MANT_WIDTH       = 3,
    parameter   MXFP_SCALE_WIDTH      = 8,
    parameter   BLOCK_DIM             = 4,
    // Accumulator Data Format
    parameter   ACC_FP_EXP_WIDTH      = 8,
    parameter   ACC_FP_MANT_WIDTH     = 7,
    // Dimension
    parameter   M                     = 4,
    parameter   N                     = 4,
    parameter   K                     = 8, 
    localparam  ROW_BLOCK_NUM         = K / BLOCK_DIM
)(
    input   logic clk,
    input   logic rst,
    input   M_OP  control,      // 0 for GEMV, 1 for GEMM
    // Multiplicant Matrix 1
    input   logic [K - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] v1_element,
    input   logic [ROW_BLOCK_NUM - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0] v1_scale,
    input   logic v1_in_valid,
    output  logic v1_in_ready,
    // Multiplier   Matrix 2
    input   logic [K - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] v2_element,
    input   logic [ROW_BLOCK_NUM - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0] v2_scale,
    input   logic v2_in_valid,
    output  logic v2_in_ready,
    // Vector Product Output
    output  logic [M - 1 : 0][ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH : 0] v_result,
    output  logic v_result_valid,
    input   logic v_result_ready,
    output  logic load_in_progress
);

    initial begin
        if (M != N) begin
            $error("Systolic MCU only supports M == N, but got M = %0d, N = %0d", M, N);
            $finish;
        end
    end

    localparam SYS_ARRAY_AMOUNT = K / M;
    localparam COMPUTE_DIM = M;

    // -----------------------------
    // Data Wires Declaration
    // -----------------------------

    logic [SYS_ARRAY_AMOUNT - 1 : 0] v1_data_in_valid, v1_data_in_ready;
    logic v2_for_mm_in_valid, v2_for_mm_in_ready;
    logic [SYS_ARRAY_AMOUNT - 1 : 0] v2_data_for_mm_in_valid, v2_data_for_mm_in_ready;
    logic v2_for_mv_in_valid, v2_for_mv_in_ready;
    logic [SYS_ARRAY_AMOUNT - 1 : 0] v2_data_for_mv_in_valid, v2_data_for_mv_in_ready;

    logic [SYS_ARRAY_AMOUNT - 1 : 0] array_top_in_valid, array_top_in_ready;
    logic [SYS_ARRAY_AMOUNT - 1 : 0] array_left_in_valid, array_left_in_ready;

    logic [SYS_ARRAY_AMOUNT - 1 : 0][COMPUTE_DIM - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] array_top_in_element;
    logic [SYS_ARRAY_AMOUNT - 1 : 0][ROW_BLOCK_NUM - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0]           array_top_in_scale;
    logic [SYS_ARRAY_AMOUNT - 1 : 0][COMPUTE_DIM - 1 : 0][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] array_left_in_element;
    logic [SYS_ARRAY_AMOUNT - 1 : 0][ROW_BLOCK_NUM - 1 : 0][MXFP_SCALE_WIDTH - 1 : 0]           array_left_in_scale;

    logic [SYS_ARRAY_AMOUNT - 1 : 0][COMPUTE_DIM- 1: 0][COMPUTE_DIM- 1: 0][ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] gemm_result;
    logic [SYS_ARRAY_AMOUNT - 1 : 0] gemm_result_valid, gemm_result_ready;

    logic [SYS_ARRAY_AMOUNT - 1 : 0][COMPUTE_DIM- 1: 0][ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] gemv_result;
    logic [SYS_ARRAY_AMOUNT - 1 : 0] gemv_result_valid, gemv_result_ready;
    
    // -----------------------------
    // Control and Status Tracking
    // -----------------------------

    logic   load_array_data;
    logic   complete_loading;
    M_OP    control_under_exe, control_in_queue;
    logic   gemm_en;

    always_ff @(posedge clk) begin
        if (rst) begin
            control_under_exe    <= STALL_M; 
            control_in_queue     <= STALL_M;
            load_in_progress     <= 1'b0;
        end else begin
            if ((control_under_exe == STALL_M) & (control != STALL_M)) begin
                control_under_exe <= control;
                load_in_progress <= 1'b1;
            end else if ((control_under_exe != STALL_M) & (control != STALL_M)) begin
                control_in_queue <= control;
                load_in_progress <= 1'b1;
            end else if (complete_loading) begin
                if (control_in_queue == STALL_M) begin
                    control_under_exe <= STALL_M;
                end else begin
                    control_under_exe <= control_in_queue;
                end
                load_in_progress <= 1'b0;
            end
        end
    end

    always_comb begin
        if (control_under_exe == MV || control_under_exe == MV_O) begin
            v2_in_ready = v2_for_mv_in_ready;
            v2_for_mv_in_valid = v2_in_valid;
        end else begin
            v2_in_ready = v2_for_mm_in_ready;
            v2_for_mm_in_valid = v2_in_valid;
        end
    end

    assign gemm_en = ((control_under_exe == MM) || (control_under_exe == MM_O));

    localparam COUNTER_BIT_WIDTH = $clog2(K);
    logic [COUNTER_BIT_WIDTH : 0] v1_load_counter;
    logic [COUNTER_BIT_WIDTH : 0] v2_load_counter;
    logic complete_v1_load, complete_v2_load;

    always_ff @(posedge clk) begin
        if (rst) begin
            v1_load_counter <= '0;
            complete_v1_load <= 1'b0;
        end else if (v1_in_valid & v1_in_ready) begin
            if (v1_load_counter == K - 1) begin
                v1_load_counter <= '0;
                complete_v1_load <= 1'b1;
            end else begin
                v1_load_counter <= v1_load_counter + 'b1;
                complete_v1_load <= 1'b0;
            end
        end else if (complete_loading) begin
            complete_v1_load <= 1'b0;
        end
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            v2_load_counter <= '0;
            complete_v2_load <= 1'b0;
        end else if (v2_in_valid & v2_in_ready) begin
            if (v2_load_counter == K - 1) begin
                v2_load_counter <= '0;
                complete_v2_load <= 1'b1;
            end else begin
                v2_load_counter <= v2_load_counter + 'b1;
                complete_v2_load <= 1'b0;
            end
        end else if (complete_loading) begin
            complete_v2_load <= 1'b0;
        end
    end

    always_comb begin
        if (complete_v1_load & complete_v2_load) begin
            complete_loading = 1'b1;
        end else begin
            complete_loading = 1'b0;
        end
    end


    // -----------------------------
    // Systolic Array Computation Unit
    // -----------------------------

    generate;
        split_n #(
            .N(SYS_ARRAY_AMOUNT)
        ) v1_handshake (
            .data_in_valid  (v1_in_valid),
            .data_in_ready  (v1_in_ready),
            .data_out_valid (v1_data_in_valid),
            .data_out_ready (v1_data_in_ready)
        );

        split_n #(
            .N(SYS_ARRAY_AMOUNT)
        ) v2_handshake (
            .data_in_valid  (v2_for_mm_in_valid),
            .data_in_ready  (v2_for_mm_in_ready),
            .data_out_valid (v2_data_for_mm_in_valid),
            .data_out_ready (v2_data_for_mm_in_ready)
        );

        split_n #(
            .N(SYS_ARRAY_AMOUNT)
        ) vect_handshake (
            .data_in_valid(v2_for_mv_in_valid),
            .data_in_ready(v2_for_mv_in_ready),
            .data_out_valid(v2_data_for_mv_in_valid),
            .data_out_ready(v2_data_for_mv_in_ready)
        );

        for (genvar i = 0; i < SYS_ARRAY_AMOUNT; i++) begin
            systolic_data_streamer #(
                .MXFP_EXP_WIDTH     (MXFP_EXP_WIDTH),
                .MXFP_MANT_WIDTH    (MXFP_MANT_WIDTH),
                .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH),
                .BLOCK_DIM          (BLOCK_DIM),
                .ACC_FP_EXP_WIDTH   (ACC_FP_EXP_WIDTH),
                .ACC_FP_MANT_WIDTH  (ACC_FP_MANT_WIDTH),
                .COMPUTE_DIM        (COMPUTE_DIM)
            ) top_streamer (
                .clk(clk),
                .rst(rst),
                .data_elem_in   (v1_element[i * M +: M]),
                .data_scale_in  (v1_scale[i * (ROW_BLOCK_NUM / SYS_ARRAY_AMOUNT) +: (ROW_BLOCK_NUM / SYS_ARRAY_AMOUNT)]),
                .data_in_valid  (v1_data_in_valid[i]),
                .data_in_ready  (v1_data_in_ready[i]),
                .data_elem_out  (array_top_in_element[i]),
                .data_scale_out (array_top_in_scale[i]),
                .data_out_valid (array_top_in_valid[i]),
                .data_out_ready (array_top_in_ready[i])
            );

            systolic_data_streamer #(
                .MXFP_EXP_WIDTH     (MXFP_EXP_WIDTH),
                .MXFP_MANT_WIDTH    (MXFP_MANT_WIDTH),
                .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH),
                .BLOCK_DIM          (BLOCK_DIM),
                .ACC_FP_EXP_WIDTH   (ACC_FP_EXP_WIDTH),
                .ACC_FP_MANT_WIDTH  (ACC_FP_MANT_WIDTH),
                .COMPUTE_DIM        (COMPUTE_DIM)
            ) left_streamer (
                .clk(clk),
                .rst(rst),
                .data_elem_in   (v2_element[i * M +: M]),
                .data_scale_in  (v2_scale[i * (ROW_BLOCK_NUM / SYS_ARRAY_AMOUNT) +: (ROW_BLOCK_NUM / SYS_ARRAY_AMOUNT)]),
                .data_in_valid  (v2_data_for_mm_in_valid[i]),
                .data_in_ready  (v2_data_for_mm_in_ready[i]),
                .data_elem_out  (array_left_in_element[i]),
                .data_scale_out (array_left_in_scale[i]),
                .data_out_valid (array_left_in_valid[i]),
                .data_out_ready (array_left_in_ready[i])
            );

            systolic_array #(
                .MXFP_EXP_WIDTH     (MXFP_EXP_WIDTH),
                .MXFP_MANT_WIDTH    (MXFP_MANT_WIDTH),
                .MXFP_SCALE_WIDTH   (MXFP_SCALE_WIDTH),
                .BLOCK_DIM          (BLOCK_DIM),
                .ACC_FP_EXP_WIDTH   (ACC_FP_EXP_WIDTH),
                .ACC_FP_MANT_WIDTH  (ACC_FP_MANT_WIDTH),
                .COMPUTE_DIM        (COMPUTE_DIM)
            ) systolic_array_inst (
                .clk(clk),
                .rst(rst),
                .control            (gemm_en),
                .in_top_element     (array_top_in_element[i]),
                .in_top_scale       (array_top_in_scale[i]),
                .in_top_valid       (array_top_in_valid[i]),
                .in_top_ready       (array_top_in_ready[i]),
                .in_left_element    (array_left_in_element[i]),
                .in_left_scale      (array_left_in_scale[i]),
                .in_left_valid      (array_left_in_valid[i]),
                .in_left_ready      (array_left_in_ready[i]),
                .in_top_v_element   (v2_element[i * M +: M]),
                .in_top_v_scale     (v2_scale[i * (ROW_BLOCK_NUM / SYS_ARRAY_AMOUNT) +: (ROW_BLOCK_NUM / SYS_ARRAY_AMOUNT)]),
                .in_top_v_valid     (v2_data_for_mv_in_valid[i]),
                .in_top_v_ready     (v2_data_for_mv_in_ready[i]),
                .m_out_fp           (gemm_result[i]),
                .m_out_valid        (gemm_result_valid[i]),
                .m_out_ready        (gemm_result_ready[i]),
                .v_out_fp           (gemv_result[i]),
                .v_out_valid        (gemv_result_valid[i]),
                .v_out_ready        (gemv_result_ready[i])
            );
        end
    endgenerate

    // -----------------------------
    // Storing the computed result and write to the Vector SRAM
    // -----------------------------

    sa_result_collector #(
        .SYS_ARRAY_AMOUNT(SYS_ARRAY_AMOUNT),
        .COMPUTE_DIM(M),
        .ACC_FP_EXP_WIDTH(ACC_FP_EXP_WIDTH),
        .ACC_FP_MANT_WIDTH(ACC_FP_MANT_WIDTH)
    ) sa_result_collector_inst (
        .clk(clk),
        .rst(rst),
        .control            (gemm_en),
        .gemm_result        (gemm_result),
        .gemm_result_valid  (gemm_result_valid),
        .gemm_result_ready  (gemm_result_ready),
        .gemv_result        (gemv_result),
        .gemv_result_valid  (gemv_result_valid),
        .gemv_result_ready  (gemv_result_ready),
        .out_fp             (v_result),
        .out_result_valid   (v_result_valid),
        .out_result_ready   (v_result_ready)
    );

endmodule