`timescale 1ns / 1ps

`include "configuration.svh"
`include "operation.svh"

/*
Module      : Scalar Fixed ALU
Timing      : Combinatorial Logic
Description : This module is mainly used for address manipulation
Status      : Passed Simple Test
*/

module int_alu #(
    parameter int BITWIDTH = 32,
    parameter int IMM_SHIFT_AMOUNT = 4
)(
    input  logic                  clk,
    input  logic                  rst,
    input  logic [BITWIDTH-1:0]   operand_a,
    input  logic [BITWIDTH-1:0]   operand_b,
    input  logic [BITWIDTH-1:0]   imm_value,
    input  S_INT_OP               operation,
    output logic                  result_valid,
    output logic [BITWIDTH-1:0]   computed_address,
    output logic [BITWIDTH-1:0]   result
);

    S_INT_OP             p1_operation;
    logic [BITWIDTH-1:0]   p1_operand_b;
    // ALU operation
    always_ff @(posedge clk) begin
        if (rst) begin
            result_valid <= 1'b0;
            result <= '0;
            p1_operation <= STALL_S_INT;
            p1_operand_b <= '0;
        end else begin
            p1_operation <= operation;
            p1_operand_b <= operand_b;
                case (operation)
                    ADD_INT: begin
                        result <= operand_a + operand_b; // Addition
                        result_valid <= 1'b1;
                    end

                    SUB_INT: begin
                        result <= operand_a - operand_b; // Subtraction
                        result_valid <= 1'b1;
                    end

                    MUL_INT: begin
                        result <= operand_a * operand_b; // Multiplication
                        result_valid <= 1'b1;
                    end

                    LUI_INT: begin
                        result <= { {(BITWIDTH - IMM_SHIFT_AMOUNT){1'b0}}, imm_value, {IMM_SHIFT_AMOUNT{1'b0}} }; // Load upper immediate
                        result_valid <= 1'b1;
                    end

                    ADDI_INT: begin
                        result <= operand_a + imm_value; // Compute address with immediate
                        result_valid <= 1'b1;
                    end

                    MV_INT: begin
                        result <= operand_a; // Move
                        result_valid <= 1'b1;
                    end

                    default: begin
                        result <= '0;
                        result_valid <= 1'b0;
                    end
                endcase
            end
        end
    assign computed_address = ((operation == COMP_ADDR) || (operation == LD_INT) || (operation == ST_INT)) ? operand_a + imm_value : '0;
endmodule
