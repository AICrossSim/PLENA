module fp_multiplier (
    input  logic [31:0] a,   // First IEEE 754 floating-point number
    input  logic [31:0] b,   // Second IEEE 754 floating-point number
    output logic [31:0] result // Result of multiplication
);

    logic sign_a, sign_b, sign_res;
    logic [7:0] exp_a, exp_b, exp_res;
    logic [23:0] mant_a, mant_b;
    logic [47:0] mant_res;
    logic [7:0] final_exp;
    logic [22:0] final_mant;
    logic rounding_bit;
    
    // Extract sign, exponent, and mantissa
    assign sign_a = a[31];
    assign sign_b = b[31];
    assign exp_a  = a[30:23];
    assign exp_b  = b[30:23];
    assign mant_a = {1'b1, a[22:0]}; // Implicit leading 1
    assign mant_b = {1'b1, b[22:0]}; // Implicit leading 1

    // Compute sign
    assign sign_res = sign_a ^ sign_b;

    // Compute exponent (bias = 127)
    assign exp_res = exp_a + exp_b - 8'd127;

    // Multiply mantissas (24-bit * 24-bit)
    assign mant_res = mant_a * mant_b;

    always_comb begin
        if (mant_res[47]) begin
            // Normalization (Shift right and increase exponent)
            final_mant = mant_res[46:24];
            rounding_bit = mant_res[23];
            final_exp = exp_res + 1;
        end else begin
            // No normalization needed
            final_mant = mant_res[45:23];
            rounding_bit = mant_res[22];
            final_exp = exp_res;
        end

        // Rounding (Round to nearest even)
        if (rounding_bit && final_mant != 23'h7FFFFF)
            final_mant = final_mant + 1;
    end

    // Handle special cases
    always_comb begin
        if (exp_a == 8'hFF || exp_b == 8'hFF) begin
            // Handle NaN and Infinity
            result = {sign_res, 8'hFF, 23'h0}; // Inf or NaN
        end else if (a == 32'h0 || b == 32'h0) begin
            // Handle multiplication by zero
            result = 32'h0;
        end else begin
            // Normal case
            result = {sign_res, final_exp, final_mant};
        end
    end

endmodule
