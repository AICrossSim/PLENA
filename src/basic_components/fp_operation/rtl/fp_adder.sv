`timescale 1ns / 1ps
/*
Module      : Floating Point Configurable Precision Adder (With Sign)
Timing      : Combinatorial Logic
Description : FP_Adder
            - The lossy trade-off in FP adder is between output width and exp_difference.
            - (If the exponent difference is large, maintaining full precision may require a wider output to preserve underflowed bits. We choose truncate(floor) the extra, which is also the lossy part.)
*/

module fp_adder #(
    parameter int IN_EXP_WIDTH = 5,
    parameter int IN_FIX_WIDTH = 10,
    parameter int IN_FIX_FRAC_WIDTH = IN_FIX_WIDTH - 1,
    // Amount of bits needed to shift mantissas for alignment
    parameter int OUT_EXP_WIDTH = -1,
    parameter int OUT_FIX_WIDTH = -1,
    parameter int OUT_FIX_FRAC_WIDTH = -1
)(
    input  logic clk,
    input  logic rst,
    input  logic a_in_valid,
    output logic a_in_ready,
    input  logic signed [IN_EXP_WIDTH - 1:0] exp_a,
    input  logic signed [IN_FIX_WIDTH - 1:0] mant_a,
    input  logic b_in_valid,
    output logic b_in_ready,
    input  logic signed [IN_EXP_WIDTH - 1:0] exp_b,
    input  logic signed [IN_FIX_WIDTH - 1:0] mant_b,
    output logic out_valid,
    input  logic out_ready,
    output logic signed [OUT_EXP_WIDTH - 1:0] exp_out,
    output logic signed [OUT_FIX_WIDTH - 1:0] mant_out
);

    localparam int DATA_FIX_WIDTH = OUT_FIX_WIDTH - 1;
    localparam int DATA_FIX_FRAC_WIDTH = OUT_FIX_FRAC_WIDTH;
    initial begin
        assert (IN_FIX_FRAC_WIDTH <= OUT_FIX_FRAC_WIDTH)
            else $error("IN_FIX_FRAC_WIDTH must be less than OUT_FIX_FRAC_WIDTH");
    end

    localparam signed FRAC_DIFF = DATA_FIX_FRAC_WIDTH - IN_FIX_FRAC_WIDTH;

    logic signed [IN_EXP_WIDTH - 1:0]   exp_diff;
    logic signed [OUT_EXP_WIDTH - 1:0]  p1_computed_exp_out;
    logic signed [DATA_FIX_WIDTH - 1:0] mant_a_shifted, mant_b_shifted;
    logic signed [DATA_FIX_WIDTH - 1:0] p1_mant_a_shifted, p1_mant_b_shifted;
    logic signed [DATA_FIX_WIDTH - 1:0] p1_mant_a_dynamic_shifted, p1_mant_b_dynamic_shifted;
    logic signed [IN_EXP_WIDTH - 1:0]   p1_exp_a, p1_exp_b;
    logic signed [IN_EXP_WIDTH - 1:0]   p1_exp_diff;

    logic signed [OUT_EXP_WIDTH - 1:0]  p2_exp_out;
    logic signed [DATA_FIX_WIDTH - 1:0] p2_mant_a_shifted;
    logic signed [DATA_FIX_WIDTH - 1:0] p2_mant_b_shifted;
    
    logic p1_data_in_valid;
    logic p1_data_in_ready;

    logic p2_data_in_valid;
    logic p2_data_in_ready;

    always_comb begin
        mant_a_shifted = mant_a << FRAC_DIFF;
        mant_b_shifted = mant_b << FRAC_DIFF;

        if (exp_a > exp_b) begin
            exp_diff = exp_a - exp_b;
        end else begin
            exp_diff = exp_b - exp_a;
        end

        if (p1_exp_a > p1_exp_b) begin
            p1_mant_a_dynamic_shifted = p1_mant_a_shifted;
            p1_mant_b_dynamic_shifted = p1_mant_b_shifted >>> p1_exp_diff;
            p1_computed_exp_out = p1_exp_a;
        end else begin
            p1_mant_a_dynamic_shifted = p1_mant_a_shifted >>> p1_exp_diff;
            p1_mant_b_dynamic_shifted = p1_mant_b_shifted;
            p1_computed_exp_out = p1_exp_b;
        end
    end

    assign  mant_out = p2_mant_a_shifted + p2_mant_b_shifted;
    assign  exp_out  = p2_exp_out;

    join2 #() join_inst (
      .data_in_valid ({a_in_valid, b_in_valid}),
      .data_in_ready ({a_in_ready, b_in_ready}),
      .data_out_valid(p1_data_in_valid),
      .data_out_ready(p1_data_in_ready)
    );

    skid_buffer #(
        .DATA_WIDTH(IN_EXP_WIDTH * 3 + DATA_FIX_WIDTH * 2)
    ) skid_p1 (
        .clk(clk),
        .rst(rst),
        .data_in_valid  (p1_data_in_valid),
        .data_in_ready  (p1_data_in_ready),
        .data_in        ({exp_a, exp_b, exp_diff, mant_a_shifted, mant_b_shifted}),
        .data_out_valid (p2_data_in_valid),
        .data_out_ready (p2_data_in_ready),
        .data_out       ({p1_exp_a, p1_exp_b, p1_exp_diff, p1_mant_a_shifted, p1_mant_b_shifted})
    );

    
    // assign p1_data_in_ready = 1'b1;
    // always_ff @(posedge clk) begin
    //     if (rst) begin
    //         p1_exp_a            <= 'b0;
    //         p1_exp_b            <= 'b0;
    //         p1_exp_diff         <= 'b0;
    //         p1_mant_a_shifted   <= 'b0;
    //         p1_mant_b_shifted   <= 'b0;
    //         p2_data_in_valid    <= 1'b0;
    //     end else if (p1_data_in_valid) begin
    //         p1_exp_a            <= exp_a;
    //         p1_exp_b            <= exp_b;
    //         p1_exp_diff         <= exp_diff;
    //         p1_mant_a_shifted   <= mant_a_shifted;
    //         p1_mant_b_shifted   <= mant_b_shifted;
    //         p2_data_in_valid    <= p1_data_in_valid;
    //     end else begin
    //         p1_exp_a            <= 'b0;
    //         p1_exp_b            <= 'b0;
    //         p1_exp_diff         <= 'b0;
    //         p1_mant_a_shifted   <= 'b0;
    //         p1_mant_b_shifted   <= 'b0;
    //         p2_data_in_valid    <= p1_data_in_valid;
    //     end
    // end



    skid_buffer #(
        .DATA_WIDTH(IN_EXP_WIDTH + DATA_FIX_WIDTH + DATA_FIX_WIDTH)
    ) skid_p2 (
        .clk(clk),
        .rst(rst),
        .data_in_valid  (p2_data_in_valid),
        .data_in_ready  (p2_data_in_ready),
        .data_in        ({p1_computed_exp_out, p1_mant_a_dynamic_shifted, p1_mant_b_dynamic_shifted}),
        .data_out_valid (out_valid),
        .data_out_ready (out_ready),
        .data_out       ({p2_exp_out, p2_mant_a_shifted, p2_mant_b_shifted})
    );


endmodule