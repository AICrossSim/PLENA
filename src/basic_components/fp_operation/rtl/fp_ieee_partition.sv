/*
Module      : fp_ieee_partition
Timing      : Combinatorial Logic
Description : Give normalized fp number,
            : return a sign bit,
            : 2.MANT_WIDTH of unsigned mantissa (sign, add one?, mantissa)
            : signed biased exponent of .
Status      : Under Development
*/

module fp_ieee_partition #(
    parameter   EXP_WIDTH = 5,
    parameter   MANT_WIDTH = 10,
    parameter   OUT_MANT_WIDTH = MANT_WIDTH + 2,
)(
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_in,  // {sign, exp, mant}
    output logic signed [EXP_WIDTH - 1:0] signed_exp,
    output logic signed [OUT_MANT_WIDTH - 1:0] signed_mantissa
);

    localparam BIAS = (1 << (EXP_WIDTH - 1)) - 1;

    logic sign_bit;
    logic [EXP_WIDTH - 1:0] exp_bit;
    logic [MANT_WIDTH - 1:0] mant_bit;
    logic [OUT_MANT_WIDTH - 2:0] unsigned_mantissa;

    assert (exp_bit != (EXP_WIDTH - 1){1'b1}) else $error("we cannot handle inf or nan in our current design");

    assign sign_bit = data_in[EXP_WIDTH + MANT_WIDTH];
    assign exp_bit = data_in[EXP_WIDTH + MANT_WIDTH - 1:MANT_WIDTH];

    assign mant_bit = data_in[MANT_WIDTH - 1:0];

    assign signed_exp = (exp_bit[EXP_WIDTH - 1] == 1) ? (exp_bit - BIAS) : (signed(exp_bit) - BIAS);
    assign unsigned_mantissa = (exp_bit == 0) ? mant_bit + (1<<(MANT_WIDTH - 1)) : mant_bit;

    assign signed_mantissa = (sign_bit == 1) ? -unsigned_mantissa : unsigned_mantissa;

endmodule