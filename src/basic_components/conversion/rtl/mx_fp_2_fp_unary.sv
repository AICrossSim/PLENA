`timescale 1ns / 1ps

/*
Module      : Unary Convertion from MX-FP to FP
Timing      : Combinatorial Logic
Description : 
Status      : Passed Simple Tests
*/

module mx_fp_2_fp_unary #(
    parameter MXFP_EXP_WIDTH = 4,
    parameter MXFP_MANT_WIDTH = 3,
    parameter MXFP_SCALE_WIDTH = 8,
    parameter FP_EXP_WIDTH = 4,
    parameter FP_MANT_WIDTH = 3
)(
    
    input   logic [MXFP_EXP_WIDTH + MXFP_MANT_WIDTH : 0] element_data_in,
    input   logic [MXFP_SCALE_WIDTH - 1 : 0] scale_data_in,
    output  logic [FP_EXP_WIDTH + FP_MANT_WIDTH : 0] fp_out
);

    // initial begin
    //     assert (MXFP_SCALE_WIDTH > FP_EXP_WIDTH)
    //         else $error("FP_EXP_WIDTH must be less than MXFP_SCALE_WIDTH");
    // end

    localparam int FP_BIAS      = (1 << (FP_EXP_WIDTH - 1)) - 1;
    localparam int ELEMENT_EXP_BIAS = (1 << (MXFP_EXP_WIDTH - 1)) - 1;
    localparam int SCALE_BIAS   = (1 << ((MXFP_SCALE_WIDTH) - 1)) - 1;


    // Decompose input MX-FP value

    logic                       mxfp_sign;
    logic [MXFP_EXP_WIDTH-1:0]  mxfp_exp;
    logic [MXFP_MANT_WIDTH-1:0] mxfp_mant;

    assign mxfp_sign = element_data_in[MXFP_EXP_WIDTH + MXFP_MANT_WIDTH];
    assign mxfp_exp  = element_data_in[MXFP_EXP_WIDTH + MXFP_MANT_WIDTH - 1 : MXFP_MANT_WIDTH];
    assign mxfp_mant = element_data_in[MXFP_MANT_WIDTH - 1 : 0];

    logic [FP_MANT_WIDTH -1:0] mant_out;
    logic [FP_EXP_WIDTH -1:0] exp_out;


    generate;
        if (MXFP_MANT_WIDTH >= FP_MANT_WIDTH) begin
            assign mant_out = mxfp_mant[MXFP_MANT_WIDTH - 1 -: FP_MANT_WIDTH];
        end
        else begin
            assign mant_out = {mxfp_mant[MXFP_MANT_WIDTH - 1 : 0], {FP_MANT_WIDTH - MXFP_MANT_WIDTH{1'b0}}};
        end
    endgenerate

    // Calculate exponent
    generate;
        if (MXFP_SCALE_WIDTH > FP_EXP_WIDTH) begin
            logic [MXFP_SCALE_WIDTH - 1 : 0] temp_exp;
            logic exp_overflow;
            always_comb begin
                temp_exp = scale_data_in - SCALE_BIAS + {{(MXFP_SCALE_WIDTH - MXFP_EXP_WIDTH){1'b0}}, mxfp_exp} - ELEMENT_EXP_BIAS + FP_BIAS;
                exp_overflow = |temp_exp[MXFP_SCALE_WIDTH - 1 : FP_EXP_WIDTH];

                if (exp_overflow) begin
                    exp_out = {{(FP_EXP_WIDTH - 1){1'b1}}, 1'b0};
                end
                else begin
                    exp_out = temp_exp[FP_EXP_WIDTH - 1 : 0];
                end
            end
        end else begin
            // There is no overflow, so we can just add the scale and exponent
            assign exp_out = {{(FP_EXP_WIDTH - MXFP_SCALE_WIDTH){1'b0}}, scale_data_in}  - SCALE_BIAS + {{(FP_EXP_WIDTH - MXFP_EXP_WIDTH){1'b0}}, mxfp_exp} - ELEMENT_EXP_BIAS + FP_BIAS;
        end
    endgenerate

    assign fp_out = {mxfp_sign, exp_out, mant_out};

endmodule