`timescale 1ns / 1ps
`include "operation.svh"
/*
Module      : Floating Point Reduction Tree
Timing      : Combinatorial Logic
Description : Binary Tree Reduction of Floating Point Numbers, supporting:
            1. SUM
            2. MAX
            We assume the Layer Dim is in power of 2.
Status      : Under Development
*/

module vector_reduce_layer #(
    parameter LAYER_DIM  = 2,
    parameter IN_MAN_WIDTH = 4,
    parameter IN_EXP_WIDTH  = 3, 
    
    // In the first version vector machine, we assume all the extension related bits are zero.
    parameter EXT_MANT_WIDTH = 0,
    parameter EXT_EXP_WIDTH = 0,   

    localparam OUT_DIM  = (LAYER_DIM + 1) / 2,
    localparam INPUT_DATA_WIDTH = IN_MAN_WIDTH + IN_EXP_WIDTH + 1,
    localparam OUTPUT_DATA_WIDTH = IN_MAN_WIDTH + EXT_MANT_WIDTH + IN_EXP_WIDTH + EXT_EXP_WIDTH + 1
) (
    input   RED_V_OPERAND operation, // 0: SUM, 1: MAX
    input   logic [LAYER_DIM * INPUT_DATA_WIDTH  -1 : 0] data_in,
    output  logic [OUT_DIM * OUTPUT_DATA_WIDTH -1 : 0] data_out
);
    
    logic [OUT_DIM * OUTPUT_DATA_WIDTH -1 : 0] layer_add_out, layer_max_out;

    always_comb begin
        case (operation)
            SUM: begin
                data_out = layer_add_out;
            end

            MAX: begin
                data_out = layer_max_out;
            end

            default: begin
                data_out = '0; // Default case to avoid latches
            end
        endcase
    end


    generate;
        for (genvar i = 0; i < LAYER_DIM / 2; i++) begin : adder_pair
            fp_cp_adder #(
                .EXP_WIDTH(IN_EXP_WIDTH),
                .MANT_WIDTH(IN_MAN_WIDTH),
                .EXT_MANT_WIDTH(EXT_MANT_WIDTH),
                .EXT_EXP_WIDTH(EXT_EXP_WIDTH)
            )   fp_add (
                .data_a(data_in[2*i*INPUT_DATA_WIDTH +: INPUT_DATA_WIDTH]),
                .data_b(data_in[(2*i + 1)*INPUT_DATA_WIDTH +: INPUT_DATA_WIDTH]),
                .data_out(layer_add_out[i * OUTPUT_DATA_WIDTH +: OUTPUT_DATA_WIDTH])
            );

            fp_max #(
                .EXP_WIDTH(IN_EXP_WIDTH),
                .MANT_WIDTH(IN_MAN_WIDTH)
            )   fp_add (
                .data_a(data_in[2*i*INPUT_DATA_WIDTH +: INPUT_DATA_WIDTH]),
                .data_b(data_in[(2*i + 1)*INPUT_DATA_WIDTH +: INPUT_DATA_WIDTH]),
                .data_out(layer_max_out[i * OUTPUT_DATA_WIDTH +: OUTPUT_DATA_WIDTH])
            );

        end
    endgenerate
    

endmodule
