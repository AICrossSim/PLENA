`timescale 1ns / 1ps
/*
Module      : fp_ieee_normalize
Timing      : Combinatorial Logic
Description : Give a sign bit, exponent, and mantissa, return a normalized fp number.
              Note: this normalization only count for the case that exponent don't need to over or underflow
              and the mantissa don't need underflow.
              If want to support the casting, there is a casting module which can be connected after.

Input       : 
    signed_mant : the mantissa of the fp number
    signed_exp  : the exponent of the fp number

Output      : 
    fp_out : the normalized fp number

*/

module fp_ieee_normalize #(
    parameter  IN_FIXED_WIDTH = 8,  // For sign bit and implicit 1
    parameter IN_FIXED_FRAC_WIDTH = 5,
    parameter IN_EXP_WIDTH = 5,
    parameter   OUT_MANT_WIDTH = 5,
    localparam   OUT_EXP_WIDTH = IN_EXP_WIDTH + 1
)(
    input  logic signed [IN_FIXED_WIDTH-1:0] signed_mant,
    input  logic signed [IN_EXP_WIDTH-1:0] signed_exp,
    output logic [OUT_EXP_WIDTH + OUT_MANT_WIDTH:0] fp_out
);
    initial begin
        assert (OUT_MANT_WIDTH >= IN_FIXED_WIDTH - 1)
        else $error("OUT_MANT_WIDTH should be greater than IN_FIXED_WIDTH - 1");

        assert (OUT_EXP_WIDTH >= $clog2(OUT_MANT_WIDTH))
        else $error("OUT_EXP_WIDTH should be greater than $clog2(OUT_MANT_WIDTH)");
    end

    localparam signed BIAS = (1 << (OUT_EXP_WIDTH - 1));
    
    logic sign_bit;

    logic [IN_FIXED_WIDTH-1:0] abs_mant;
    logic [$clog2(IN_FIXED_WIDTH)-1:0] leading_zeros;
    logic [IN_FIXED_WIDTH-1:0] unnormed_mantissa;
    logic [OUT_MANT_WIDTH:0] normed_mantissa;
    

    logic signed [$clog2(IN_FIXED_WIDTH)-1:0] shift_amount;
    logic signed [IN_EXP_WIDTH:0] adjusted_exp; 
    
    logic [OUT_EXP_WIDTH-1:0] exp_bits;
    logic [OUT_MANT_WIDTH-1:0] mant_bits;

    clz_int #(
        .width_i(IN_FIXED_WIDTH)
    ) clz_inst (
        .i_num(abs_mant),
        .o_lz(leading_zeros)
    );

    always_comb begin
        // get the sign bit
        sign_bit = signed_mant[IN_FIXED_WIDTH-1];

        // get the mantisssa
        abs_mant = sign_bit ? -signed_mant : signed_mant;
        unnormed_mantissa = abs_mant << (leading_zeros - 1);
        normed_mantissa = {
            unnormed_mantissa[IN_FIXED_WIDTH - 3: 0], 
            {(OUT_MANT_WIDTH - 1 - (IN_FIXED_WIDTH -2)){1'b0}}
        };
        mant_bits = normed_mantissa[IN_MANT_WIDTH-2:IN_MANT_WIDTH-MANT_WIDTH-1]; 

        // get the sign bit
        shift_amount = leading_zeros - 1 - (IN_FIXED_WIDTH - IN_FIXED_FRAC_WIDTH + 2); 
        adjusted_exp = signed_exp - shift_amount;
        exp_bits = (adjusted_exp + BIAS)[OUT_EXP_WIDTH-1:0];
    end
    
    // Assemble final IEEE 754 format
    assign fp_out = {sign_bit, exp_bits, mant_bits};

endmodule