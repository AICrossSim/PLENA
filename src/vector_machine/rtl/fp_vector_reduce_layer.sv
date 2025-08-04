`timescale 1ns / 1ps

`include "configuration.svh"
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

module fp_vector_reduce_layer #(
    // Declared Input Width
    parameter OVERALL_INPUT_WIDTH = 16,

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
    input   logic clk,
    input   logic rst,
    input   V_REDUCT_OP operation, // 0: SUM, 1: MAX
    input   logic [OVERALL_INPUT_WIDTH -1 : 0] data_in,
    input   logic data_in_valid,
    output  logic data_in_ready,
    output  logic [OVERALL_INPUT_WIDTH -1 : 0] data_out,
    output  logic data_out_valid,
    input   logic data_out_ready
);
    
    logic [OUT_DIM * OUTPUT_DATA_WIDTH -1 : 0] layer_add_out, layer_max_out;

    logic [LAYER_DIM / 2 - 1: 0] adder_data_in_valid_array,     adder_data_in_ready_array;
    logic [LAYER_DIM / 2 - 1: 0] adder_data_out_valid_array,    adder_data_out_ready_array;
    logic [LAYER_DIM / 2 - 1: 0] max_data_in_valid_array,       max_data_in_ready_array;
    logic [LAYER_DIM / 2 - 1: 0] max_data_out_valid_array,      max_data_out_ready_array;

    logic sum_data_in_valid, sum_data_in_ready;
    logic sum_data_out_valid, sum_data_out_ready;
    logic max_data_in_valid, max_data_in_ready;
    logic max_data_out_valid, max_data_out_ready;

    always_comb begin
        case (operation)
            SUM_V_REDUCT: begin
                sum_data_in_valid   = data_in_valid;
                data_in_ready       = sum_data_in_ready;
                data_out_valid      = sum_data_out_valid;
                sum_data_out_ready  = data_out_ready;
                data_out = {{OVERALL_INPUT_WIDTH - OUT_DIM * OUTPUT_DATA_WIDTH{1'b0}} ,layer_add_out};
            end

            MAX_V_REDUCT: begin
                max_data_in_valid   = data_in_valid;
                data_in_ready       = max_data_in_ready;
                data_out_valid      = max_data_out_valid;
                max_data_out_ready  = data_out_ready;
                data_out = {{OVERALL_INPUT_WIDTH - OUT_DIM * OUTPUT_DATA_WIDTH{1'b0}} ,layer_max_out};
            end

            default: begin
                data_out = {OVERALL_INPUT_WIDTH{1'b0}}; // Default case to avoid latches
            end
        endcase
    end

    split_n #(
        .N(LAYER_DIM / 2)
    ) split_sum_signal (
        .data_in_valid(sum_data_in_valid),
        .data_in_ready(sum_data_in_ready),
        .data_out_valid(adder_data_in_valid_array),
        .data_out_ready(adder_data_in_ready_array)
    );

    split_n #(
        .N(LAYER_DIM / 2)
    ) split_max_signal (
        .data_in_valid(max_data_in_valid),
        .data_in_ready(max_data_in_ready),
        .data_out_valid(max_data_in_valid_array),
        .data_out_ready(max_data_in_ready_array)
    );



    generate;
        for (genvar i = 0; i < LAYER_DIM / 2; i++) begin : adder_pair
            // fp_cp_adder #(
            //     .EXP_WIDTH(IN_EXP_WIDTH),
            //     .MANT_WIDTH(IN_MAN_WIDTH),
            //     .EXT_MANT_WIDTH(EXT_MANT_WIDTH),
            //     .EXT_EXP_WIDTH(EXT_EXP_WIDTH)
            // )   layer_fp_add (
            //     .clk(clk),
            //     .rst(rst),
            //     .data_in_valid      (adder_data_in_valid_array[i]),
            //     .data_in_ready      (adder_data_in_ready_array[i]),
            //     .data_a             (data_in[2*i*INPUT_DATA_WIDTH +: INPUT_DATA_WIDTH]),
            //     .data_b             (data_in[(2*i + 1)*INPUT_DATA_WIDTH +: INPUT_DATA_WIDTH]),
            //     .data_out           (layer_add_out[i * OUTPUT_DATA_WIDTH +: OUTPUT_DATA_WIDTH]),
            //     .data_out_valid     (adder_data_out_valid_array[i]),
            //     .data_out_ready     (adder_data_out_ready_array[i])
            // );

            fp_cp_adder #(
                .EXP_WIDTH(IN_EXP_WIDTH),
                .MANT_WIDTH(IN_MAN_WIDTH)
            )   layer_fp_add (
                .clk(clk),
                .rst(rst),
                .data_in_valid      (adder_data_in_valid_array[i]),
                .data_in_ready      (adder_data_in_ready_array[i]),
                .data_a             (data_in[2*i*INPUT_DATA_WIDTH +: INPUT_DATA_WIDTH]),
                .data_b             (data_in[(2*i + 1)*INPUT_DATA_WIDTH +: INPUT_DATA_WIDTH]),
                .data_out           (layer_add_out[i * OUTPUT_DATA_WIDTH +: OUTPUT_DATA_WIDTH]),
                .data_out_valid     (adder_data_out_valid_array[i]),
                .data_out_ready     (adder_data_out_ready_array[i])
            );

            fp_max #(
                .EXP_WIDTH(IN_EXP_WIDTH),
                .MANT_WIDTH(IN_MAN_WIDTH)
            )   layer_fp_max (
                .clk(clk),
                .rst(rst),
                .data_in_valid      (max_data_in_valid_array[i]),
                .data_in_ready      (max_data_in_ready_array[i]),
                .data_a             (data_in[2*i*INPUT_DATA_WIDTH +: INPUT_DATA_WIDTH]),
                .data_b             (data_in[(2*i + 1)*INPUT_DATA_WIDTH +: INPUT_DATA_WIDTH]),
                .data_out           (layer_max_out[i * OUTPUT_DATA_WIDTH +: OUTPUT_DATA_WIDTH]),
                .data_out_valid     (max_data_out_valid_array[i]),
                .data_out_ready     (max_data_out_ready_array[i])
            );

        end
    endgenerate
    

    join_n #(
        .NUM_HANDSHAKES(LAYER_DIM / 2)
    ) join_sum_sig (
        .data_in_valid  (adder_data_out_valid_array),
        .data_in_ready  (adder_data_out_ready_array),
        .data_out_valid (sum_data_out_valid),
        .data_out_ready (sum_data_out_ready)
    );

    join_n #(
        .NUM_HANDSHAKES(LAYER_DIM / 2)
    ) join_max_sig (
        .data_in_valid  (max_data_out_valid_array),
        .data_in_ready  (max_data_out_ready_array),
        .data_out_valid (max_data_out_valid),
        .data_out_ready (max_data_out_ready)
    );

endmodule
