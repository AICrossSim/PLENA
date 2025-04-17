`timescale 1ns / 1ps
`include "operation.svh"
/*
Module      : Vector ALU
Timing      : Combinatorial Logic
Description : This module includes elementwise vector computations
            : 1. Elementwise Add, 2. Elementwise Subtract, 3. Elementwise Multiply, 4. Elementwise Exponential
Status      : Under Development
*/

module vector_element_alu #(
    parameter   EXP_WIDTH = 5,
    parameter   MANT_WIDTH = 10
)(
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_a,  // {sign, exp, mant}
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_b,
    input  ELEMENT_V_OPERAND operation,       // 0: add, 1: sub, 2: mul, 3: exp
    output logic [EXP_WIDTH + MANT_WIDTH : 0] data_out
);

    logic [EXP_WIDTH + MANT_WIDTH : 0] data_out_add, 
                                          data_out_mul,
                                          data_out_exp;
    logic [EXP_WIDTH + MANT_WIDTH : 0] negated_data_b;
    logic negated_en;

    always_comb begin
        // Combinational module to flip the sign bit for FP subtraction
        negated_data_b = {~data_b[EXP_WIDTH + MANT_WIDTH], data_b[EXP_WIDTH + MANT_WIDTH - 1 : 0]};
        case (operation)
            ADD: begin
                negated_en = 1'b0;
                data_out = data_out_add;
            end

            SUB: begin
                negated_en = 1'b1;
                data_out = data_out_add;
            end

            MUL: begin
                negated_en = 1'b0;
                data_out = data_out_mul;
            end

            EXP: begin
                negated_en = 1'b0;
                data_out = data_out_exp;
            end

            default: begin
                negated_en = 1'b0;
                data_out = '0; // Default case to avoid latches
            end

        endcase
    end


fp_cp_adder #(
    .EXP_WIDTH(EXP_WIDTH),
    .MANT_WIDTH(MANT_WIDTH),
    .EXT_EXP_WIDTH(0),
    .EXT_MANT_WIDTH(0)
) adder (
    .data_a(data_a),
    .data_b(negated_en ? negated_data_b : data_b),
    .data_out(data_out_add)
);


fp_cp_mult #(
    .EXP_WIDTH(EXP_WIDTH),
    .MANT_WIDTH(MANT_WIDTH),
    .EXT_EXP_WIDTH(0),
    .EXT_MANT_WIDTH(0)
) multiplier (
    .data_a(data_a),
    .data_b(data_b),
    .data_out(data_out_mul)
);


// TODO EXP

endmodule
