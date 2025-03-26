`timescale 1ns / 1ps
/*
Module      : Floating Point Adder Tree
Description : Every two elements are added together in a tree-like structure, 
This module contains the computation within each layer.
The computation process does not sacrifice any precision.
*/

module fp_adder_tree_layer #(
    // Declared Input Width
    parameter OVERALL_INPUT_WIDTH = 16,

    parameter LAYER_DIM  = 2,
    parameter IN_MAN_WIDTH = 4,
    parameter IN_EXP_WIDTH  = 3, 
    
    // Max possible shift bits needed
    localparam int EXT_BITS = (1 << IN_EXP_WIDTH),
    localparam OUT_DIM  = (LAYER_DIM + 1) / 2,
    localparam INPUT_DATA_WIDTH = IN_MAN_WIDTH + IN_EXP_WIDTH,
    localparam OUTPUT_DATA_WIDTH = IN_MAN_WIDTH + EXT_BITS + IN_EXP_WIDTH
) (
    input   logic [OVERALL_INPUT_WIDTH -1 : 0] data_in,
    output  logic [OVERALL_INPUT_WIDTH -1 : 0] data_out
);

    logic last_element_sign;

    generate;
        for (genvar i = 0; i < LAYER_DIM / 2; i++) begin : pair
            fp_add_full_precision #(
                .EXP_WIDTH(IN_EXP_WIDTH),
                .MANT_WIDTH(IN_MAN_WIDTH)
            )   full_precision_fp_add (
                .data_a(data_in[2*i*INPUT_DATA_WIDTH +: INPUT_DATA_WIDTH]),
                .data_b(data_in[(2*i + 1)*INPUT_DATA_WIDTH +: INPUT_DATA_WIDTH]),
                .data_out(data_out[i * OUTPUT_DATA_WIDTH +: OUTPUT_DATA_WIDTH])
            );
        end
    endgenerate

    always @(*) begin
        if (LAYER_DIM % 2 != 0) begin : left
            last_element_sign = data_in[(LAYER_DIM)*INPUT_DATA_WIDTH - 1];
            data_out[(OUT_DIM-1)*OUTPUT_DATA_WIDTH +: INPUT_DATA_WIDTH] = {last_element_sign, {EXT_BITS{1'b0}} ,data_in[(LAYER_DIM-1) * INPUT_DATA_WIDTH +: (INPUT_DATA_WIDTH - 1 )]};
        end
        
    end


endmodule
