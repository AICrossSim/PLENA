/*
Module      : fp_ieee_normalize
Timing      : Combinatorial Logic
Description : Give a sign bit,
            : 1.MANT_WIDTH of unsigned mantissa 
            : already been biased exponent.
            : return a normalized fp number.
Status      : Under Development
*/

module fp_ieee_normalize #(
    parameter   EXP_WIDTH = 5,
    parameter   MANT_WIDTH = 10,
    parameter   IN_MANT_WIDTH = MANT_WIDTH + 2  // For sign bit and implicit 1
)(
    input  logic signed [IN_MANT_WIDTH-1:0] signed_mant,
    input  logic signed [EXP_WIDTH-1:0] signed_exp,
    output logic [EXP_WIDTH + MANT_WIDTH:0] fp_out
);
// TODO: test it

    localparam BIAS = (1 << (EXP_WIDTH - 1)) - 1;
    
    logic sign_bit;
    logic [EXP_WIDTH-1:0] exp_bits;
    logic [MANT_WIDTH-1:0] mant_bits;
    logic [IN_MANT_WIDTH-1:0] abs_mant;
    
    // Extract sign bit
    assign sign_bit = (signed_mant < 0);
    
    // Get absolute value of mantissa
    assign abs_mant = sign_bit ? -signed_mant : signed_mant;
    
    // Normalize the mantissa and adjust exponent
    logic [$clog2(IN_MANT_WIDTH)-1:0] leading_zeros;
    logic [$clog2(IN_MANT_WIDTH)-1:0] shift_amount;
    logic [IN_MANT_WIDTH-1:0] normalized_mant;
    logic signed [EXP_WIDTH:0] adjusted_exp; // Extra bit for overflow
    
    // Count leading zeros
    always_comb begin
        leading_zeros = 0;
        for (int i = IN_MANT_WIDTH-1; i >= 0; i--) begin
            if (abs_mant[i]) break;
            leading_zeros = leading_zeros + 1;
        end
    end
    
    // Determine shift amount for normalization
    assign shift_amount = (abs_mant == 0) ? 0 : leading_zeros;
    
    // Normalize mantissa
    assign normalized_mant = (abs_mant << shift_amount);
    
    // Adjust exponent
    assign adjusted_exp = signed_exp - shift_amount;
    
    // Extract mantissa bits (remove implicit 1)
    assign mant_bits = normalized_mant[IN_MANT_WIDTH-2:IN_MANT_WIDTH-MANT_WIDTH-1];
    
    // Handle special cases and prepare final exponent
    always_comb begin
        if (abs_mant == 0) begin
            // Zero
            exp_bits = 0;
        end else if (adjusted_exp < -BIAS) begin
            // Underflow to zero
            exp_bits = 0;
        end else if (adjusted_exp >= ((1 << EXP_WIDTH) - 1) - BIAS) begin
            // Overflow to infinity
            exp_bits = {EXP_WIDTH{1'b1}};
        end else begin
            // Normal case: add bias
            exp_bits = adjusted_exp + BIAS;
        end
    end
    
    // Assemble final IEEE 754 format
    assign fp_out = {sign_bit, exp_bits, mant_bits};

endmodule