`timescale 1ns / 1ps

/*
Module      : Convertion a block unit of mx-fp data to fp data
Timing      : Combinatorial Logic
Status      : Passed Simple Tests, 
TODO:       : Need to consider the case MXFP_SCALE < FP_EXP_WIDTH
*/


module mx_fp_2_fp_block #(
    parameter BLOCK_DIM = 8, 
    parameter MXFP_MANT_WIDTH = 3,
    parameter MXFP_EXP_WIDTH = 4,
    parameter MXFP_SCALE_WIDTH = 8,

    parameter FP_MANT_WIDTH = 3,
    parameter FP_EXP_WIDTH = 4
)(
    input   logic [BLOCK_DIM-1:0][MXFP_MANT_WIDTH + MXFP_EXP_WIDTH : 0] element_in,
    input   logic [MXFP_SCALE_WIDTH-1:0] scale_in,
    output  logic [BLOCK_DIM-1:0][FP_MANT_WIDTH + FP_EXP_WIDTH : 0] fp_out
);
    initial begin
        // To ensure the output mantissa is large enough to hold the input mantissa.
        assert (MXFP_SCALE_WIDTH >= FP_EXP_WIDTH)
            else $error("MXFP_SCALE_WIDTH must be greater than or equal to FP_EXP_WIDTH");
    end

    for (genvar i = 0; i < BLOCK_DIM; i++) begin
        mx_fp_2_fp_unary #(
            .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
            .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
            .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
            .FP_MANT_WIDTH(FP_MANT_WIDTH),
            .FP_EXP_WIDTH(FP_EXP_WIDTH)
        ) mx_fp_2_fp_unary_inst (
            .element_data_in(element_in[i]),
            .scale_data_in(scale_in),
            .fp_out(fp_out[i])
        );
    end


endmodule
