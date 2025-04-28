`timescale 1ns / 1ps
`include "operation.svh"

/*
Module      : Vector ALU
Timing      : Combinatorial Logic
Description : This module includes elementwise vector computations
            : 1. Elementwise Add, 2. Elementwise Subtract, 3. Elementwise Multiply, 4. Elementwise Exponential
Status      : Under Development
*/

module  fp_exp #(
    parameter   EXP_WIDTH = 5,
    parameter   MANT_WIDTH = 10
)(
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_in,  // {sign, exp, mant}
    input logic data_in_valid,
    output logic data_in_ready,
    output logic [EXP_WIDTH + MANT_WIDTH : 0] data_out,
    output logic data_out_valid,
    input logic data_out_ready
);
  localparam DATA_LOG2_E_WIDTH = 8;
  localparam DATA_LOG2_E_FRAC_WIDTH = 4;
  localparam signed FIXED_LOG2_E = 8'H40;

  localparam DATA_N_WIDTH = 8; // Including sign bit
  localparam DATA_R_WIDTH = 8; // Including sign bit
  localparam DATA_IN_FIXED_WIDTH = DATA_N_WIDTH + DATA_R_WIDTH - 1;

  logic [DATA_IN_FIXED_WIDTH - 1:0] data_in_fixed;
  logic data_in_fixed_valid, data_in_fixed_ready;

  logic [DATA_IN_FIXED_WIDTH - 1:0] data_in_fixed_log2_e;
  logic data_in_fixed_log2_e_valid, data_in_fixed_log2_e_ready;

  logic [DATA_IN_FIXED_WIDTH - 1:0] data_in_fixed_log2_e_rounded;
  logic data_in_fixed_log2_e_valid, data_in_fixed_log2_e_ready;
  // data_n is the integer part of the fixed point number
  // data_r is the fractional part of the fixed point number
  logic [DATA_N_WIDTH - 1:0] data_in_n;
  logic [DATA_R_WIDTH - 1:0] data_in_r;
  fp_to_fixed_conversion #(
    .EXP_WIDTH(EXP_WIDTH),
    .MANT_WIDTH(MANT_WIDTH),
    .IN_WIDTH(EXP_WIDTH + MANT_WIDTH + 1),
    .OUT_WIDTH(DATA_IN_FIXED_WIDTH),
    .OUT_FRAC_WIDTH(FRAC_WIDTH - 1)
  ) fp_to_fixed_conversion_inst (
    .data_in(data_in),
    .data_in_valid(data_in_valid),
    .data_in_ready(data_in_ready),
    .data_out(data_in_fixed),
    .data_out_valid(data_in_fixed_valid),
    .data_out_ready(data_in_fixed_ready)
  );

  assign data_in_fixed_log2_e = data_in_fixed * FIXED_LOG2_E;
  fixed_round #(
    .IN_WIDTH(DATA_IN_FIXED_WIDTH + DATA_LOG2_E_WIDTH),
    .IN_FRAC_WIDTH(DATA_IN_FIXED_WIDTH - 1 + DATA_LOG2_E_FRAC_WIDTH),
    .OUT_WIDTH(DATA_IN_FIXED_WIDTH),
    .OUT_FRAC_WIDTH(DATA_IN_FIXED_WIDTH - 1)
  ) fixed_round_inst (
    .data_in(data_in_fixed_log2_e),
    .data_out(data_in_fixed_log2_e_rounded)
  );
  
  assign data_in_n = {data_in_fixed_log2_e_rounded[DATA_IN_FIXED_WIDTH - 1], data_in_fixed_log2_e_rounded[DATA_N_WIDTH + DATA_R_WIDTH - 3:DATA_R_WIDTH - 1]};
  assign data_in_r = {data_in_fixed_log2_e_rounded[DATA_IN_FIXED_WIDTH - 1], data_in_fixed_log2_e_rounded[DATA_R_WIDTH - 2:0]};

  // So basically, The input frac_width is DATA_LOG2_E_MAN_FRAC_WIDTH
  // We wish to make the output frac_width = CASTED_DATA_LOG2_E_FRAC_WIDTH
  // real_data = man * 2** exp this is left shift here
  assign shift_value = DATA_LOG2_E_MAN_FRAC_WIDTH - CASTED_DATA_LOG2_E_FRAC_WIDTH - $signed(edata_in_0_log2_e);
    // or implement with fixed_2_n_inst
    // the benefit is we can implement the fixed_2_n_inst with the same logic as the fixed_round_inst
    fixed_2_n #(
        .DATA_IN_WIDTH(DATA_R_WIDTH),
        .DATA_IN_FRAC_WIDTH(DATA_R_WIDTH - 1),
        .DATA_OUT_WIDTH(DATA_OUT_MAN_WIDTH),
        .DATA_OUT_FRAC_WIDTH(DATA_OUT_MAN_WIDTH - 2)
    ) fixed_2_n_inst (
        .data_in(data_in_r),
        .data_out(data_in_exp)
    );
    fix_with_shift_2_fp #(
        .FIXED_DATA_WIDTH(DATA_R_WIDTH),
        .SHIFT_WIDTH(DATA_R_WIDTH),
        .FP_EXP_WIDTH(EXP_WIDTH),
        .FP_MANT_WIDTH(MANT_WIDTH)
    ) fix_with_shift_2_fp_inst (
        .data_in(data_in_r),
        .shift_in(data_in_n),
        .exp_out(data_in_exp),
        .mant_out(data_in_mant)
    );
    assign sign_bit = data_in_mant[MANT_WIDTH - 1];
    assign data_out = {sign_bit, data_in_exp, data_in_mant};
    assign data_out_valid = data_in_fixed_valid;
    assign data_in_fixed_ready = data_out_ready;

