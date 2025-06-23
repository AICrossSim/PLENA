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

module fp_systolic_mcu #(
    // Data Format
    parameter FP_EXP_WIDTH    = 8,
    parameter FP_MANT_WIDTH   = 7,
    parameter ACC_FP_EXP_WIDTH    = 8,
    parameter ACC_FP_MANT_WIDTH   = 7,
    parameter PROD_EXT_EXP_WIDTH  = 0,
    parameter PROD_EXT_MANT_WIDTH = 0, 
    parameter SYSTOLIC_PROCESSING_OVERHEAD = 4,
    // Dimension
    parameter   M                     = 4,
    parameter   N                     = 4,
    parameter   K                     = 8
)(
    input   logic clk,
    input   logic rst,
    input   M_OP  control,      // 0 for GEMV, 1 for GEMM
    // Multiplicant Matrix 1
    input   logic [K - 1 : 0][FP_EXP_WIDTH + FP_MANT_WIDTH : 0] v1_data,
    input   logic v1_in_valid,
    output  logic v1_in_ready,
    // Multiplier   Matrix 2
    input   logic [K - 1 : 0][FP_EXP_WIDTH + FP_MANT_WIDTH : 0] v2_data,
    input   logic v2_in_valid,
    output  logic v2_in_ready,
    // Vector Product Output
    output  logic [K - 1 : 0][ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH : 0] v_result,
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

    logic [SYS_ARRAY_AMOUNT - 1 : 0][COMPUTE_DIM - 1 : 0][FP_EXP_WIDTH + FP_MANT_WIDTH : 0]     array_top_in_data;
    logic [SYS_ARRAY_AMOUNT - 1 : 0][COMPUTE_DIM - 1 : 0][FP_EXP_WIDTH + FP_MANT_WIDTH : 0]     array_left_in_data;

    logic [SYS_ARRAY_AMOUNT - 1 : 0][COMPUTE_DIM- 1: 0][COMPUTE_DIM- 1: 0][ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] sa_m_result;
    logic [SYS_ARRAY_AMOUNT - 1 : 0][COMPUTE_DIM- 1: 0][COMPUTE_DIM- 1: 0][ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] gebm_result;
    logic [SYS_ARRAY_AMOUNT - 1 : 0] gemm_result_valid, gemm_result_w_ready;

    logic [SYS_ARRAY_AMOUNT - 1 : 0][COMPUTE_DIM- 1: 0][ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] gemv_result;
    logic [SYS_ARRAY_AMOUNT - 1 : 0] gemv_result_valid, gemv_result_w_ready;
    
    // -----------------------------
    // Control and Status Tracking
    // -----------------------------

    logic   load_array_data;
    logic   complete_loading;
    M_OP    control_in_exe;
    logic   sa_control;
    logic   output_reset;


    localparam COUNTER_BIT_WIDTH = $clog2(K);
    logic [COUNTER_BIT_WIDTH : 0] v1_load_counter;
    logic [COUNTER_BIT_WIDTH : 0] v2_load_counter;
    logic [COUNTER_BIT_WIDTH : 0] feed_counter;
    logic complete_v1_load, complete_v2_load;

    
    always_ff @(posedge clk) begin
        if (rst) begin
            v1_load_counter     <= '0;
            complete_v1_load    <= 1'b0;
            v2_load_counter     <= '0;
            complete_v2_load    <= 1'b0;
            output_reset        <= 1'b0;
        end else begin
            // Counter for v1
            if (v1_in_valid & v1_in_ready) begin
                if (v1_load_counter == M - 1) begin
                    v1_load_counter <= '0;
                    complete_v1_load <= 1'b1;
                end else begin
                    v1_load_counter <= v1_load_counter + 'b1;
                    complete_v1_load <= 1'b0;
                end
            end else if (complete_loading) begin
                complete_v1_load <= 1'b0;
            end
            // Counter for v2
            if (v2_in_valid & v2_in_ready) begin
                if (v2_load_counter == M - 1) begin
                    v2_load_counter <= '0;
                    complete_v2_load <= 1'b1;
                end else begin
                    v2_load_counter <= v2_load_counter + 'b1;
                    complete_v2_load <= 1'b0;
                end
            end else if (complete_loading) begin
                complete_v2_load <= 1'b0;
            end
            // Output Reset
            output_reset <= ((control_in_exe == MV_O) || (control_in_exe == MM_O)) & (gemm_result_valid || gemv_result_valid);
        end
    end

    always_comb begin
        if (complete_v1_load & complete_v2_load) begin
            complete_loading = 1'b1;
        end else begin
            complete_loading = 1'b0;
        end
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            control_in_exe   <= STALL_M; 
            load_in_progress     <= 1'b0;
        end else begin
            if ((control_in_exe == STALL_M) & (control != STALL_M)) begin
                control_in_exe <= control;
                load_in_progress <= 1'b1;
            end else if ((control_in_exe != STALL_M) & (control != STALL_M)) begin
                load_in_progress <= 1'b1;
                control_in_exe <= control;
            end else if (complete_loading) begin
                load_in_progress <= 1'b0;
            end
        end
    end

    
    always_comb begin
        if (control_in_exe == MV || control_in_exe == MV_O) begin
            v2_in_ready = v2_for_mv_in_ready;
            v2_for_mv_in_valid = v2_in_valid;
        end else begin
            v2_in_ready = v2_for_mm_in_ready;
            v2_for_mm_in_valid = v2_in_valid;
        end
    end

    assign sa_control = ((control_in_exe == MV) || (control_in_exe == MV_O)); // 0 for GEMM, 1 for GEMV
    logic start_feed_count;
    logic ready_to_load_output;

    always_ff @(posedge clk) begin
        if (rst) begin
            feed_counter            <= '0;
            start_feed_count        <= 1'b0;
            gemv_result_valid       <= 'b0;
            gemm_result_valid       <= 'b0;
            ready_to_load_output    <= 1'b0;
        end else begin
            if (complete_loading & control_in_exe == MM_O) begin
                feed_counter        <= '0;
                start_feed_count    <= 1'b1;
            end else if (start_feed_count) begin
                if (feed_counter == 2 * COMPUTE_DIM + SYSTOLIC_PROCESSING_OVERHEAD) begin
                    feed_counter    <= '0;
                    start_feed_count <= 1'b0;
                    ready_to_load_output <= 1'b1;
                end else begin
                    feed_counter <= feed_counter + 'b1;
                    ready_to_load_output <= 1'b0;
                end
            end else begin
                start_feed_count <= 1'b0;
                ready_to_load_output <= 1'b0;
            end
            gemv_result_valid <= (gemv_result_w_ready & (control_in_exe == MV_O) & ready_to_load_output) ? {SYS_ARRAY_AMOUNT{1'b1}} : 'b0;
            gemm_result_valid <= (gemm_result_w_ready & (control_in_exe == MM_O) & ready_to_load_output) ? {SYS_ARRAY_AMOUNT{1'b1}} : 'b0;
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
            fp_systolic_data_streamer #(
                .FP_EXP_WIDTH     (FP_EXP_WIDTH),
                .FP_MANT_WIDTH    (FP_MANT_WIDTH),
                .COMPUTE_DIM      (COMPUTE_DIM)
            ) top_streamer (
                .clk(clk),
                .rst(rst | output_reset),
                .data_in        (v1_data[i * M +: M]),
                .data_in_valid  (v1_data_in_valid[i]),
                .data_in_ready  (v1_data_in_ready[i]),
                .data_out       (array_top_in_data[i]),
                .data_out_valid (array_top_in_valid[i]),
                .data_out_ready (array_top_in_ready[i])
            );

            fp_systolic_data_streamer #(
                .FP_EXP_WIDTH     (FP_EXP_WIDTH),
                .FP_MANT_WIDTH    (FP_MANT_WIDTH),
                .COMPUTE_DIM      (COMPUTE_DIM)
            ) left_streamer (
                .clk(clk),
                .rst(rst | output_reset),
                .data_in        (v2_data[i * M +: M]),
                .data_in_valid  (v2_data_for_mm_in_valid[i]),
                .data_in_ready  (v2_data_for_mm_in_ready[i]),
                .data_out       (array_left_in_data[i]),
                .data_out_valid (array_left_in_valid[i]),
                .data_out_ready (array_left_in_ready[i])
            );

            fp_systolic_array #(
                .FP_EXP_WIDTH       (FP_EXP_WIDTH),
                .FP_MANT_WIDTH      (FP_MANT_WIDTH),
                .ACC_FP_EXP_WIDTH   (ACC_FP_EXP_WIDTH),
                .ACC_FP_MANT_WIDTH  (ACC_FP_MANT_WIDTH),
                .PROD_EXT_EXP_WIDTH (PROD_EXT_EXP_WIDTH),
                .PROD_EXT_MANT_WIDTH(PROD_EXT_MANT_WIDTH),
                .COMPUTE_DIM        (COMPUTE_DIM)
            ) systolic_array_inst (
                .clk(clk),
                .rst(rst | output_reset),
                .control            (sa_control),
                .in_top_data        (array_top_in_data[i]),
                .in_top_valid       (array_top_in_valid[i]),
                .in_top_ready       (array_top_in_ready[i]),
                .in_left_data       (array_left_in_data[i]),
                .in_left_valid      (array_left_in_valid[i]),
                .in_left_ready      (array_left_in_ready[i]),
                .in_top_v_data      (v2_data[i * M +: M]),
                .in_top_v_valid     (v2_data_for_mv_in_valid[i]),
                .in_top_v_ready     (v2_data_for_mv_in_ready[i]),
                .m_out_fp           (sa_m_result[i]),
                .m_out_ready        (gemm_result_w_ready[i]),
                .v_out_fp           (gemv_result[i]),
                .v_out_ready        (gemv_result_w_ready[i])
            );
        end
    endgenerate

    // -----------------------------
    // Summation Across the Systolic Array
    // -----------------------------

    sum_across_sa #(
        .ACC_FP_MANT_WIDTH(ACC_FP_MANT_WIDTH),
        .ACC_FP_EXP_WIDTH(ACC_FP_EXP_WIDTH),
        .COMPUTE_DIM(COMPUTE_DIM),
        .SYS_ARRAY_AMOUNT(SYS_ARRAY_AMOUNT)
    ) sa_sum_across_inst (
        .clk(clk),
        .rst(rst),
        .m_in_data(sa_m_result),
        .in_valid(gemm_result_valid),
        .in_ready(gemm_result_w_ready),
        .m_out_data(gebm_result),
        .out_valid(),
        .out_ready(v_result_ready)
    );


    // -----------------------------
    // Storing the computed result and write to the Vector SRAM
    // -----------------------------

    // systolic_result_collector #(
    //     .SYS_ARRAY_AMOUNT(SYS_ARRAY_AMOUNT),
    //     .COMPUTE_DIM(M),
    //     .ACC_FP_EXP_WIDTH(ACC_FP_EXP_WIDTH),
    //     .ACC_FP_MANT_WIDTH(ACC_FP_MANT_WIDTH)
    // ) sa_result_collector_inst (
    //     .clk(clk),
    //     .rst(rst),
    //     .control            (sa_control),
    //     .gemm_result        (gebm_result),
    //     .gemm_result_valid  (gemm_result_valid),
    //     .gemm_result_w_ready  (gemm_result_w_ready),
    //     .gemv_result        (gemv_result),
    //     .gemv_result_valid  (gemv_result_valid),
    //     .gemv_result_w_ready  (gemv_result_w_ready),
    //     .out_fp             (v_result),
    //     .out_result_valid   (v_result_valid),
    //     .out_result_fetch   (v_result_ready)
    // );

endmodule