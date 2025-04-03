`timescale 1ns / 1ps
/*
Module      : MX-FP Configurable Precision Unit Adder Tree
Timing      : Combinatorial Logic
Description : Every two elements are added together in a tree-like structure, 
              This module contains the computation within each layer.
              The computation process does not sacrifice any precision.
Status      : Passed Simple Tests
*/

module mx_fp_unit_adder_tree_layer #(
    // Declared Input Width
    parameter ELEMENT_ARRAY_WIDTH = 16,
    parameter SCALE_ARRAY_WIDTH = 8,

    parameter LAYER_DIM  = 2,

    parameter MXFP_EXP_WIDTH = 4,
    parameter MXFP_MANT_WIDTH = 3,
    parameter MXFP_SCALE_WIDTH = 8,
    
    // Max possible shift bits needed
    parameter EXT_MANT_WIDTH = 1,
    parameter EXT_EXP_WIDTH = 1,   

    localparam OUT_DIM  = (LAYER_DIM + 1) / 2,
    localparam INPUT_ELEMENT_WIDTH = MXFP_MANT_WIDTH + MXFP_EXP_WIDTH + 1,
    localparam OUTPUT_ELEMENT_WIDTH = MXFP_MANT_WIDTH + EXT_MANT_WIDTH + MXFP_EXP_WIDTH + EXT_EXP_WIDTH + 1

) (
    input   logic [ELEMENT_ARRAY_WIDTH -1 : 0]  element_data_in,
    input   logic [SCALE_ARRAY_WIDTH -1 : 0]    scale_data_in,
    output  logic [ELEMENT_ARRAY_WIDTH -1 : 0]  element_data_out,
    output  logic [SCALE_ARRAY_WIDTH -1 : 0]    scale_data_out
);

    logic last_element_sign;
    localparam UNUSED_BITS = ELEMENT_ARRAY_WIDTH - OUTPUT_ELEMENT_WIDTH * LAYER_DIM;
    
    localparam int BIAS = (1 << (MXFP_EXP_WIDTH - 1)) - 1;
    localparam int NEW_BIAS = (1 << ((MXFP_EXP_WIDTH + EXT_EXP_WIDTH) - 1)) - 1;
    localparam int UPDATED_BIAS = NEW_BIAS - BIAS;

    logic [MXFP_EXP_WIDTH + EXT_EXP_WIDTH - 1:0]    updated_exp;
    logic [MXFP_MANT_WIDTH + EXT_MANT_WIDTH - 1:0]  updated_man;

    generate;
        for (genvar i = 0; i < LAYER_DIM / 2; i++) begin : pair
            mx_fp_unit_adder #(
                .MXFP_EXP_WIDTH(MXFP_EXP_WIDTH),
                .MXFP_MANT_WIDTH(MXFP_MANT_WIDTH),
                .MXFP_SCALE_WIDTH(MXFP_SCALE_WIDTH),
                .EXT_MANT_WIDTH(EXT_MANT_WIDTH),
                .EXT_EXP_WIDTH(EXT_EXP_WIDTH)
            )   mx_fp_addition (
                .element_data_a(element_data_in[2*i*INPUT_ELEMENT_WIDTH +: INPUT_ELEMENT_WIDTH]),
                .element_data_b(element_data_in[(2*i + 1)*INPUT_ELEMENT_WIDTH +: INPUT_ELEMENT_WIDTH]),
                .scale_data_a(scale_data_in[2*i*SCALE_ARRAY_WIDTH +: SCALE_ARRAY_WIDTH]),
                .scale_data_b(scale_data_in[(2*i + 1)*SCALE_ARRAY_WIDTH +: SCALE_ARRAY_WIDTH]),
                .element_data_out(element_data_out[i * OUTPUT_ELEMENT_WIDTH +: OUTPUT_ELEMENT_WIDTH])
            );
        end
    endgenerate
    
    
    always_comb begin
        if (LAYER_DIM % 2 != 0) begin : left
            last_element_sign = element_data_in[(LAYER_DIM) * INPUT_ELEMENT_WIDTH - 1];
            updated_exp = {{EXT_EXP_WIDTH{1'b0}}, element_data_in[(LAYER_DIM)*INPUT_ELEMENT_WIDTH - 2 -: MXFP_EXP_WIDTH]} + UPDATED_BIAS[MXFP_EXP_WIDTH + EXT_EXP_WIDTH - 1 : 0];
            updated_man = {element_data_in[(LAYER_DIM) * INPUT_ELEMENT_WIDTH - 2 - MXFP_MANT_WIDTH : (LAYER_DIM - 1) * INPUT_ELEMENT_WIDTH], {EXT_MANT_WIDTH{1'b0}}};
            element_data_out[(OUT_DIM-1)*OUTPUT_ELEMENT_WIDTH +: OUTPUT_ELEMENT_WIDTH] = {last_element_sign, updated_exp, updated_man};
            scale_data_out[(LAYER_DIM) * SCALE_ARRAY_WIDTH - 1 : 0] = scale_data_in[(LAYER_DIM) * SCALE_ARRAY_WIDTH - 1 : 0];
        end        
    end


endmodule
