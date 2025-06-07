`timescale 1ns / 1ps
module fp_quantizer #(
    parameter int IN_EXP_WIDTH  = 5,
    parameter int IN_MANT_WIDTH = 10,
    parameter int OUT_EXP_WIDTH = 4,
    parameter int OUT_MANT_WIDTH = 3
)(
    input  logic [1 + IN_EXP_WIDTH + IN_MANT_WIDTH - 1:0] in_fp,
    output logic [1 + OUT_EXP_WIDTH + OUT_MANT_WIDTH - 1:0] out_fp
);

    // Calculate biases
    localparam int IN_BIAS  = (1 << (IN_EXP_WIDTH - 1)) - 1;
    localparam int OUT_BIAS = (1 << (OUT_EXP_WIDTH - 1)) - 1;

    // Unpack input
    logic                  in_sign;
    logic [IN_EXP_WIDTH-1:0]  in_exp;
    logic [IN_MANT_WIDTH-1:0] in_mant;

    logic                  out_sign;
    logic [OUT_EXP_WIDTH-1:0] out_exp;
    logic [OUT_MANT_WIDTH-1:0] out_mant;

    // Intermediate variables
    int exp_unbiased;
    int new_exp;

    always_comb begin
        // Unpack input
        in_sign = in_fp[1 + IN_EXP_WIDTH + IN_MANT_WIDTH - 1];
        in_exp  = in_fp[IN_MANT_WIDTH +: IN_EXP_WIDTH];
        in_mant = in_fp[0 +: IN_MANT_WIDTH];

        // Default output
        out_sign = in_sign;
        out_exp  = '0;
        out_mant = '0;

        // Check special cases
        if (in_exp == {IN_EXP_WIDTH{1'b1}}) begin
            // Inf or NaN
            out_exp  = {OUT_EXP_WIDTH{1'b1}};
            out_mant = (in_mant == 0) ? '0 : {{(OUT_MANT_WIDTH-1){1'b0}}, 1'b1}; // quiet NaN
        end else if (in_exp == '0) begin
            // Zero or subnormal
            out_exp  = '0;
            out_mant = '0;
        end else begin
            // Normal number
            exp_unbiased = int'(in_exp) - IN_BIAS;
            new_exp      = exp_unbiased + OUT_BIAS;

            if (new_exp < 0) begin
                // Underflow
                out_exp  = '0;
                out_mant = '0;
            end else if (new_exp >= (1 << OUT_EXP_WIDTH) - 1) begin
                // Overflow
                out_exp  = {OUT_EXP_WIDTH{1'b1}};
                out_mant = '0;
            end else begin
                out_exp  = logic'(new_exp);
                out_mant = in_mant[IN_MANT_WIDTH-1 -: OUT_MANT_WIDTH]; // truncate
            end
        end

        // Repack
        out_fp = {out_sign, out_exp, out_mant};
    end

endmodule
