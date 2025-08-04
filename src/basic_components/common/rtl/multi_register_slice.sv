`timescale 1ns / 1ps
module multi_register_slice #(
    parameter DATA_WIDTH = 8,
    parameter N = 2
) (
    input logic clk,
    input logic rst,

    input  logic [DATA_WIDTH-1:0] data_in,
    input  logic  data_in_valid,
    output logic  data_in_ready,

    output logic [DATA_WIDTH-1:0] data_out,
    output logic  data_out_valid,
    input  logic  data_out_ready
);

  logic [DATA_WIDTH-1:0] data_array [N-1:0];
  logic data_valid_array [N-1:0];
  logic data_ready_array [N-1:0];

  assign data_array[0] = data_in;
  assign data_valid_array[0] = data_in_valid;
  assign data_in_ready = data_ready_array[0];

  assign data_out = data_array[N-1];
  assign data_out_valid = data_valid_array[N-1];
  assign data_ready_array[N-1] = data_out_ready;


  for (genvar i = 0; i < N-1; i++) begin : gen_register_slice
    register_slice #(
        .DATA_WIDTH(DATA_WIDTH)
    ) register_slice_inst (
        .clk(clk),
        .rst(rst),
        .data_in(data_array[i]),
        .data_in_valid(data_valid_array[i]),
        .data_in_ready(data_ready_array[i]),
        .data_out(data_array[i+1]),
        .data_out_valid(data_valid_array[i+1]),
        .data_out_ready(data_ready_array[i+1])
    );
  end
endmodule
