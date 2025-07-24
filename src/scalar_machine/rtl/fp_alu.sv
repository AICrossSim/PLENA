`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Scalar FP ALU
Timing      : Combinatorial Logic
Description : This module is used for all the FP operations
            : 1. FP Add, 2. FP Subtract, 3. FP Multiply, 
*/

module fp_alu #(
    parameter   EXP_WIDTH = 5,
    parameter   MANT_WIDTH = 10
)(
    input  logic clk,
    input  logic rst,
    input  S_FP_OP operation,
    input  logic [FP_OPERAND_WIDTH - 1 : 0]     reg_waddr,
    output  logic [FP_OPERAND_WIDTH - 1 : 0]    stored_reg_waddr, 
    input  logic [EXP_WIDTH + MANT_WIDTH : 0]   data_a,  // {sign, exp, mant}
    input  logic [EXP_WIDTH + MANT_WIDTH : 0]   data_b,
    output logic [EXP_WIDTH + MANT_WIDTH : 0]   data_out,
    output  logic                               data_out_valid
);


logic data_in_valid, data_in_ready;
logic mult_data_in_valid, mult_data_in_ready;
logic mult_data_out_valid, mult_data_out_ready;
logic add_data_in_valid, add_data_in_ready;
logic add_data_out_valid, add_data_out_ready;

logic [EXP_WIDTH + MANT_WIDTH : 0] fp_add_out, fp_sub_out, fp_mul_out;
logic [EXP_WIDTH + MANT_WIDTH : 0] negated_data_b;
logic [EXP_WIDTH + MANT_WIDTH : 0] data_out_add, data_out_mul, data_out_exp;
logic negated_en;
logic data_out_ready;

// Status Tracking
S_FP_OP recorded_operation;
logic alu_in_use;

always_ff @(posedge clk) begin
    if (rst) begin
        recorded_operation  <= STALL_S_FP;
        data_in_valid       <= 1'b0;
        stored_reg_waddr    <= 'b0;
        data_out_ready      <= 1'b0;
    end else begin
        data_out_ready      <= 1'b1;
        if (!alu_in_use & operation != STALL_S_FP) begin
            recorded_operation <= operation;
            stored_reg_waddr <= reg_waddr;
            data_in_valid <= 1'b1;
            alu_in_use <= 1'b1;
        end else if (data_out_valid & data_out_ready & alu_in_use) begin
            // At the end of the operation, reset the SFU
            recorded_operation <= STALL_S_FP; 
            data_in_valid <= 1'b0;
        end else if (alu_in_use) begin
            recorded_operation <= recorded_operation;
            data_in_valid <= 1'b0;
        end else begin
            recorded_operation <= STALL_S_FP;
            data_in_valid <= 1'b0;
        end
    end
end


always_comb begin
    // Combinational module to flip the sign bit for FP subtraction
    negated_data_b = {~data_b[EXP_WIDTH + MANT_WIDTH], data_b[EXP_WIDTH + MANT_WIDTH - 1 : 0]};
    case (recorded_operation)
        ADD_FP: begin
            negated_en = 1'b0;
            add_data_in_valid   = data_in_valid;
            data_in_ready       = add_data_in_ready;
            data_out            = data_out_add;
            data_out_valid      = add_data_out_valid;
            add_data_out_ready  = data_out_ready;
        end

        SUB_FP: begin
            negated_en          = 1'b1;
            add_data_in_valid   = data_in_valid;
            data_in_ready       = add_data_in_ready;
            data_out            = data_out_add;
            data_out_valid      = add_data_out_valid;
            add_data_out_ready  = data_out_ready;
        end

        MUL_FP: begin
            negated_en = 1'b0;
            mult_data_in_valid  = data_in_valid;
            data_in_ready       = mult_data_in_ready;
            data_out            = data_out_mul;
            data_out_valid      = mult_data_out_valid;
            mult_data_out_ready = data_out_ready;
        end

        MV_FP: begin
            negated_en      = 1'b0;
            data_out        = data_a; 
            data_out_valid  = data_in_valid;
            data_in_ready   = data_out_ready;
        end

        default: begin
            negated_en      = 1'b0;
            data_out        = 'b0;
            data_out_valid  = 1'b0;
            data_in_ready   = 1'b0;
        end

    endcase
end


fp_fix_adder #(
    .EXP_WIDTH(EXP_WIDTH),
    .MANT_WIDTH(MANT_WIDTH)
) adder (
    .clk(clk),
    .rst(rst),
    .data_in_valid(add_data_in_valid),
    .data_in_ready(add_data_in_ready),
    .data_a(data_a),
    .data_b(negated_en ? negated_data_b : data_b),
    .data_out(data_out_add),
    .data_out_valid(add_data_out_valid),
    .data_out_ready(add_data_out_ready)
);

fp_fix_mult #(
    .EXP_WIDTH(EXP_WIDTH),
    .MANT_WIDTH(MANT_WIDTH)
) multiplier (
    .clk(clk),
    .rst(rst),
    .data_in_valid(mult_data_in_valid),
    .data_in_ready(mult_data_in_ready),
    .data_a(data_a),
    .data_b(data_b),
    .data_out(data_out_mul),
    .data_out_valid(mult_data_out_valid),
    .data_out_ready(mult_data_out_ready)
);


endmodule