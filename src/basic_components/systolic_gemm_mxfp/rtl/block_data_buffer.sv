`timescale 1ns / 1ps
`include "operation.svh"
`include "configuration.svh"
`include "precision.svh"

/*
Module      : Partial Result Buffer for Matrix Machine V2
Timing      : Sequential, Takes x cycles to compute the dot product
Description : This module will buffer [Batch, Batch] result every time and output [MLEN, 1] every time.
            : |a, b| |e, f|
              |c, d| |g, h|
            : will output [a, b, e, f] every time.
            : Note, the address here is the column index, controlling the inserted position of the block data.
*/

module block_data_buffer #(
    parameter M = 4,
    parameter K = 8,
    parameter N = 4,
    parameter FP_EXP_WIDTH = 8,
    parameter FP_MANT_WIDTH = 7,
    localparam ACC_NUM = K / M,
    localparam ACC_ADDR_WIDTH = $clog2(ACC_NUM)
)(
    input   logic clk,
    input   logic rst,
    // Input, accepting [M, N] partial results
    input   logic [M-1:0][N-1:0][FP_EXP_WIDTH + FP_MANT_WIDTH : 0] block_data_in,
    input   logic [ACC_ADDR_WIDTH-1:0] acc_waddr,
    input   logic acc_waddr_valid,
    output  logic acc_waddr_ready,
    input   logic wait_for_output,
    input   logic block_data_valid,
    output  logic block_data_ready,
    // Output, outputting [K] results for M cycles
    output  logic [K-1:0][FP_EXP_WIDTH + FP_MANT_WIDTH : 0] unrolled_data_out,
    output  logic unrolled_data_out_valid,
    input   logic unrolled_data_out_ready
);

initial begin
    assert (M == N) else $fatal("M must be equal to N for this block data buffer.");
end

  logic write_to_buffer_valid, write_to_buffer_ready;

  join2 #() join_inst (
      .data_in_ready ({block_data_ready, acc_waddr_ready}),
      .data_in_valid ({block_data_valid, acc_waddr_valid}),
      .data_out_valid(write_to_buffer_valid),
      .data_out_ready(write_to_buffer_ready)
  );

  logic [M : 0] load_out_counter;
  logic [M-1:0][K-1:0][FP_EXP_WIDTH + FP_MANT_WIDTH : 0] buffered_data;
  logic start_to_load_out;

  always_ff @(posedge clk or posedge rst) begin
      if (rst) begin
          load_out_counter <= 'b0;
          unrolled_data_out_valid <= 1'b0;
          write_to_buffer_ready <= 1'b0;
          buffered_data <= 'b0;
          start_to_load_out <= 1'b0;
      end else begin
          write_to_buffer_ready <= 1'b1;
          if (write_to_buffer_valid) begin
              // Load the block data into the buffer
              for (int i = 0; i < M; i++) begin
                  buffered_data[i][acc_waddr * N +: N] <= block_data_in[i];
              end
          end

          if (acc_waddr == ACC_NUM - 1 && write_to_buffer_valid && wait_for_output) begin
              load_out_counter <= 'b0;
              start_to_load_out <= 1'b1;
          end else if (load_out_counter == M) begin
              unrolled_data_out_valid <= 1'b0;
              load_out_counter        <= 'b0;
              start_to_load_out       <= 1'b0;
              unrolled_data_out       <= 'b0;
          end else if (start_to_load_out & unrolled_data_out_ready) begin
              unrolled_data_out_valid <= 1'b1;
              unrolled_data_out <= buffered_data[load_out_counter];
              load_out_counter  <= load_out_counter + 1;
          end
      end
  end


endmodule