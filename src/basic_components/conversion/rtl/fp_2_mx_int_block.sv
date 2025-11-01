`timescale 1ns / 1ps

/*
Module      : fp_2_mx_int_block
Timing      : Combinational Logic
Description : Convert a block of IEEE FP numbers to MXINT format
The mxint format will be composed with block of signed mantissas and a shared scale (max_exp)
Mant part will be Q0.x format
*/

module fp_2_mx_int_block #(
    parameter BLOCK_DIM = 8, 
    parameter FP_MANT_WIDTH = 3,
    parameter FP_EXP_WIDTH = 4,
    localparam MXINT_MANT_WIDTH = FP_MANT_WIDTH + 2,
    localparam MXINT_SCALE_WIDTH = FP_EXP_WIDTH
)(
    input   logic [FP_MANT_WIDTH + FP_EXP_WIDTH : 0] data_in [BLOCK_DIM-1:0],
    output  logic signed [MXINT_MANT_WIDTH : 0] element_data_out [BLOCK_DIM-1:0],
    output  logic signed [MXINT_SCALE_WIDTH-1:0] scale_data_out
);
    localparam SIGNED_MANT_WIDTH = FP_MANT_WIDTH + 2;  // Output from fp_ieee_partition

    // Step 1: Partition all FP numbers into signed exp and mant
    logic signed [FP_EXP_WIDTH-1:0] signed_exp [BLOCK_DIM-1:0];
    logic signed [SIGNED_MANT_WIDTH-1:0] signed_mant [BLOCK_DIM-1:0];

    for (genvar i = 0; i < BLOCK_DIM; i++) begin : gen_partition
        fp_ieee_partition #(
            .EXP_WIDTH(FP_EXP_WIDTH),
            .MANT_WIDTH(FP_MANT_WIDTH)
        ) partition_inst (
            .data_in        (data_in[i]),
            .signed_exp     (signed_exp[i]),
            .signed_mant    (signed_mant[i])
        );
    end

    // Step 2: Find max exponent
    logic signed [FP_EXP_WIDTH-1:0] signed_exp_max;
    
    // Simple combinational max finder (tree structure)
    always_comb begin
        signed_exp_max = signed_exp[0];
        for (int i = 1; i < BLOCK_DIM; i++) begin
            if ($signed(signed_exp[i]) > $signed(signed_exp_max)) begin
                signed_exp_max = signed_exp[i];
            end
        end
    end

    // Output the scale (max exponent)
    assign scale_data_out = signed_exp_max;
    logic signed [FP_EXP_WIDTH:0] shift_amount[BLOCK_DIM-1:0];
    logic signed [SIGNED_MANT_WIDTH-1:0] mant_to_shift[BLOCK_DIM-1:0];
    logic signed [SIGNED_MANT_WIDTH-1:0] shifted_result[BLOCK_DIM-1:0];

    // Step 3: Shift all mantissas based on (max_exp - their_exp)
    for (genvar i = 0; i < BLOCK_DIM; i++) begin : gen_shift

        always_comb begin
            shift_amount[i] = signed_exp[i] - signed_exp_max;
            mant_to_shift[i] = signed_mant[i];
        end

        bit_width_aware_signed_left_shift #(
            .IN_WIDTH(SIGNED_MANT_WIDTH),
            .OUT_WIDTH(MXINT_MANT_WIDTH),
            .SHIFT_WIDTH(FP_EXP_WIDTH)
        ) shift_inst (
            .in_data(mant_to_shift[i]),
            .shift_amt(shift_amount[i]),
            .out_data(shifted_result[i])
        );
        assign element_data_out[i]=shifted_result[i];
    end

endmodule


