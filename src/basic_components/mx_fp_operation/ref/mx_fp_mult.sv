module mx_fp_multiplier #(
    parameter int EXP_WIDTH = 5,    // Number of exponent bits
    parameter int MANT_WIDTH = 10   // Number of mantissa bits
)(
    input  logic [(1 + EXP_WIDTH + MANT_WIDTH) - 1:0] a,  // First MX-FP number
    input  logic [(1 + EXP_WIDTH + MANT_WIDTH) - 1:0] b,  // Second MX-FP number
    output logic [(1 + EXP_WIDTH + MANT_WIDTH) - 1:0] result // MX-FP multiplication result
);

    // Internal signal widths
    localparam int BIAS = (1 << (EXP_WIDTH - 1)) - 1;  // Bias for exponent calculation
    localparam int FULL_MANT_WIDTH = (MANT_WIDTH + 1); // Includes implicit leading 1
    localparam int MANT_MULT_WIDTH = (FULL_MANT_WIDTH * 2); // Multiplied mantissa width

    // Extract fields from input
    logic sign_a, sign_b, sign_res;
    logic [EXP_WIDTH-1:0] exp_a, exp_b, exp_res;
    logic [FULL_MANT_WIDTH-1:0] mant_a, mant_b;
    logic [MANT_MULT_WIDTH-1:0] mant_res;

    // Compute sign bit (XOR of input signs)
    assign sign_a = a[EXP_WIDTH + MANT_WIDTH];
    assign sign_b = b[EXP_WIDTH + MANT_WIDTH];
    assign sign_res = sign_a ^ sign_b;

    // Extract exponent and mantissa (implicit leading 1)
    assign exp_a = a[EXP_WIDTH + MANT_WIDTH - 1:MANT_WIDTH];
    assign exp_b = b[EXP_WIDTH + MANT_WIDTH - 1:MANT_WIDTH];
    assign mant_a = {1'b1, a[MANT_WIDTH-1:0]}; // Adding hidden 1
    assign mant_b = {1'b1, b[MANT_WIDTH-1:0]}; // Adding hidden 1

    // Compute exponent result (with bias correction)
    assign exp_res = exp_a + exp_b - BIAS;

    // Perform mantissa multiplication
    assign mant_res = mant_a * mant_b;

    // Normalization and rounding logic
    logic [EXP_WIDTH-1:0] final_exp;
    logic [MANT_WIDTH-1:0] final_mant;
    logic rounding_bit;

    always_comb begin
        if (mant_res[MANT_MULT_WIDTH-1]) begin
            // If the highest bit is set, shift right and increment exponent
            final_mant = mant_res[MANT_MULT_WIDTH-2:MANT_MULT_WIDTH-MANT_WIDTH-1];
            rounding_bit = mant_res[MANT_MULT_WIDTH-MANT_WIDTH-2];
            final_exp = exp_res + 1;
        end else begin
            // No need to shift
            final_mant = mant_res[MANT_MULT_WIDTH-3:MANT_MULT_WIDTH-MANT_WIDTH-2];
            rounding_bit = mant_res[MANT_MULT_WIDTH-MANT_WIDTH-3];
            final_exp = exp_res;
        end

        // Round to nearest even
        if (rounding_bit && final_mant != {MANT_WIDTH{1'b1}})
            final_mant = final_mant + 1;
    end

    // Handle special cases (zero, infinity, NaN)
    always_comb begin
        if (exp_a == {EXP_WIDTH{1'b1}} || exp_b == {EXP_WIDTH{1'b1}}) begin
            // Handle NaN and Infinity
            result = {sign_res, {EXP_WIDTH{1'b1}}, {MANT_WIDTH{1'b0}}}; // Inf or NaN
        end else if (a == 0 || b == 0) begin
            // Handle multiplication by zero
            result = 0;
        end else begin
            // Normal case
            result = {sign_res, final_exp, final_mant};
        end
    end

endmodule
