module fp_shift #(
    parameter int EXP_WIDTH = 5,
    parameter int MANT_WIDTH = 10
)(
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_in,  // {sign, exp, mant}
    input  logic [EXP_WIDTH - 1 : 0] shift_amount,
    output logic [EXP_WIDTH + MANT_WIDTH : 0] data_out
);

    // Split input fields
    logic sign;
    logic [EXP_WIDTH-1:0] exponent;
    logic [MANT_WIDTH-1:0] mantissa;

    // Intermediate signals
    logic [EXP_WIDTH-1:0] new_exponent;
    logic [MANT_WIDTH-1:0] shifted_mantissa;
    logic overflow, underflow;

    always_comb begin
        // Unpack input
        sign     = data_in[EXP_WIDTH + MANT_WIDTH];
        exponent = data_in[EXP_WIDTH + MANT_WIDTH - 1 -: EXP_WIDTH];
        mantissa = data_in[MANT_WIDTH-1:0];

        // Default outputs
        overflow    = 1'b0;
        underflow   = 1'b0;

        // Compute new exponent
        if (exponent >= shift_amount) begin
            new_exponent = exponent - shift_amount;
        end else begin
            new_exponent = {EXP_WIDTH{1'b0}};
            underflow = 1'b1;
        end

        // Shift mantissa
        shifted_mantissa = mantissa >> shift_amount;

        // Overflow check
        if ((exponent + shift_amount) > ((1 << EXP_WIDTH) - 1)) begin
            overflow = 1'b1;
        end

        // Handle output
        if (underflow) begin
            data_out = {(EXP_WIDTH + MANT_WIDTH + 1){1'b0}}; // Set to zero on underflow
        end else if (overflow) begin
            data_out = {sign, {(EXP_WIDTH){1'b1}}, {(MANT_WIDTH){1'b0}}}; // Inf representation
        end else begin
            data_out = {sign, new_exponent, shifted_mantissa};
        end
    end

endmodule
