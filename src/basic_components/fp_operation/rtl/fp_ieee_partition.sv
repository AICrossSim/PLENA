`timescale 1ns / 1ps
/*
Module      : fp_ieee_partition
Timing      : Combinatorial Logic
Description : FP_IEEE_Partition
            - Splits IEEE floating-point data into a signed mantissa and a signed integer exponent.
*/

module fp_ieee_partition #(
    parameter   EXP_WIDTH = 5,
    parameter   MANT_WIDTH = 10,
    localparam   OUT_MANT_WIDTH = MANT_WIDTH + 2
)(
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_in,  // {sign, exp, mant}
    output logic signed [EXP_WIDTH - 1:0] signed_exp,
    output logic signed [OUT_MANT_WIDTH - 1:0] signed_mant
);

    localparam BIAS = (1 << (EXP_WIDTH - 1)) - 1;

    logic sign_bit;
    logic [EXP_WIDTH - 1:0] exp_bit;
    logic [MANT_WIDTH - 1:0] mant_bit;
    logic [OUT_MANT_WIDTH - 1:0] unsigned_mant;

    assign sign_bit = data_in[EXP_WIDTH + MANT_WIDTH];
    assign exp_bit = data_in[EXP_WIDTH + MANT_WIDTH - 1:MANT_WIDTH];
    assign mant_bit = data_in[MANT_WIDTH - 1:0];
    localparam EXP_HIGH = EXP_WIDTH - 1;

`ifdef SIMULATION
    always @(*) begin
        assert (exp_bit != {(EXP_WIDTH){1'b1}}) else $warning("we cannot handle inf or nan of bits: %b in our current design", data_in);
    end
`endif

    assign signed_exp = signed'(exp_bit) - BIAS;
    assign unsigned_mant = (exp_bit == 0) ? 
                               {2'b00, mant_bit} : 
                               {2'b01, mant_bit};

    assign signed_mant = (sign_bit == 1) ? -signed'(unsigned_mant) : signed'(unsigned_mant);

endmodule