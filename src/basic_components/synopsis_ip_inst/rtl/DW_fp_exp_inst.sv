`timescale 1ns / 1ps

module DW_fp_exp_inst #(
    parameter int EXP_WIDTH = 8,
    parameter int MANT_WIDTH = 23
)(
    input logic clk,
    input logic rst,
    input logic [MANT_WIDTH+EXP_WIDTH : 0] data_in,
    input logic data_in_valid,
    output logic data_in_ready,
    output logic [MANT_WIDTH+EXP_WIDTH : 0] data_out,
    output logic data_out_valid,
    input logic data_out_ready
);


logic [MANT_WIDTH+EXP_WIDTH : 0] data_out_reg;
// Instance of DW_fp_add
DW_fp_exp #(.sig_width(MANT_WIDTH), .exp_width(EXP_WIDTH), .arch(2'd0))
    U1 ( .a(data_in), .z(data_out_reg), .status());

register_slice #(
    .DATA_WIDTH(MANT_WIDTH+EXP_WIDTH + 1)
) register_slice_inst (
    .clk(clk),
    .rst(rst),
    .data_in        (data_out_reg),
    .data_in_valid  (data_in_valid),
    .data_in_ready  (data_in_ready),
    .data_out       (data_out),
    .data_out_valid (data_out_valid),
    .data_out_ready (data_out_ready)
);

endmodule