`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Scalar Fixed ALU
Timing      : Combinatorial Logic
Description : This module is mainly used for address manipulation
Status      : Under Development
*/

module fixed_alu #(
    parameter int BITWIDTH = 32,
    parameter int IMM_WIDTH = 16,
    parameter int IMM_SHIFT_AMOUNT = 12
)(
    input  logic [BITWIDTH-1:0]   operand_a,
    input  logic [BITWIDTH-1:0]   operand_b,
    input  logic [IMM_WIDTH-1:0]  imm_value,    // Immediate value
    input  S_FIXED_OP             operation,           // 0 for add, 1 for sub
    output logic [BITWIDTH-1:0]   result
);

    // ALU operation
    always_comb begin
        case (operation)
            ADDI_FIX:
                result = operand_a + imm_value; // Immediate addition
            ADD_FIX:
                result = operand_a + operand_b; // Addition
            SUB_FIX:
                result = operand_a - operand_b; // Subtraction
            MUL_FIX:
                result = operand_a * operand_b; // Multiplication
            DIV_FIX:
                result = operand_a / operand_b; // Division
            LUI_FIX:
                result = { {(BITWIDTH - IMM_WIDTH - IMM_SHIFT_AMOUNT){1'b0}}, imm_value, {IMM_SHIFT_AMOUNT{1'b0}}};     // Load upper immediate
            COMP_ADDR, LD_FIX, ST_FIX:
                result = operand_a + imm_value; // Compute address with imm
            
            MV_FIX:
                result = operand_a; // Move
            default: result = '0;
        endcase
    end

endmodule
