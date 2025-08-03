`timescale 1ns / 1ps
`include "operation.svh"
/*
Module      : writeback_buffer_controller
Description : The output of the MM_WO instruction has the dimension (BLEN, BLEN). However, writing to the Vector SRAM requires a buffer to accumulate data until the dimension (MLEN, BLEN) is reached, at which point the data is written to the SRAM together.
*/


module writeback_buffer_controller #(
    parameter int unsigned BLEN = 4,
    parameter int unsigned MLEN = 4,
    parameter int unsigned ADDR_WIDTH = 16

) (
    input logic clk,
    input logic rst,
    input logic writeback_buffer_enable,
    input logic  [ADDR_WIDTH-1:0] buffer_addr_in,
    output logic [ADDR_WIDTH-1:0] buffer_addr_out,
    output logic buffer_addr_valid,
    input logic  buffer_addr_ready
);

localparam int BUFFER_AMOUNT = MLEN / BLEN;
localparam int BUFFER_ADDR_WIDTH = $clog2(BUFFER_AMOUNT + 1);
logic [BUFFER_ADDR_WIDTH-1:0] buffer_addr_counter;


always_ff @(posedge clk or posedge rst) begin
    if (rst) begin
        buffer_addr_counter <= '0;
        buffer_addr_out <= '0;
        buffer_addr_valid <= 1'b0;
    end else begin
        if (writeback_buffer_enable) begin
            if (buffer_addr_counter < BUFFER_AMOUNT) begin
                buffer_addr_out <= {{ADDR_WIDTH-BUFFER_ADDR_WIDTH{1'b0}}, buffer_addr_counter};
                buffer_addr_valid <= 1'b1;
                buffer_addr_counter <= buffer_addr_counter + 1;
            end else begin
                buffer_addr_valid <= 1'b0;
                buffer_addr_counter <= '0;
                buffer_addr_out <= '0;
            end
        end else begin
            buffer_addr_valid <= 1'b0;
        end
    end
end



endmodule