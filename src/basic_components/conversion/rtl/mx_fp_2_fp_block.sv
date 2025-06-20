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
        assert (MXFP_SCALE_WIDTH > FP_EXP_WIDTH)
            else $error("FP_EXP_WIDTH must be less than MXFP_SCALE_WIDTH");
    end

    localparam int FP_BIAS          = (1 << (FP_EXP_WIDTH - 1)) - 1;
    localparam int ELEMENT_EXP_BIAS = (1 << (MXFP_EXP_WIDTH - 1)) - 1;
    localparam int SCALE_BIAS      = (1 << (MXFP_SCALE_WIDTH - 1)) - 1;

    logic [BLOCK_DIM-1:0]                       mxfp_sign;
    logic [BLOCK_DIM-1:0][MXFP_EXP_WIDTH-1:0]   mxfp_exp;
    logic [BLOCK_DIM-1:0][MXFP_MANT_WIDTH-1:0]  mxfp_mant;

    logic [MXFP_SCALE_WIDTH -1:0]                   fp_exp_base;

    logic [BLOCK_DIM-1:0]exp_overflow;
    logic [BLOCK_DIM-1:0][FP_MANT_WIDTH-1:0]  mant_out;
    logic [BLOCK_DIM-1:0][MXFP_SCALE_WIDTH-1:0] temp_exp;
    logic [BLOCK_DIM-1:0][FP_EXP_WIDTH-1:0] exp_out;    

    generate;
        assign fp_exp_base  = scale_in - SCALE_BIAS + FP_BIAS;
        for (genvar i = 0; i < BLOCK_DIM; i=i+1) begin
            if (MXFP_MANT_WIDTH >= FP_MANT_WIDTH) begin
                assign mant_out[i] = mxfp_mant[i][MXFP_MANT_WIDTH - 1 -: FP_MANT_WIDTH];
            end else begin
                assign mant_out[i] = {mxfp_mant[i][MXFP_MANT_WIDTH - 1 : 0], {FP_MANT_WIDTH - MXFP_MANT_WIDTH{1'b0}}};
            end
            always_comb begin
                // Decompose input MX-FP value
                mxfp_sign[i]     = element_in[i][MXFP_MANT_WIDTH + MXFP_EXP_WIDTH];
                mxfp_exp[i]      = element_in[i][MXFP_EXP_WIDTH + MXFP_MANT_WIDTH - 1 : MXFP_MANT_WIDTH];
                mxfp_mant[i]     = element_in[i][MXFP_MANT_WIDTH - 1 : 0];
                temp_exp[i]      = fp_exp_base + {{(FP_EXP_WIDTH - MXFP_EXP_WIDTH){1'b0}}, mxfp_exp[i]} - ELEMENT_EXP_BIAS;
                exp_overflow[i]  = |temp_exp[i][MXFP_SCALE_WIDTH - 1 : FP_EXP_WIDTH];

                if (exp_overflow[i]) begin
                    exp_out[i] = {{(FP_EXP_WIDTH - 1){1'b1}}, 1'b0}; // Max exp val
                end
                else begin
                    exp_out[i] = temp_exp[i][FP_EXP_WIDTH - 1 : 0];
                end
                fp_out[i] = {mxfp_sign[i], exp_out[i], mant_out[i]};
            end

             
        end
        
    endgenerate

endmodule