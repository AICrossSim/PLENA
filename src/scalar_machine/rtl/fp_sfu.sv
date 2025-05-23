`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Scalar FP Special Function Unit
Timing      : Combinatorial Logic
Description : This module is used for all the FP operations
            : 1. FP Reciprocal 2. FP Sqrt 6. FP Exp
Note        : In this version of the FP_SFU, since we assume that if there are continous FP related 
              Instructions, they are very likely to be data dependent. Therefore, only when the single operation
              is completed, the next operation will be started. (Can be optimized in the future)
*/


module fp_sfu #(
    parameter   EXP_WIDTH = 5,
    parameter   MANT_WIDTH = 10
)(
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_a,  // {sign, exp, mant}
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_b,
    input  S_FP_OP operation,       // 0: add, 1: sub, 2: mul, 3: isqrt
    output logic [EXP_WIDTH + MANT_WIDTH : 0] data_out
);

logic [EXP_WIDTH + MANT_WIDTH : 0] fp_add_out, fp_sub_out, fp_mul_out, fp_isqrt_out, fp_log_out, fp_exp_out;
logic [EXP_WIDTH + MANT_WIDTH : 0] negated_data_b;
logic negated_en;

// Status Tracking TODO
S_FP_OP recorded_operation;
logic in_compute;

always_comb begin
    negated_data_b = {~data_b[EXP_WIDTH + MANT_WIDTH], data_b[EXP_WIDTH + MANT_WIDTH - 1 : 0]};
    case (recorded_operation)

        RECI_FP: begin
            negated_en = 1'b0;
            data_out = fp_reciprocal_out;
        end

        SQRT_FP: begin
            negated_en = 1'b0;
            data_out = fp_sqrt_out;
        end

        EXP_FP: begin
            negated_en = 1'b0;
            data_out = fp_exp_out;
        end

        default: begin
            negated_en = 1'b0;
            data_out = {(EXP_WIDTH + MANT_WIDTH){1'b0}}; // Default case to avoid latches
        end
    endcase
end




fp_cp_reciprocal #(
    .EXP_WIDTH(EXP_WIDTH),
    .MANT_WIDTH(MANT_WIDTH)
) fp_reciprocal (
    .data_in(data_a),
    .data_out(fp_reciprocal_out)
);

fp_cp_sqrt #(
    .EXP_WIDTH(EXP_WIDTH),
    .MANT_WIDTH(MANT_WIDTH)
) fp_sqrt (
    .data_in(data_a),
    .data_out(fp_sqrt_out)
);



endmodule