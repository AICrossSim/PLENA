`timescale 1ns / 1ps

/*
Module      : Unary Convertion from FP with Configurable Precision to MX-FP
Timing      : Combinatorial Logic
Description : 
Status      : 
*/

module fp_2_sign_mag #(
    parameter FP_EXP_WIDTH = 4,
    parameter FP_MANT_WIDTH = 3,
    parameter SIGN_MAG_WIDTH = 4,
    parameter SIGN_MAG_FRAC_WIDTH = 4
)(
    input  logic [FP_EXP_WIDTH + FP_MANT_WIDTH : 0] fp_in,
    output logic [SIGN_MAG_WIDTH - 1 : 0] sign_mag_out
);

    
    // initial begin
    //     assert (SIGN_MAG_FRAC_WIDTH < FP_MANT_WIDTH)
    //         else $error("SIGN_MAG_FRAC_WIDTH must be less than FP_MANT_WIDTH");
    // end
    localparam int BIAS = (1 << (FP_EXP_WIDTH - 1)) - 1;
    localparam int ABS_SIGN_MAG_WIDTH = SIGN_MAG_WIDTH - 1;

    // Decompose input FP value
    logic                        fp_sign;
    logic [FP_EXP_WIDTH-1:0]     fp_exp;
    logic [FP_MANT_WIDTH-1:0]    fp_mant;

    logic [ABS_SIGN_MAG_WIDTH + FP_MANT_WIDTH - 1 : 0] unrounded_sign_mag_out;

    logic [ABS_SIGN_MAG_WIDTH + 1 - 1 : 0] unsigned_sign_mag_out;

    assign fp_sign = fp_in[FP_EXP_WIDTH + FP_MANT_WIDTH];
    assign fp_exp  = fp_in[FP_EXP_WIDTH + FP_MANT_WIDTH - 1 : FP_MANT_WIDTH];
    assign fp_mant = fp_in[FP_MANT_WIDTH - 1 : 0];
    
    // Convert to sign magnitude format
    always_comb begin
        if (fp_exp >= BIAS) begin
            unrounded_sign_mag_out = fp_mant >> (fp_exp - BIAS);
        end
        else if (fp_exp > 0) begin
            unrounded_sign_mag_out = fp_mant << (BIAS - fp_exp);
        end
        else begin
            unrounded_sign_mag_out = fp_mant >> (1 - fp_exp);
        end
    end
    
    fixed_round #(
        .IN_WIDTH(ABS_SIGN_MAG_WIDTH + FP_MANT_WIDTH + 1),
        .IN_FRAC_WIDTH(FP_MANT_WIDTH),
        .OUT_WIDTH(ABS_SIGN_MAG_WIDTH + 1),
        .OUT_FRAC_WIDTH(SIGN_MAG_FRAC_WIDTH)
    ) round_inst (
        .data_in({1'b0, unrounded_sign_mag_out}),
        .data_out(unsigned_sign_mag_out)
    );

    assign unsigned_sign_mag_out = {fp_sign, sign_mag_out[ABS_SIGN_MAG_WIDTH - 1 : 0]};

endmodule