`timescale 1ns / 1ps

/*
Module      : Unary Convertion from FP with Configurable Precision to MX-FP
Timing      : Combinatorial Logic
Description : 
Status      : Passed Simple Tests
*/

module fp_2_mx_fp_unary #(
    parameter FP_EXP_WIDTH = 4,
    parameter FP_MANT_WIDTH = 3,
    parameter MXFP_EXP_WIDTH = 4,
    parameter MXFP_MANT_WIDTH = 3,
    parameter MXFP_SCALE_WIDTH = 8
)(
    input  logic [FP_EXP_WIDTH + FP_MANT_WIDTH : 0] fp_in,
    output logic [MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] element_data_out,
    output logic [MXFP_SCALE_WIDTH - 1 : 0] scale_data_out
);

    initial begin
        assert (MXFP_SCALE_WIDTH > FP_EXP_WIDTH)
            else $error("FP_EXP_WIDTH must be less than MX_FP_SCALE_WIDTH");
    end
    localparam int BIAS = (1 << (FP_EXP_WIDTH - 1)) - 1;
    localparam int NEW_BIAS = (1 << ((MXFP_SCALE_WIDTH) - 1)) - 1;
    localparam int UPDATED_BIAS = NEW_BIAS - BIAS;

    // Decompose input FP value
    logic                        fp_sign;
    logic [FP_EXP_WIDTH-1:0]     fp_exp;
    logic [FP_MANT_WIDTH-1:0]    fp_mant;

    assign fp_sign = fp_in[FP_EXP_WIDTH + FP_MANT_WIDTH];
    assign fp_exp  = fp_in[FP_EXP_WIDTH + FP_MANT_WIDTH - 1 : FP_MANT_WIDTH];
    assign fp_mant = fp_in[FP_MANT_WIDTH - 1 : 0];

    // Convert to MX-FP format
    generate;
        if (FP_MANT_WIDTH >= MXFP_MANT_WIDTH) begin
            assign element_data_out = {fp_sign, 1'b0, {(MXFP_EXP_WIDTH - 1){1'b1}} , fp_mant[FP_MANT_WIDTH - 1 -: MXFP_MANT_WIDTH]};
        end
        else begin
            assign element_data_out = {fp_sign, 1'b0, {(MXFP_EXP_WIDTH - 1){1'b1}} , fp_mant[FP_MANT_WIDTH - 1 : 0], {MXFP_MANT_WIDTH - FP_MANT_WIDTH{1'b0}}};
        end

        // Scale the exponent
        assign scale_data_out = {{(MXFP_SCALE_WIDTH - FP_EXP_WIDTH){1'b0}}, fp_exp} + UPDATED_BIAS;
    endgenerate


endmodule