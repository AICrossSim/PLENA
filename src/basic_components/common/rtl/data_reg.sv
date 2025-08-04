`timescale 1ns / 1ps

module data_reg #(
  parameter DATA_WIDTH = 8, 
  parameter REG_N = 100
)(
  input logic clk,
  input logic rst,
  input logic stall,
  input logic [DATA_WIDTH - 1:0] data_in,
  output logic [DATA_WIDTH - 1:0] data_out
);
  always_ff @(posedge clk) begin
    if (rst) begin
      data_out <= 0;
    end else begin
      data_out <= data_in;
    end
  end
endmodule