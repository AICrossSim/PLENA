`timescale 1ns / 1ps
/*
Module      : Floating Point Adder Tree
Timing      : Combinatorial Logic
Description : Every two elements are added together in a tree-like structure, 
              This module contains the computation within each layer.
              The computation process does not sacrifice any precision.
Status      : Passed Simple Tests
*/

module fp_adder_tree_layer #(
    // Declared Input Width
    parameter OVERALL_INPUT_WIDTH = 16,

    parameter LAYER_DIM  = 2,
    parameter IN_MAN_WIDTH = 4,
    parameter IN_EXP_WIDTH  = 3, 
    
    // Max possible shift bits needed
    parameter EXT_MANT_WIDTH = 1,
    parameter EXT_EXP_WIDTH = 1,   

    localparam OUT_DIM  = (LAYER_DIM + 1) / 2,
    localparam INPUT_DATA_WIDTH = IN_MAN_WIDTH + IN_EXP_WIDTH + 1,
    localparam OUTPUT_DATA_WIDTH = IN_MAN_WIDTH + EXT_MANT_WIDTH + IN_EXP_WIDTH + EXT_EXP_WIDTH + 1
) (
    input   logic [OVERALL_INPUT_WIDTH -1 : 0] data_in,
    output  logic [OVERALL_INPUT_WIDTH -1 : 0] data_out
);

    logic last_element_sign;
    localparam UNUSED_BITS = OVERALL_INPUT_WIDTH - OUTPUT_DATA_WIDTH * LAYER_DIM;
    
    localparam int BIAS = (1 << (IN_EXP_WIDTH - 1)) - 1;
    localparam int NEW_BIAS = (1 << ((IN_EXP_WIDTH + EXT_EXP_WIDTH) - 1)) - 1;
    localparam int UPDATED_BIAS = NEW_BIAS - BIAS;

    logic [IN_EXP_WIDTH + EXT_EXP_WIDTH - 1:0] updated_exp;
    logic [IN_MAN_WIDTH + EXT_MANT_WIDTH - 1:0] updated_man;

    generate;
        for (genvar i = 0; i < LAYER_DIM / 2; i++) begin : pair
            fp_cp_adder_v1 #(
                .EXP_WIDTH(IN_EXP_WIDTH),
                .MANT_WIDTH(IN_MAN_WIDTH),
                .EXT_MANT_WIDTH(EXT_MANT_WIDTH),
                .EXT_EXP_WIDTH(EXT_EXP_WIDTH)
            )   fp_add (
                .data_a(data_in[2*i*INPUT_DATA_WIDTH +: INPUT_DATA_WIDTH]),
                .data_b(data_in[(2*i + 1)*INPUT_DATA_WIDTH +: INPUT_DATA_WIDTH]),
                .data_out(data_out[i * OUTPUT_DATA_WIDTH +: OUTPUT_DATA_WIDTH])
            );
        end
    endgenerate
    

    
    always_comb begin
        if (LAYER_DIM % 2 != 0) begin : left
            last_element_sign = data_in[(LAYER_DIM) * INPUT_DATA_WIDTH - 1];
            updated_exp = {{EXT_EXP_WIDTH{1'b0}}, data_in[(LAYER_DIM)*INPUT_DATA_WIDTH - 2 -: IN_EXP_WIDTH]} + UPDATED_BIAS[IN_EXP_WIDTH + EXT_EXP_WIDTH - 1 : 0];
            updated_man = {data_in[(LAYER_DIM) * INPUT_DATA_WIDTH - 2 - IN_MAN_WIDTH : (LAYER_DIM - 1) * INPUT_DATA_WIDTH], {EXT_MANT_WIDTH{1'b0}}};
            data_out[(OUT_DIM-1)*OUTPUT_DATA_WIDTH +: OUTPUT_DATA_WIDTH] = {last_element_sign, updated_exp, updated_man};
        end
        else begin
            last_element_sign = 1'b0;
            updated_exp = {EXT_EXP_WIDTH{1'b0}};
            updated_man = 0;
        end
        
    end


endmodule
