`timescale 1ns / 1ps
module bit_width_aware_right_shift #(
    parameter IN_WIDTH = 8,
    parameter OUT_WIDTH = 8,
    parameter SHIFT_WIDTH = 8
) (
    input  logic [IN_WIDTH-1:0] in_data,
    input  logic [SHIFT_WIDTH-1:0] shift_amt,
    output logic [OUT_WIDTH-1:0] out_data
);

  logic [IN_WIDTH - 1:0] shift_data_list[IN_WIDTH - 1:0];

  for (genvar i = 0; i < IN_WIDTH; i++) begin
    assign shift_data_list[i] = in_data >> i;
  end

  assign out_data = (shift_amt < IN_WIDTH) ? shift_data_list[shift_amt] : 0;

endmodule