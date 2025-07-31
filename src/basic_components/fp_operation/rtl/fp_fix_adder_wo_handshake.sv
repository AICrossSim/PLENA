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
module fp_fix_adder_wo_handshake #(
    parameter int EXP_WIDTH = 5,
    parameter int MANT_WIDTH = 10,
    parameter int IEEE_COMPLIANCE = 0
)(
    input  logic clk,
    input  logic rst,
    input  logic data_in_valid,
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_a,  // {sign, exp, mant}
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_b,
    output logic [EXP_WIDTH + MANT_WIDTH : 0] data_out,
    output logic data_out_valid
);

`ifdef DC_LIB_EN
    logic [MANT_WIDTH+EXP_WIDTH : 0] data_out_reg;

    // Instance of DW_fp_add
    DW_fp_add #(MANT_WIDTH, EXP_WIDTH, IEEE_COMPLIANCE)
        U1 ( .a(data_a), .b(data_b), .rnd(3'b000), .z(data_out_reg), .status() );

    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            data_out <= '0;
            data_out_valid <= 1'b0;
        end else begin
            if (data_in_valid) begin
                data_out <= data_out_reg;
                data_out_valid <= 1'b1;
            end else begin
                data_out_valid <= 1'b0;
            end
        end
    end

`else
    fp_cp_adder #(
        .MANT_WIDTH(MANT_WIDTH),
        .EXP_WIDTH(EXP_WIDTH)
    ) fp_cp_adder (
        .clk(clk),
        .rst(rst),
        .data_in_valid(data_in_valid),
        .data_in_ready(),
        .data_a(data_a),
        .data_b(data_b),
        .data_out(data_out),
        .data_out_valid(data_out_valid),
        .data_out_ready(1'b1)
    );
`endif
endmodule
