`timescale 1ns / 1ps
`include "global_define.vh"
/*
Module      : Floating Point Configurable Precision Adder (With Sign)
Timing      : Combinatorial Logic
Description : Adds two FP numbers with different exponents and signs.
              Aligns mantissas, preserves full precision (no bits discarded).
              Output format: {sign, exp_out, mant_out}.
              No rounding.
              It needs normalisation.
              The lossy part will be at the mantissa adder
Status      : Passed Simple Tests
*/

module fp_fix_mult #(
    parameter int EXP_WIDTH = 5,
    parameter int MANT_WIDTH = 10,
    parameter int IEEE_COMPLIANCE = 0,
    parameter int UBR_FLAG = 0
)(
    input  logic clk,
    input  logic rst,
    input  logic data_in_valid,
    output logic data_in_ready,
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_a,  // {sign, exp, mant}
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_b,
    output logic [EXP_WIDTH + MANT_WIDTH : 0] data_out,
    output logic data_out_valid,
    input  logic data_out_ready
);

`ifdef DC_LIB_EN
    DW_fp_mult_inst #(
        .EXP_WIDTH(EXP_WIDTH),
        .MANT_WIDTH(MANT_WIDTH)
    ) dc_lib_fp_fix_mult (
        .clk(clk),  
        .rst(rst),
        .data_in_valid(data_in_valid),
        .data_in_ready(data_in_ready),
        .data_a(data_a),
        .data_b(data_b),
        .data_out(data_out),
        .data_out_valid(data_out_valid),
        .data_out_ready(data_out_ready)
    );
`else
    fp_cp_mult #(
        .EXP_WIDTH(EXP_WIDTH),
        .MANT_WIDTH(MANT_WIDTH)
    ) fp_cp_mult_inst (
        .clk(clk),  
        .rst(rst),
        .data_in_valid(data_in_valid),
        .data_in_ready(data_in_ready),
        .data_a(data_a),
        .data_b(data_b),
        .data_out(data_out),
        .data_out_valid(data_out_valid),
        .data_out_ready(data_out_ready)
    );
`endif // DC_LIB_EN

endmodule
