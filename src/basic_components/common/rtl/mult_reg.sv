`timescale 1ns / 1ps
module mult_reg #(
  parameter DATA_WIDTH = 4,
  parameter REG_N = 1
)(
  input logic clk,
  input logic rst,
  input logic [DATA_WIDTH - 1:0] data_in,
  output logic [DATA_WIDTH - 1:0] data_out
);
  logic [DATA_WIDTH - 1:0] data_reg[REG_N-1:0];
  for (genvar i = 0; i < REG_N; i++) begin
    always_ff @(posedge clk) begin
      if (rst) begin
        data_reg[i] <= 0;
      end else if (i == 0) begin
        data_reg[i] <= data_in;
      end else begin
        data_reg[i] <= data_reg[i-1];
      end
    end
  end
  assign data_out = data_reg[REG_N-1];
endmodule