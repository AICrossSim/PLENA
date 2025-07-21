`timescale 1ns / 1ps

/*
Module      : fp_dequantizer
Timing      : Combinatorial Logic
Description : FP_IEEE_Casting
            - Performs dequantising the lower precision floating-point format to a higher precision format.
*/

module fp_ieee_upcasting #(
    parameter int IN_EXP_WIDTH  = 4,
    parameter int IN_MANT_WIDTH = 3,
    parameter int OUT_EXP_WIDTH = 5,
    parameter int OUT_MANT_WIDTH = 10
)(
    input  logic [1 + IN_EXP_WIDTH + IN_MANT_WIDTH - 1:0] in_fp,
    output logic [1 + OUT_EXP_WIDTH + OUT_MANT_WIDTH - 1:0] out_fp
);

    initial begin
        // To ensure the output mantissa is large enough to hold the input mantissa.
        assert (OUT_MANT_WIDTH >= IN_MANT_WIDTH)
            else $error("OUT_MANT_WIDTH must be greater than or equal to IN_MANT_WIDTH");
        assert (OUT_EXP_WIDTH >= IN_EXP_WIDTH)
            else $error("OUT_EXP_WIDTH must be greater than or equal to IN_EXP_WIDTH");
    end

    // Calculate biases
    localparam int IN_BIAS  = (1 << (IN_EXP_WIDTH  - 1)) - 1;
    localparam int OUT_BIAS = (1 << (OUT_EXP_WIDTH - 1)) - 1;

    // Unpack input
    logic                       in_sign;
    logic [IN_EXP_WIDTH-1:0]    in_exp;
    logic [IN_MANT_WIDTH-1:0]   in_mant;

    localparam int LEADING_ZERO_COUNT_WIDTH = $clog2(IN_MANT_WIDTH+1);
    localparam int SHIFT_MAX = OUT_BIAS - IN_BIAS;
    logic [LEADING_ZERO_COUNT_WIDTH-1:0] leading_zero_count;
    logic [IN_MANT_WIDTH:0] in_mant_tobe_shifted;
    logic round_up;
    logic [LEADING_ZERO_COUNT_WIDTH-1:0] shift_amt;
    logic [IN_MANT_WIDTH:0] shifted_mantissa;

    logic                       out_sign;
    logic [OUT_EXP_WIDTH-1:0]   out_exp;
    logic [OUT_MANT_WIDTH-1:0]  out_mant;
    clz_int #(
        .width_i(IN_MANT_WIDTH)
    ) clz_inst (
        .i_num(in_mant_tobe_shifted),
        .o_lz(leading_zero_count)
    );
    assign round_up = in_mant_tobe_shifted[IN_MANT_WIDTH] && (|in_mant_tobe_shifted[IN_MANT_WIDTH-1:0]);
    assign shift_amt = leading_zero_count > SHIFT_MAX ? SHIFT_MAX : leading_zero_count;


    bit_width_aware_left_shift #(
        .IN_WIDTH(IN_MANT_WIDTH + 1),
        .OUT_WIDTH(IN_MANT_WIDTH + 1),
        .SHIFT_WIDTH(LEADING_ZERO_COUNT_WIDTH)
    ) bit_width_aware_left_shift_inst (
        .in_data(in_mant_tobe_shifted),
        .shift_amt(shift_amt),
        .out_data(shifted_mantissa)
    );

    always_comb begin
        // Unpack
        in_sign = in_fp[IN_EXP_WIDTH + IN_MANT_WIDTH];
        in_exp  = in_fp[IN_EXP_WIDTH + IN_MANT_WIDTH - 1 : IN_MANT_WIDTH];
        in_mant = in_fp[IN_MANT_WIDTH - 1:0];

        // Default outputs
        out_sign = in_sign;
        out_exp  = '0;
        out_mant = '0;
        if (in_exp == {IN_EXP_WIDTH{1'b1}}) begin
            // Inf or NaN
            out_exp  = {OUT_EXP_WIDTH{1'b1}};
            out_mant = (in_mant == 0) ? '0 : {{(OUT_MANT_WIDTH-1){1'b0}}, 1'b1}; // quiet NaN
        end else if (in_exp == '0) begin
            // Zero or subnormal
            if (OUT_EXP_WIDTH == IN_EXP_WIDTH) begin
                out_exp  = '0;
                out_mant = {in_mant, {(OUT_MANT_WIDTH - IN_MANT_WIDTH){1'b0}}};
            end else begin
                if (leading_zero_count < SHIFT_MAX) begin
                    out_exp  = OUT_BIAS - IN_BIAS - shift_amt;
                    out_mant = {shifted_mantissa[IN_MANT_WIDTH-1:0], {(OUT_MANT_WIDTH - IN_MANT_WIDTH){1'b0}}};
                end else begin
                    out_exp  = (round_up ? '1 : '0);
                    out_mant = round_up ? {(OUT_MANT_WIDTH){1'b0}} : {OUT_MANT_WIDTH{1'b1}};
                end
            end
        end else begin
            out_exp  = in_exp + OUT_BIAS - IN_BIAS;
            out_mant = {in_mant, {(OUT_MANT_WIDTH - IN_MANT_WIDTH){1'b0}}}; // zero-extend mantissa
        end
        // Repack output
        out_fp = {out_sign, out_exp, out_mant};
    end

endmodule
