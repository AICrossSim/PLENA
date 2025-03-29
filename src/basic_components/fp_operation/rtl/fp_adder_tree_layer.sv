`timescale 1ns / 1ps
/*
Module      : Floating Point Adder Tree
Timing      : Combinatorial Logic
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
    parameter EXT_MANT_BITS = 1,
    parameter EXT_EXP_BITS = 1,   

    localparam OUT_DIM  = (LAYER_DIM + 1) / 2,
    localparam INPUT_DATA_WIDTH = IN_MAN_WIDTH + IN_EXP_WIDTH + 1,
    localparam OUTPUT_DATA_WIDTH = IN_MAN_WIDTH + EXT_MANT_BITS + IN_EXP_WIDTH + EXT_EXP_BITS + 1
) (
    input   logic [OVERALL_INPUT_WIDTH -1 : 0] data_in,
    output  logic [OVERALL_INPUT_WIDTH -1 : 0] data_out
);

    logic last_element_sign;
    localparam UNUSED_BITS = OVERALL_INPUT_WIDTH - OUTPUT_DATA_WIDTH * LAYER_DIM;

    generate;
        for (genvar i = 0; i < LAYER_DIM / 2; i++) begin : pair
            fp_cp_adder #(
                .EXP_WIDTH(IN_EXP_WIDTH),
                .MANT_WIDTH(IN_MAN_WIDTH),
                .EXT_MANT_WIDTH(EXT_MANT_BITS),
                .EXT_EXP_WIDTH(EXT_EXP_BITS)
            )   fp_add (
                .data_a(data_in[2*i*INPUT_DATA_WIDTH +: INPUT_DATA_WIDTH]),
                .data_b(data_in[(2*i + 1)*INPUT_DATA_WIDTH +: INPUT_DATA_WIDTH]),
                .data_out(data_out[i * OUTPUT_DATA_WIDTH +: OUTPUT_DATA_WIDTH])
            );
        end
    endgenerate

    always @(*) begin
        if (LAYER_DIM % 2 != 0) begin : left
            last_element_sign = data_in[(LAYER_DIM)*INPUT_DATA_WIDTH - 1];
            data_out[(OUT_DIM-1)*OUTPUT_DATA_WIDTH +: OUTPUT_DATA_WIDTH] = {last_element_sign, 1'b0, data_in[(LAYER_DIM-1) * INPUT_DATA_WIDTH +: (INPUT_DATA_WIDTH - 1 )], {EXT_MANT_BITS{1'b0}}};
        end
        // assign data_out[OVERALL_INPUT_WIDTH -1 -: OVERALL_INPUT_WIDTH] = {OVERALL_INPUT_WIDTH{1'b0}};
        
    end


endmodule
