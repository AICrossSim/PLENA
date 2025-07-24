`timescale 1ns / 1ps

module DW_fp_recip_inst #(
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

    DW_fp_recip #(
        .sig_width(MANT_WIDTH), 
        .exp_width(EXP_WIDTH), 
        .ieee_compliance(1),
        .faithful_round(1)
    ) dc_lib_fp_reciprocal ( 
        .a      (data_in),
        .rnd    (3'b000),
        .z      (data_out_reg),
        .status ()
    );

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