`timescale 1ns / 1ps

/*
Module      : Convertion Units Floating Point with Configurable Precision to MX-FP
Timing      : Sequential, Takes 1 cycle to compute the dot product
Description : 
*/


module fp_2_mx_fp (
    parameter CONVERT_DIM = 8, 
    parameter IN_MAN_WIDTH = 3,
    parameter IN_EXP_WIDTH = 4,
    parameter MX_FP_MAN_WIDTH = 3,
    parameter MX_FP_EXP_WIDTH = 4,
    parameter MX_FP_SCALE_WIDTH = 8
)(
    input   logic clk,
    input   logic [CONVERT_DIM-1:0][IN_MAN_WIDTH + IN_EXP_WIDTH : 0] data_in,
    input   logic data_in_valid,
    output  logic data_in_ready,

    output  logic [CONVERT_DIM-1:0][MX_FP_MAN_WIDTH + MX_FP_EXP_WIDTH : 0] element_data_out,
    output  logic [MX_FP_SCALE_WIDTH-1:0] scale_data_out,
    output  logic element_data_out_valid,
    input   logic element_data_out_ready
);



    unsigned_max #(
        .width(IN_MAN_WIDTH),
        .length(CONVERT_DIM),
        .pl_freq(max_pl_freq),
        .flop_output(0)
    ) u0_exp_max (
        .clk(clk),
        .i_exps(p0_exps),
        .o_e_max(p0_e_max)
    );

    
endmodule