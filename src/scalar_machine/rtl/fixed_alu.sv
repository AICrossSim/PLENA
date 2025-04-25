// Simple ALU with support for register or immediate operands and basic operations
module fixed_alu #(
    parameter int BITWIDTH = 32
)(
    input  logic [BITWIDTH-1:0]   operand_a,
    input  logic [BITWIDTH-1:0]   operand_b,
    input  logic                  use_imm,      // 1 to use immediate, 0 to use register
    input  logic [BITWIDTH-1:0]   imm_value,    // Immediate value
    input  logic                  op,           // 0 for add, 1 for sub
    output logic [BITWIDTH-1:0]   result
);

    logic [BITWIDTH-1:0] operand_b_mux;

    // Select between register operand and immediate
    assign operand_b_mux = use_imm ? imm_value : operand_b;

    // ALU operation
    always_comb begin
        case (op)
            1'b0: result = operand_a + operand_b_mux; // Addition
            1'b1: result = operand_a - operand_b_mux; // Subtraction
            default: result = '0;
        endcase
    end

endmodule
