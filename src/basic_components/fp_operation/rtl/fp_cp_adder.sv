`timescale 1ns / 1ps
/*
Module      : Floating Point Configurable Precision Adder (With Sign)
Timing      : Combinatorial Logic
Description : Adds two FP numbers with different exponents and signs.
              Aligns mantissas, preserves full precision (no bits discarded).
              Output format: {sign, exp_out, mant_out}.
              No rounding.
              It needs normalisation.
Status      : Passed Simple Tests
*/

module fp_cp_adder #(
    parameter int EXP_WIDTH = 5,
    parameter int MANT_WIDTH = 10,
    // Amount of bits needed to shift mantissas for alignment
    parameter int EXT_MANT_WIDTH = 4,
    // Need to increase exp width by 1 to handle overflow
    parameter int EXT_EXP_WIDTH = 1
)(
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_a,  // {sign, exp, mant}
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_b,
    output logic [EXP_WIDTH + EXT_EXP_WIDTH + MANT_WIDTH + EXT_MANT_WIDTH : 0] data_out
);

    localparam int BIAS = (1 << (EXP_WIDTH - 1)) - 1;
    localparam int NEW_BIAS = (1 << ((EXP_WIDTH + EXT_EXP_WIDTH) - 1)) - 1;
    localparam int UPDATED_BIAS = NEW_BIAS - BIAS;

    // Bit field declarations
    logic sign_a, sign_b, sign_res;
    logic [EXP_WIDTH-1:0] exp_a, exp_b;
    logic [MANT_WIDTH-1:0] mant_a, mant_b;

    logic [MANT_WIDTH + EXT_MANT_WIDTH + 1:0] full_mant_a, full_mant_b;
    logic [MANT_WIDTH + EXT_MANT_WIDTH + 1:0] mant_a_shifted, mant_b_shifted;
    logic [MANT_WIDTH + EXT_MANT_WIDTH + 1:0] mant_sum, mant_out;

    logic [EXP_WIDTH - 1:0] exp_diff;
    logic [EXP_WIDTH - 1:0] exp_max;
    logic [EXP_WIDTH + EXT_EXP_WIDTH - 1:0] exp_out;

    localparam EXP_SHIFT_SUB_WIDTH = $clog2(MANT_WIDTH + 3);
    logic [EXP_SHIFT_SUB_WIDTH -1:0] exp_shift_sub;

    always_comb begin
        // Extract sign, exponent, mantissa
        sign_a = data_a[EXP_WIDTH + MANT_WIDTH];
        exp_a  = data_a[EXP_WIDTH + MANT_WIDTH - 1 : MANT_WIDTH];
        mant_a = data_a[MANT_WIDTH-1:0];

        sign_b = data_b[EXP_WIDTH + MANT_WIDTH];
        exp_b  = data_b[EXP_WIDTH + MANT_WIDTH -1 : MANT_WIDTH];
        mant_b = data_b[MANT_WIDTH-1:0];

        // Add implicit 1 and pad for alignment
        full_mant_a = {2'b01, mant_a, {EXT_MANT_WIDTH{1'b0}}};
        full_mant_b = {2'b01, mant_b, {EXT_MANT_WIDTH{1'b0}}};

        // Align mantissas
        if (exp_a > exp_b) begin
            exp_diff       = exp_a - exp_b;
            mant_a_shifted = full_mant_a;
            mant_b_shifted = full_mant_b >> exp_diff;
            exp_max        = exp_a;
        end else begin
            exp_diff       = exp_b - exp_a;
            mant_a_shifted = full_mant_a >> exp_diff;
            mant_b_shifted = full_mant_b;
            exp_max        = exp_b;
        end

        // Addition
        if (sign_a == sign_b) begin
            mant_sum = mant_a_shifted + mant_b_shifted;
            sign_res = sign_a;
            // Mantissa overflow handling (e.g., normalisation)
            if (mant_sum[MANT_WIDTH + EXT_MANT_WIDTH + 1] == 1'b1) begin
                if (EXT_EXP_WIDTH == 0) begin
                    mant_out    = mant_sum >> 1;
                    if (exp_max == {EXP_WIDTH{1'b1}}) begin
                        // Handle overflow case
                        exp_out = {EXP_WIDTH{1'b1}}; // Set to max exponent
                    end else begin
                        exp_out = exp_max + 'b1;
                    end
                end else begin
                    mant_out = mant_sum >> 1;
                    exp_out = {{EXT_EXP_WIDTH{1'b0}}, exp_max} + 'b1 + UPDATED_BIAS[EXP_WIDTH + EXT_EXP_WIDTH - 1:0];
                end

            end else begin
                mant_out = mant_sum;
                exp_out = {{EXT_EXP_WIDTH{1'b0}}, exp_max} + UPDATED_BIAS[EXP_WIDTH + EXT_EXP_WIDTH - 1:0];
            end
        end 
        // Subtraction
        else begin
            if (mant_a_shifted >= mant_b_shifted) begin
                mant_sum = mant_a_shifted - mant_b_shifted;
                sign_res = sign_a;
            end else begin
                mant_sum = mant_b_shifted - mant_a_shifted;
                sign_res = sign_b;
            end
            mant_out = mant_sum << exp_shift_sub;
            exp_out = {{EXT_EXP_WIDTH{1'b0}}, exp_max} - exp_shift_sub + UPDATED_BIAS[EXP_WIDTH + EXT_EXP_WIDTH - 1:0];
        end

        // Output final packed value: {sign, exponent, extended mantissa}
        data_out = {sign_res, exp_out, mant_out[MANT_WIDTH + EXT_MANT_WIDTH - 1:0]};
    end


    // Counting Num of zeros for subtraction
    clz_int #(
        .width_i(MANT_WIDTH + EXT_MANT_WIDTH + 1)
    ) clz_inst (
        .i_num(mant_sum[MANT_WIDTH + EXT_MANT_WIDTH:0]),
        .o_lz(exp_shift_sub)
    );

endmodule
