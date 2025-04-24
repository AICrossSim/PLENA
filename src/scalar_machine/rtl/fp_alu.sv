`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Scalar ALU
Timing      : Combinatorial Logic
Description : This module includes elementwise vector computations
            : 1. FP Add, 2. FP Subtract, 3. FP Multiply, 4. FP Isqrt 5. FP Log 6. FP Exp
Status      : Under Development
*/

module fp_alu #(
    parameter   EXP_WIDTH = 5,
    parameter   MANT_WIDTH = 10
)(
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_a,  // {sign, exp, mant}
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_b,
    input  S_ALU_OP operation,       // 0: add, 1: sub, 2: mul, 3: isqrt
    output logic [EXP_WIDTH + MANT_WIDTH : 0] data_out
)

logic [EXP_WIDTH + MANT_WIDTH : 0] fp_add_out, fp_sub_out, fp_mul_out, fp_isqrt_out, fp_log_out, fp_exp_out;
logic [EXP_WIDTH + MANT_WIDTH : 0] negated_data_b;
logic negated_en;

always_comb begin
    negated_data_b = {~data_b[EXP_WIDTH + MANT_WIDTH], data_b[EXP_WIDTH + MANT_WIDTH - 1 : 0]};
    case (operation)
        ADD: begin
            negated_en = 1'b0;
            data_out = fp_add_out;
        end

        SUB: begin
            negated_en = 1'b1;
            data_out = fp_sub_out;
        end

        MUL: begin
            negated_en = 1'b0;
            data_out = fp_mul_out;
        end

        ISQRT: begin
            negated_en = 1'b0;
            data_out = fp_isqrt_out;
        end

        LOG: begin
            negated_en = 1'b0;
            data_out = fp_log_out;
        end

        EXP: begin
            negated_en = 1'b0;
            data_out = fp_exp_out;
        end

        default: begin
            negated_en = 1'b0;
            data_out = '0; // Default case to avoid latches
        end
    endcase
end


fp_cp_mult #(
    .EXP_WIDTH(EXP_WIDTH),
    .MANT_WIDTH(MANT_WIDTH)
) fp_multiplier (
    .data_a(data_a),
    .data_b(negated_en ? negated_data_b : data_b),
    .data_out(fp_mul_out)
);


// Do not consider extension
fp_cp_adder #(
    .EXP_WIDTH(EXP_WIDTH),
    .MANT_WIDTH(MANT_WIDTH)
) fp_adder (
    .data_a(data_a),
    .data_b(data_b),
    .data_out(data_out)
);


endmodule