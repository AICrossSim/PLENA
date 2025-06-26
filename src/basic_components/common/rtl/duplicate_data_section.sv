`timescale 1ns / 1ps

/*
Module      : duplicate data section
Description : This module receives data and repeats it N times.
                ABCD -> AABBCCDD
*/

module duplicate_data_section #(
    parameter REPEAT = 2,
    parameter BITSTREAM_WIDTH = 12,
    parameter DATA_SEC_WIDTH = BITSTREAM_WIDTH,
    localparam SEC_NUM = BITSTREAM_WIDTH / DATA_SEC_WIDTH
) (
    input   logic   [BITSTREAM_WIDTH-1:0] in_data,
    output  logic   [BITSTREAM_WIDTH * REPEAT - 1:0] out_data
);

    generate
        if (REPEAT == 1) begin : gen_passthrough
            assign out_data = in_data;
        end else begin : gen_repeater
            for(genvar i = 0; i < SEC_NUM; i++) begin : gen_repeat
                for (genvar j = 0; j < REPEAT; j++) begin : gen_repeat_inner
                    assign out_data[(i * REPEAT + j) * DATA_SEC_WIDTH +: DATA_SEC_WIDTH] = in_data[i * DATA_SEC_WIDTH +: DATA_SEC_WIDTH];
                end
            end
        end
    endgenerate


endmodule