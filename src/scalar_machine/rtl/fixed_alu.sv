`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Scalar Fixed ALU
Timing      : Combinatorial Logic
Description : This module is mainly used for address manipulation
Status      : Under Development
*/

module fixed_alu #(
    parameter int BITWIDTH = 32
)(
    input  logic [BITWIDTH-1:0]   operand_a,
    input  logic [BITWIDTH-1:0]   operand_b,
    input  logic [BITWIDTH-1:0]   imm_value,    // Immediate value
    input  S_FIXED_OP         operation,           // 0 for add, 1 for sub
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
            default: result = '0;
        endcase
    end

endmodule
