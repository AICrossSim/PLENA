`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Scalar Fixed ALU
Timing      : Combinatorial Logic
Description : This module is mainly used for address manipulation
Status      : Passed Simple Test
*/

module fixed_alu #(
    parameter int BITWIDTH = 32,
    parameter int IMM_SHIFT_AMOUNT = 12
)(
    input  logic                  clk,
    input  logic                  rst,
    input  logic [BITWIDTH-1:0]   operand_a,
    input  logic [BITWIDTH-1:0]   operand_b,
    input  logic [BITWIDTH-1:0]   imm_value,
    input  S_FIXED_OP             operation,
    output logic                  result_valid,
    output logic [BITWIDTH-1:0]   computed_address,
    output logic [BITWIDTH-1:0]   result
);

    S_FIXED_OP             p1_operation;
    logic [BITWIDTH-1:0]   p1_operand_b;
    // ALU operation
    always_ff @(posedge clk) begin
        if (rst) begin
            result_valid <= 1'b0;
            result <= '0;
            p1_operation <= STALL_S_FIXED;
            p1_operand_b <= '0;
        end else begin
            p1_operation <= operation;
            p1_operand_b <= operand_b;
            if (p1_operation == ACC_MULI) begin
                result <= result + p1_operand_b;
                result_valid <= 1'b1;
            end else begin
                case (operation)
                    ADD_FIX: begin
                        result <= operand_a + operand_b; // Addition
                        result_valid <= 1'b1;
                    end

                    SUB_FIX: begin
                        result <= operand_a - operand_b; // Subtraction
                        result_valid <= 1'b1;
                    end

                    MUL_FIX: begin
                        result <= operand_a * operand_b; // Multiplication
                        result_valid <= 1'b1;
                    end

                    LUI_FIX: begin
                        result <= { {(BITWIDTH - IMM_SHIFT_AMOUNT){1'b0}}, imm_value, {IMM_SHIFT_AMOUNT{1'b0}} }; // Load upper immediate
                        result_valid <= 1'b1;
                    end

                    ACC_MULI: begin
                        result <= operand_a * imm_value;
                        result_valid <= 1'b0;
                    end

                    ADDI_FIX: begin
                        result <= operand_a + imm_value; // Compute address with immediate
                        result_valid <= 1'b1;
                    end

                    MV_FIX: begin
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
    end
    assign computed_address = ((operation == COMP_ADDR) || (operation == LD_FIX) || (operation == ST_FIX)) ? operand_a + imm_value : '0;
endmodule
