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
  logic [DATA_WIDTH - 1:0] data_out;
  always_ff @(posedge clk) begin
    if (rst) begin
      data_out <= 0;
    // end else if (stall) begin
    //   data_out <= data_out;
    end else begin
      data_out <= data_in;
    end
  end
endmodule
//   logic [DATA_WIDTH - 1:0] data_reg[REG_N-1:0];
//   for (genvar i = 0; i < REG_N; i++) begin
//     always_ff @(posedge clk) begin
//       if (rst) begin
//         data_reg[i] <= 0;
//       end else if (stall) begin
//         data_reg[i] <= data_reg[i];
//       end else if (i == 0) begin
//         data_reg[i] <= data_in;
//       end else begin
//         data_reg[i] <= data_reg[i-1];
//       end
//     end
//   end
//   assign data_out = data_reg[REG_N-1];
// endmodule