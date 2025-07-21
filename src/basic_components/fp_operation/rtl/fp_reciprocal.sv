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
    input logic clk,
    input logic rst,
    input logic data_in_valid,
    output logic data_in_ready,
    input logic data_out_ready,
    output logic data_out_valid,
    input logic signed [IN_FIX_WIDTH - 1:0] signed_mant_in,
    input logic signed [IN_EXP_WIDTH - 1:0] signed_exp_in,
    output logic signed [OUT_EXP_WIDTH - 1:0] signed_exp_out,
    output logic signed [OUT_FIX_WIDTH - 1:0] signed_mant_out
);
    logic stall;
    assign stall = !data_out_ready;
    assign data_in_ready = data_out_ready;

    localparam IN_WIDTH = IN_FIX_WIDTH - 1;
    localparam EXTEND_EXP_WIDTH = OUT_EXP_WIDTH + 1;
    localparam RECIPROCAL_MANTISSA_WIDTH = OUT_FIX_WIDTH + IN_FIX_WIDTH; //RANDOM set a large width for the reciprocal mantissa


    logic sign;
    logic unsigned [IN_WIDTH - 1:0] unsigned_mant_in;
    logic signed [RECIPROCAL_MANTISSA_WIDTH - 1:0] unsigned_reciprocal_mantissa;

    data_reg #(
        .DATA_WIDTH(1),
        .REG_N(2)
    ) data_in_reg (
        .data_in(data_in_valid),
        .data_out(data_out_valid),
        .*
    );

    logic signed [OUT_EXP_WIDTH - 1:0] leading_zeros;
    logic signed [EXTEND_EXP_WIDTH - 1:0] extend_exp;
    logic signed [EXTEND_EXP_WIDTH - 1:0] exp_difference;
    logic signed [EXTEND_EXP_WIDTH - 1:0] shift_value;

    logic unsigned [RECIPROCAL_MANTISSA_WIDTH - 1:0] unsigned_output_mantissa_lossless;
    logic unsigned [OUT_FIX_WIDTH - 1 - 1:0] unsigned_mant_out;

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
    logic signed [IN_EXP_WIDTH - 1:0] signed_exp_in_reg;
    logic unsigned [RECIPROCAL_MANTISSA_WIDTH - 1:0] unsigned_reciprocal_mantissa_reg;
    logic sign_reg;
    // reg here
    // now the unsigned_reciprocal_mantissa becomes *.IN_WIDTH
    data_reg #(
        .DATA_WIDTH(RECIPROCAL_MANTISSA_WIDTH + IN_EXP_WIDTH + 1),
        .REG_N(2)
    ) data_reg_inst (
        .data_in({sign, signed_exp_in, unsigned_reciprocal_mantissa}),
        .data_out({sign_reg, signed_exp_in_reg, unsigned_reciprocal_mantissa_reg}),
        .*
    );

    clz_int #(
        .width_i(RECIPROCAL_MANTISSA_WIDTH)
    ) clz_inst (
        .i_num(unsigned_reciprocal_mantissa_reg),
        .o_lz(leading_zeros[$clog2(RECIPROCAL_MANTISSA_WIDTH + 1) - 1:0])
    );
    
    // Calculate leading zeros and extended exponent
    assign extend_exp = -(signed_exp_in_reg - IN_FIX_FRAC_WIDTH) - leading_zeros; // for the int part, [sign, int, *frac]
    
    // Clamp exponent to valid range using signed_clamp module
    signed_clamp #(
        .IN_WIDTH (EXTEND_EXP_WIDTH),
        .OUT_WIDTH(OUT_EXP_WIDTH)
    ) exp_clamp (
        .in_data (extend_exp),
        .out_data(signed_exp_out)
    );
    
    // Calculate exponent difference
    assign exp_difference = extend_exp - signed_exp_out;
    
    // Scale mantissa by leading zeros and exponent difference
    assign shift_value = (leading_zeros + exp_difference);

    bit_width_aware_left_shift #(
        .IN_WIDTH (RECIPROCAL_MANTISSA_WIDTH),
        .OUT_WIDTH(RECIPROCAL_MANTISSA_WIDTH),
        .SHIFT_WIDTH(EXTEND_EXP_WIDTH)
    ) shift_inst (
        .in_data (unsigned_reciprocal_mantissa_reg),
        .shift_amt(shift_value),
        .out_data(unsigned_output_mantissa_lossless)
    );
    // Clamp mantissa to valid range using signed_clamp module
    round_to_nearest_even #(
        .IN_WIDTH (RECIPROCAL_MANTISSA_WIDTH),
        .OUT_WIDTH(OUT_FIX_FRAC_WIDTH + 1)
    ) mant_round (
        .data_in (unsigned_output_mantissa_lossless),
        .data_out(unsigned_mant_out)
    );
    assign signed_mant_out = (sign_reg) ? -unsigned_mant_out: unsigned_mant_out;

endmodule