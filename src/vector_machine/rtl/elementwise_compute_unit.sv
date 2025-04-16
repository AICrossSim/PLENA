`timescale 1ns / 1ps

/*
Module      : Matrix Machine Module
Timing      : Sequential, Takes x cycles to compute the dot product
Description : This module conducts the operation m(MLEN, MLEN) @ v(MLEN, 1) + o (MLEN, 1)
*/


module elementwise_compute_unit #(
    // FP Data Format
    parameter EXP_WIDTH    = 4,
    parameter MANT_WIDTH   = 3,

    // Dimensions
    parameter VLEN      = 8,

    // Operation Control
    parameter OPERAND_WIDTH = 4

) (
    input logic clk,
    input logic rst,

    // Input vector
    input logic [VLEN - 1:0] [MANT_WIDTH + EXP_WIDTH : 0] v_in_a,
    input logic v_in_a_valid,
    output logic v_in_a_ready,
    input logic [VLEN - 1:0] [MANT_WIDTH + EXP_WIDTH : 0] v_in_b,
    input logic v_in_b_valid,
    output logic v_in_b_ready,

    // Control
    input logic [OPERAND_WIDTH - 1:0] operation, // 0: add, 1: sub, 2: mul

    // Output Vector
    output logic [VLEN - 1:0] [MANT_WIDTH + EXP_WIDTH : 0] v_out,
    output logic v_out_valid,
    input logic v_out_ready
);

typedef enum logic [OPERAND_WIDTH -1:0] { 
    ADD = 0,
    SUB = 1,
    MUL = 2,
    EXP = 3
 } ELEMENT_V_OPERAND;

logic [VLEN - 1:0] [MANT_WIDTH + EXP_WIDTH : 0] v_out_add;
logic [VLEN - 1:0] [MANT_WIDTH + EXP_WIDTH : 0] v_out_sub;
logic [VLEN - 1:0] [MANT_WIDTH + EXP_WIDTH : 0] v_out_mul;
logic [VLEN - 1:0] [MANT_WIDTH + EXP_WIDTH : 0] v_out_exp;


logic v_in_add_valid, v_in_sub_valid, v_in_mul_valid, v_in_exp_valid;
logic v_in_add_ready, v_in_sub_ready, v_in_mul_ready, v_in_exp_ready;
logic v_out_add_valid, v_out_sub_valid, v_out_mul_valid, v_out_exp_valid;
logic v_out_add_ready, v_out_sub_ready, v_out_mul_ready, v_out_exp_ready;


always_comb begin
    v_out_valid = 0;
    v_out_ready = 0;
    v_out = '0;

    case (operation)
        ADD: begin
            v_out = v_out_add;
            v_out_valid = v_out_add_valid;
            v_out_ready = v_out_add_ready;
        end
        SUB: begin
            v_out = v_out_sub;
            v_out_valid = v_out_sub_valid;
            v_out_ready = v_out_sub_ready;
        end
        MUL: begin
            v_out = v_out_mul;
            v_out_valid = v_out_mul_valid;
            v_out_ready = v_out_mul_ready;
        end
        EXP: begin
            v_out = v_out_exp;
            v_out_valid = v_out_exp_valid;
            v_out_ready = v_out_exp_ready;
        end
    endcase
end

// Elementwise Add, do not include the extended mantissa and exponent
fp_vector_add #(
    .VEC_DIM(VLEN),
    .MANT_WIDTH(MANT_WIDTH),
    .EXP_WIDTH(EXP_WIDTH),
    .EXT_MANT_WIDTH(0),
    .EXT_EXP_WIDTH(0)
) elementwise_add (
    .clk(clk),
    .rst(rst),

    // input port A
    .data_a_in(v_in_a),
    .data_a_in_valid(v_in_a_valid),
    .data_a_in_ready(v_in_add_ready),

    // input port B
    .data_b_in(v_in_b),
    .data_b_in_valid(v_in_b_valid),
    .data_b_in_ready(v_in_sub_ready),

    // output port
    .data_out(v_out_add),
    .data_out_valid(v_out_add_valid),
    .data_out_ready(v_out_add_ready)
);

// Elementwise Mul
fp_vector_mult #(
    .VEC_DIM(VLEN),
    .MANT_WIDTH(MANT_WIDTH),
    .EXP_WIDTH(EXP_WIDTH),
    .EXT_MANT_WIDTH(0),
    .EXT_EXP_WIDTH(0)
) elementwise_mult (
    .clk(clk),
    .rst(rst),

    // input port A
    .data_a_in(v_in_a),
    .data_a_in_valid(v_in_a_valid),
    .data_a_in_ready(v_in_mul_ready),

    // input port B
    .data_b_in(v_in_b),
    .data_b_in_valid(v_in_b_valid),
    .data_b_in_ready(v_in_mul_ready),

    // output port
    .data_out(v_out_mul),
    .data_out_valid(v_out_mul_valid),
    .data_out_ready(v_out_mul_ready)
);



endmodule