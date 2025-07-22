`timescale 1ns / 1ps

module DW_fp_add_inst #(
    parameter int EXP_WIDTH = 8,
    parameter int MANT_WIDTH = 23,
    parameter int IEEE_COMPLIANCE = 0,
    parameter int ADDER_CYCLES = 1
)(
    input [MANT_WIDTH+EXP_WIDTH : 0] a,
    input [MANT_WIDTH+EXP_WIDTH : 0] b,
    output [MANT_WIDTH+EXP_WIDTH : 0] z,
    output [7 : 0] status
);


input [2 : 0] rnd;
output [MANT_WIDTH+EXP_WIDTH : 0] z;
output [7 : 0] status;

    // Instance of DW_fp_add
    DW_fp_add #(MANT_WIDTH, EXP_WIDTH, IEEE_COMPLIANCE)
	  U1 ( .a(a), .b(b), .rnd(3'b000), .z(z), .status(status) );

endmodule