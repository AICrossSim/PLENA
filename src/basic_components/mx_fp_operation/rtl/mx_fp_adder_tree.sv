`timescale 1ns / 1ps

/*
Module      : MX-FP Adder Tree
Description : This module is used to summing a vector of MX-FP data, this vector is composed of blocks of MX-FP data sharing the same scaling.
Timing      :
Input
        e1  | 
        e2  |
        e3  | -fp_adder_tree-> (e1234, s1)
        e4  |                               \
                                                mx_fp_unit_adder_tree -> (result_element, result_scale)
        e5  |                               /
        e6  | -fp_adder_tree-> (e5678, s2)
        e7  |
        e8  |
Status      : Passed Simple Tests
*/

module mx_fp_adder_tree #(
    parameter VEC_DIM       = 4,
    parameter IN_EXP_WIDTH  = 3,
    parameter IN_MAN_WIDTH  = 4,
    
    // Precision Control
    parameter EXT_MANT_WIDTH_PER_LAYER = 1,
    parameter EXT_EXP_BITS_PER_LAYER = 1,
    
    localparam LEVELS = $clog2(VEC_DIM),

    localparam OVERALL_MANT_EXT_BITS = LEVELS * EXT_MANT_WIDTH_PER_LAYER, 
    localparam OUT_MAN_WIDTH = OVERALL_MANT_EXT_BITS + IN_MAN_WIDTH,    

    localparam OVERALL_EXP_EXT_BITS = LEVELS * EXT_EXP_BITS_PER_LAYER,
    localparam OUT_EXP_WIDTH  = OVERALL_EXP_EXT_BITS + IN_EXP_WIDTH,

    localparam IN_WIDTH       = IN_MAN_WIDTH + IN_EXP_WIDTH + 1,
    localparam OUT_WIDTH      = OUT_MAN_WIDTH + OUT_EXP_WIDTH + 1
) (
    /* verilator lint_off UNUSEDSIGNAL */
    input  logic                 clk,
    input  logic                 rst,
    /* verilator lint_on UNUSEDSIGNAL */
    input  logic [VEC_DIM-1:0] [IN_WIDTH - 1 : 0] data_in,
    input  logic                 data_in_valid,
    output logic                 data_in_ready,
    output logic [OUT_WIDTH - 1 : 0] data_out,
    output logic                 data_out_valid,
    input  logic                 data_out_ready
);


endmodule