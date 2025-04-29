`timescale 1ns / 1ps

/*
Module      : Data Broadcast Module
Timing      : Combinatorial
Description : This module broadcast single element to an unpacked array
*/

module broadcast #(
    parameter DATA_WIDTH,
    parameter BROADCAST_DIM
) (
    input logic [DATA_WIDTH-1:0] in_data,
    output logic [BROADCAST_DIM-1:0] [DATA_WIDTH - 1:0] out_data
);

    generate;
        if (BROADCAST_DIM == 1) begin
            assign out_data = in_data;
        end else begin
            for(genvar i = 0; i < BROADCAST_DIM; i++) begin
                assign out_data[i] = in_data;
            end
        end
    endgenerate


endmodule