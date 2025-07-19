`timescale 1ns / 1ps
// `include "operation.svh"

/*
Module      : FP Reciprocal
Timing      : Combinatorial Logic
Description : This module computes reciprocal of floating point numbers
            : represented with separate mantissa and exponent
Status      : Under Development
*/

module fp_reciprocal #(
    parameter   IN_EXP_WIDTH = 5,
    parameter   IN_FIX_WIDTH = 8,
    parameter   IN_FIX_FRAC_WIDTH = 5,
    parameter   OUT_EXP_WIDTH = -1,
    parameter   OUT_FIX_WIDTH = -1,
    parameter   OUT_FIX_FRAC_WIDTH = -1
)(
    input  logic clk,
    input  logic rst,
    input  logic data_in_valid,
    output logic data_in_ready,
    input logic signed [IN_FIX_WIDTH - 1:0] signed_mant_in,
    input logic signed [IN_EXP_WIDTH - 1:0] signed_exp_in,
    output logic data_out_valid,
    input  logic data_out_ready,
    output logic signed [OUT_EXP_WIDTH - 1:0] signed_exp_out,
    output logic signed [OUT_FIX_WIDTH - 1:0] signed_mant_out
);

    localparam IN_WIDTH = IN_FIX_WIDTH - 1;
    localparam EXTEND_EXP_WIDTH = OUT_EXP_WIDTH + 1;
    localparam RECIPROCAL_MANTISSA_WIDTH = OUT_FIX_WIDTH + IN_FIX_WIDTH; //RANDOM set a large width for the reciprocal mantissa
    localparam LEAD_ZERO_WIDTH = $clog2(RECIPROCAL_MANTISSA_WIDTH + 1);
    
    // --------------
    // P1
    // --------------
    
    logic sign;
    logic unsigned [IN_WIDTH - 1:0] unsigned_mant_in;
    logic signed [RECIPROCAL_MANTISSA_WIDTH - 1:0] unsigned_reciprocal_mantissa;

    logic signed [OUT_EXP_WIDTH - 1:0]      leading_zeros;
    logic signed [EXTEND_EXP_WIDTH - 1:0]   extend_exp;
    logic signed [EXTEND_EXP_WIDTH - 1:0]   exp_difference;
    logic signed [EXTEND_EXP_WIDTH - 1:0]   shift_value;

    logic signed [IN_FIX_WIDTH - 1:0] p1_signed_mant_out;
    logic signed [IN_EXP_WIDTH - 1:0] p1_signed_exp_out;
    logic p1_sign;
    logic p1_recip_mant_data_in_valid, p1_fp_data_in_valid;
    logic p1_recip_mant_data_in_ready, p1_fp_data_in_ready;
    logic p1_recip_mant_data_out_valid, p1_recip_mant_data_out_ready;
    logic signed [RECIPROCAL_MANTISSA_WIDTH - 1:0] p1_unsigned_reciprocal_mantissa;
    logic p1_fp_data_out_valid, p1_fp_data_out_ready;
    logic p1_data_valid, p1_data_ready;

    assign sign = signed_mant_in[IN_FIX_WIDTH - 1];
    assign unsigned_mant_in = (sign) ? ~signed_mant_in + 1 : signed_mant_in;
    // Calculate reciprocal mantissa
    always_comb begin
        if (unsigned_mant_in == 0) begin
            // Handle division by zero - set to maximum representable value
            unsigned_reciprocal_mantissa = (1<<(RECIPROCAL_MANTISSA_WIDTH - 1) - 1);
        end else begin
            // Calculate reciprocal using division
            // This is a simplified approach - in actual hardware, you'd use a divider or lookup table
            unsigned_reciprocal_mantissa = (1<<(RECIPROCAL_MANTISSA_WIDTH - 1)) / unsigned_mant_in;
        end
    end
    // now the unsigned_reciprocal_mantissa becomes *.IN_WIDTH

    split_n #(
        .N(2)
    ) split_reciprocal_signal (
        .data_in_valid(data_in_valid),
        .data_in_ready(data_in_ready),
        .data_out_valid({p1_recip_mant_data_in_valid, p1_fp_data_in_valid}),
        .data_out_ready({p1_recip_mant_data_in_ready, p1_fp_data_in_ready})
    );

    skid_buffer #(
        .DATA_WIDTH(RECIPROCAL_MANTISSA_WIDTH)
    ) buffer_reciprocal_mantissa (
        .clk(clk),
        .rst(rst),
        .data_in        (unsigned_reciprocal_mantissa),
        .data_in_valid  (p1_recip_mant_data_in_valid),
        .data_in_ready  (p1_recip_mant_data_in_ready),
        .data_out       (p1_unsigned_reciprocal_mantissa),
        .data_out_valid (p1_recip_mant_data_out_valid),
        .data_out_ready (p1_recip_mant_data_out_ready)
    );

    skid_buffer #(
        .DATA_WIDTH(IN_FIX_WIDTH + IN_EXP_WIDTH + 1)
    ) buffer_p1_exp_mant (
        .clk(clk),
        .rst(rst),
        .data_in        ({sign, signed_exp_in, signed_mant_in}),
        .data_in_valid  (p1_fp_data_in_valid),
        .data_in_ready  (p1_fp_data_in_ready),
        .data_out       ({p1_sign, p1_signed_exp_out, p1_signed_mant_out}),
        .data_out_valid (p1_fp_data_out_valid),
        .data_out_ready (p1_fp_data_out_ready)
    );

    join2 #() join_reciprocal_signal (
        .data_in_valid({p1_recip_mant_data_out_valid, p1_fp_data_out_valid}),
        .data_in_ready({p1_recip_mant_data_out_ready, p1_fp_data_out_ready}),
        .data_out_valid(p1_data_valid),
        .data_out_ready(p1_data_ready)
    );
    

    // --------------
    // P2
    // --------------

    logic signed [IN_FIX_WIDTH - 1:0] p2_signed_mant_out;
    logic signed [IN_EXP_WIDTH - 1:0] p2_signed_exp_out;
    logic p2_sign;
    logic signed [OUT_EXP_WIDTH - 1:0] p2_signed_exp;
    logic signed [EXTEND_EXP_WIDTH - 1:0] p2_shift_value;
    logic signed [RECIPROCAL_MANTISSA_WIDTH - 1:0] p2_unsigned_reciprocal_mantissa;

    logic p2_fp_data_in_valid, p2_fp_data_in_ready;
    logic p2_fp_data_out_valid, p2_fp_data_out_ready;
    logic p2_recip_mant_data_in_valid,  p2_recip_mant_data_in_ready;
    logic p2_recip_mant_data_out_valid, p2_recip_mant_data_out_ready;
    logic p2_shift_in_valid, p2_shift_in_ready;
    logic p2_shift_out_valid, p2_shift_out_ready;
    logic p2_data_valid, p2_data_ready;

    clz_int #(
        .width_i(RECIPROCAL_MANTISSA_WIDTH)
    ) clz_inst (
        .i_num  (p1_unsigned_reciprocal_mantissa),
        .o_lz   (leading_zeros[LEAD_ZERO_WIDTH - 1:0])
    );
    
    // Calculate leading zeros and extended exponent
    assign extend_exp = -(p1_signed_exp_out - IN_FIX_FRAC_WIDTH) - leading_zeros; // for the int part, [sign, int, *frac]
    
    // Clamp exponent to valid range using signed_clamp module
    signed_clamp #(
        .IN_WIDTH (EXTEND_EXP_WIDTH),
        .OUT_WIDTH(OUT_EXP_WIDTH)
    ) exp_clamp (
        .in_data (extend_exp),
        .out_data(p2_signed_exp)
    );

    // Calculate exponent difference
    assign exp_difference = extend_exp - signed_exp_out;
    
    // Scale mantissa by leading zeros and exponent difference
    assign shift_value = (leading_zeros + exp_difference);

    split_n #(
        .N(3)
    ) split_shift_signal (
        .data_in_valid(p1_data_valid),
        .data_in_ready(p1_data_ready),
        .data_out_valid({p2_shift_in_valid, p2_fp_data_in_valid, p2_recip_mant_data_in_valid}),
        .data_out_ready({p2_shift_in_ready, p2_fp_data_in_ready, p2_recip_mant_data_in_ready})
    );

    skid_buffer #(
        .DATA_WIDTH(EXTEND_EXP_WIDTH)
    ) buffer_shift (
        .clk(clk),
        .rst(rst),
        .data_in        (shift_value),
        .data_in_valid  (p2_shift_in_valid),
        .data_in_ready  (p2_shift_in_ready),
        .data_out       (p2_shift_value),
        .data_out_valid (p2_shift_out_valid),
        .data_out_ready (p2_shift_out_ready)
    );

    skid_buffer #(
        .DATA_WIDTH(IN_FIX_WIDTH + IN_EXP_WIDTH + 1)
    ) buffer_p2_exp_mant (
        .clk(clk),
        .rst(rst),
        .data_in        ({p1_sign, p2_signed_exp, p1_signed_mant_out}),
        .data_in_valid  (p2_fp_data_in_valid),
        .data_in_ready  (p2_fp_data_in_ready),
        .data_out       ({p2_sign, p2_signed_exp_out, p2_signed_mant_out}),
        .data_out_valid (p2_fp_data_out_valid),
        .data_out_ready (p2_fp_data_out_ready)
    );


    skid_buffer #(
        .DATA_WIDTH(RECIPROCAL_MANTISSA_WIDTH)
    ) buffer_p2_reciprocal_mantissa (
        .clk(clk),
        .rst(rst),
        .data_in        (p1_unsigned_reciprocal_mantissa),
        .data_in_valid  (p2_recip_mant_data_in_valid),
        .data_in_ready  (p2_recip_mant_data_in_ready),
        .data_out       (p2_unsigned_reciprocal_mantissa),
        .data_out_valid (p2_recip_mant_data_out_valid),
        .data_out_ready (p2_recip_mant_data_out_ready)
    );


    join_n #(
        .NUM_HANDSHAKES(3)
    ) join_p2_signal (
        .data_in_valid({p2_shift_out_valid, p2_fp_data_out_valid, p2_recip_mant_data_out_valid}),
        .data_in_ready({p2_shift_out_ready, p2_fp_data_out_ready, p2_recip_mant_data_out_ready}),
        .data_out_valid(p2_data_valid),
        .data_out_ready(p2_data_ready)
    );

    // --------------
    // P3
    // --------------

    logic unsigned  [RECIPROCAL_MANTISSA_WIDTH - 1:0] unsigned_output_mantissa_lossless;
    logic signed    [OUT_FIX_WIDTH - 1:0] p3_signed_mant_out;
    logic unsigned  [OUT_FIX_WIDTH - 1 - 1:0] p3_unsigned_mant_out;

    bit_width_aware_left_shift #(
        .IN_WIDTH (RECIPROCAL_MANTISSA_WIDTH),
        .OUT_WIDTH(RECIPROCAL_MANTISSA_WIDTH),
        .SHIFT_WIDTH(EXTEND_EXP_WIDTH)
    ) shift_inst (
        .in_data    (p2_unsigned_reciprocal_mantissa),
        .shift_amt  (p2_shift_value),
        .out_data   (unsigned_output_mantissa_lossless)
    );

    // Clamp mantissa to valid range using signed_clamp module

    round_to_nearest_even #(
        .IN_WIDTH (RECIPROCAL_MANTISSA_WIDTH),
        .OUT_WIDTH(OUT_FIX_FRAC_WIDTH + 1)
    ) mant_round (
        .data_in (unsigned_output_mantissa_lossless),
        .data_out(p3_unsigned_mant_out)
    );

    assign p3_signed_mant_out = (sign) ? -p3_unsigned_mant_out: p3_unsigned_mant_out;

    skid_buffer #(
        .DATA_WIDTH(OUT_EXP_WIDTH + OUT_FIX_WIDTH)
    ) buffer_p3_result_fp (
        .clk(clk),
        .rst(rst),
        .data_in        ({p2_signed_exp_out, p3_signed_mant_out}),
        .data_in_valid  (p2_data_valid),
        .data_in_ready  (p2_data_ready),
        .data_out       ({signed_exp_out, signed_mant_out}),
        .data_out_valid (data_out_valid),
        .data_out_ready (data_out_ready)
    );

endmodule