endmodule

module fixed_2_n #(
    parameter   DATA_IN_WIDTH = 8,
    parameter   DATA_IN_FRAC_WIDTH = 7,
    parameter   DATA_OUT_WIDTH = 8,
    parameter   DATA_OUT_FRAC_WIDTH = 8
)(
    input logic [DATA_IN_WIDTH - 1:0] data_in,
    output logic [DATA_OUT_WIDTH - 1:0] data_out,
);
    // TODO: testing
    // TODO: 1st get the value  
    // TODO: 2nd normalize the value
    // Linear approximation of 2^n using the formula: 2^n ≈ 1 + n*ln(2)
    // For fixed-point representation, we scale by 2^FRAC_WIDTH
    // 1 is represented as 2^FRAC_WIDTH in our fixed-point format
    // ln(2) ≈ 0.693147... is scaled to fixed-point
    localparam logic [DATA_IN_FIXED_WIDTH-1:0] ONE_FIXED = (1 << FRAC_WIDTH);
    localparam logic [DATA_IN_FIXED_WIDTH-1:0] LN2_FIXED = (FRAC_WIDTH > 8) ? 
                                                 (177 << (FRAC_WIDTH - 8)) : // 0.693147 * 2^8 ≈ 177
                                                 (177 >> (8 - FRAC_WIDTH));  // Scale down if needed
    
    // Linear approximation: 2^n ≈ 1 + n*ln(2)
    assign data_out = ONE_FIXED + ((data_in * LN2_FIXED) >>> FRAC_WIDTH);

endmodule


module fp_to_fixed_conversion #(
    parameter   EXP_WIDTH = 5,
    parameter   MANT_WIDTH = 10,
    parameter   IN_WIDTH = EXP_WIDTH + MANT_WIDTH + 1,
    parameter   OUT_WIDTH = 8,
    parameter   OUT_FRAC_WIDTH = 8
)(
    input logic clk, rst,
    input logic [IN_WIDTH - 1:0] data_in,  // {sign, exp, mant}
    input logic data_in_valid,
    output logic data_in_ready,

    output logic [OUT_WIDTH - 1:0] data_out,
    output logic data_out_valid,
    input logic data_out_ready
);
    //TODO: What is the floating point representation in the repo? BIAS probably wrong
    //TODO:
    //TODO: The fixed point number here should be signed magnitude representation
    localparam signed BIAS = 2**(EXP_WIDTH-1) - 1;
    // Extract components from floating point
    logic sign;
    logic [EXP_WIDTH-1:0] exponent;
    logic [MANT_WIDTH-1:0] mantissa;
    
    // Intermediate signals
    logic [EXP_WIDTH-1:0] integer_part;
    logic [MANT_WIDTH-1:0] fractional_part;
    logic [OUTPUT_WIDTH-1:0] result;
    
    // Pipeline registers
    logic [OUTPUT_WIDTH-1:0] result_reg;
    logic valid_reg;

    localparam REAL_MANT_WIDTH = MANT_WIDTH + 1;
    localparam REAL_MAN_FRAC_WIDTH = MANT_WIDTH - 1;
    logic [REAL_MANT_WIDTH-1:0] real_mantissa;
    logic [OUTPUT_WIDTH-1:0] fixed_point_number;
    
    assign fixed_point_number = data_in[MANT_WIDTH - 1 : 0];

    skid_buffer #(
        .IN_WIDTH(OUT_WIDTH),
        .OUT_WIDTH(OUT_WIDTH)
    ) skid_buffer_inst (
        .data_in(fixed_point_number),
        .data_in_valid(data_in_valid),
        .data_in_ready(data_in_ready),
        .data_out(data_out),
        .data_out_valid(data_out_valid),
        .data_out_ready(data_out_ready)
    );

    // always_comb begin
    //     // Extract components
    //     sign = data_in[EXP_WIDTH + MANT_WIDTH];
    //     exponent = data_in[EXP_WIDTH + MANT_WIDTH - 1 : MANT_WIDTH];
    //     mantissa = data_in[MANT_WIDTH - 1 : 0];
    // end
    
    //     // Calculate integer and fractional parts
    //      = exponent - BIAS; // Subtract bias
    //     fractional_part = mantissa;
        
    //     // Convert to fixed point representation
    //     if (exponent[EXP_WIDTH-1] == 1'b0) begin
    //         // Handle subnormal numbers or zero
    //         real_mantissa =  data_in[MANT_WIDTH - 1 : 0]};
    //     end else if (integer_part >= OUTPUT_WIDTH) begin
    //         // Overflow case
    //         result = sign ? '0 : '1; // Return min/max based on sign
    //     end else begin
    //         // Normal case: shift mantissa according to exponent
    //         result = (1'b1 << integer_part) | (fractional_part >> (MANT_WIDTH - integer_part));
    //         if (sign) begin
    //             result = -result; // Apply sign
    //         end
    //     end
    // end
    
    // // Pipeline stage
    // always_ff @(posedge clk or posedge rst) begin
    //     if (rst) begin
    //         result_reg <= '0;
    //         valid_reg <= 1'b0;
    //     end else if (data_in_valid && data_in_ready) begin
    //         result_reg <= result;
    //         valid_reg <= 1'b1;
    //     end else if (data_out_ready && valid_reg) begin
    //         valid_reg <= 1'b0;
    //     end
    // end
    

endmodule
