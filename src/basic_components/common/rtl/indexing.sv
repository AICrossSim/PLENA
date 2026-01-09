`timescale 1ns / 1ps

/*
Module      : Indexing Module
Timing      : Combinatorial
Description : This module takes an array and a target value (number), and returns 
              the index where the array element equals that target value.
*/

module indexing #(
    parameter DATA_WIDTH = 16,
    parameter ARRAY_SIZE = 4,
    parameter INDEX_WIDTH = (ARRAY_SIZE > 1) ? $clog2(ARRAY_SIZE) : 1
) (
    input  logic [ARRAY_SIZE-1:0] [DATA_WIDTH-1:0] in_array,
    input  logic [DATA_WIDTH-1:0]                  in_num,
    output logic [INDEX_WIDTH-1:0] out_index,
);

    assign out_index = in_array == in_num ? 1 : 0;

endmodule
