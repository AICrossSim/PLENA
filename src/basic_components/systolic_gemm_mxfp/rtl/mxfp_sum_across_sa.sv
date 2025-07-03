`timescale 1ns / 1ps

/*
Module      : Summation across Systolic Array
Timing      : Sequential, adder tree.
*/

module mxfp_sum_across_sa #(
    parameter ACC_FP_MANT_WIDTH = 8,
    parameter ACC_FP_EXP_WIDTH = 7,
    parameter COMPUTE_DIM = 8,
    parameter SYS_ARRAY_AMOUNT = 4
)(
    input logic clk,
    input logic rst,

    // Input from Systolic Array
    input logic     [SYS_ARRAY_AMOUNT - 1 : 0][COMPUTE_DIM- 1: 0][COMPUTE_DIM- 1: 0][ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] m_in_data,
    input logic     [SYS_ARRAY_AMOUNT - 1 : 0] in_valid,
    output logic    [SYS_ARRAY_AMOUNT - 1 : 0] in_ready,

    // Output to Top Level
    output  logic [COMPUTE_DIM- 1: 0][COMPUTE_DIM- 1: 0][ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] m_out_data,
    output  logic out_valid,
    input   logic out_ready
);

    logic input_array_valid, input_array_ready;
    logic [COMPUTE_DIM * COMPUTE_DIM- 1: 0] per_pe_valid, per_pe_ready;
    logic [COMPUTE_DIM * COMPUTE_DIM- 1: 0] per_pe_acc_valid, per_pe_acc_ready;
    logic [COMPUTE_DIM- 1: 0][COMPUTE_DIM- 1: 0][ACC_FP_MANT_WIDTH + ACC_FP_EXP_WIDTH : 0] accumulated_data;

generate;

    join_n #(
        .NUM_HANDSHAKES(SYS_ARRAY_AMOUNT)
    ) join_input_array (
        .data_in_valid(in_valid),
        .data_in_ready(in_ready),
        .data_out_valid(input_array_valid),
        .data_out_ready(input_array_ready)
    );

    split_n #(
        .N(COMPUTE_DIM * COMPUTE_DIM)
    ) split_input_array (
        .data_in_valid(input_array_valid),
        .data_in_ready(input_array_ready),
        .data_out_valid(per_pe_valid),
        .data_out_ready(per_pe_ready)
    );

    for (genvar i = 0; i < COMPUTE_DIM; i++) begin : sum_across_row
        for (genvar j = 0; j < COMPUTE_DIM; j++) begin : sum_across_col
            logic [SYS_ARRAY_AMOUNT - 1 : 0][ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH : 0] adder_in_data;
            always_comb
                for (int k = 0; k < SYS_ARRAY_AMOUNT; k++) 
                    adder_in_data[k] = m_in_data[k][i][j];
            
            fp_adder_tree #(
                .VEC_DIM(SYS_ARRAY_AMOUNT),
                .IN_EXP_WIDTH(ACC_FP_EXP_WIDTH),
                .IN_MAN_WIDTH(ACC_FP_MANT_WIDTH),
                .EXT_MANT_WIDTH_PER_LAYER(0),
                .EXT_EXP_BITS_PER_LAYER(0)
            ) per_pe_adder_tree (
                .clk(clk),
                .rst(rst),
                .data_in        (adder_in_data),
                .data_in_valid  (per_pe_valid[i * COMPUTE_DIM + j]),
                .data_in_ready  (per_pe_ready[i * COMPUTE_DIM + j]),
                .data_out       (accumulated_data[i][j]),
                .data_out_valid (per_pe_acc_valid[i * COMPUTE_DIM + j]),
                .data_out_ready (per_pe_acc_ready[i * COMPUTE_DIM + j])
            );
        end
    end

    logic acc_out_valid, acc_out_ready;
    
    join_n #(
        .NUM_HANDSHAKES(COMPUTE_DIM * COMPUTE_DIM)
    ) join_acc_result (
        .data_in_valid(per_pe_acc_valid),
        .data_in_ready(per_pe_acc_ready),
        .data_out_valid(acc_out_valid),
        .data_out_ready(acc_out_ready)
    );


    skid_buffer #(
        .DATA_WIDTH(COMPUTE_DIM * COMPUTE_DIM * (ACC_FP_EXP_WIDTH + ACC_FP_MANT_WIDTH + 1))
    ) skid_buffer_inst (
        .clk(clk),
        .rst(rst),
        .data_in            (accumulated_data),
        .data_in_valid      (acc_out_valid),
        .data_in_ready      (acc_out_ready),
        .data_out           (m_out_data),
        .data_out_valid     (out_valid),
        .data_out_ready     (out_ready)
    );

endgenerate

    

endmodule