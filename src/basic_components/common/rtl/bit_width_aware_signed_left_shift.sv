`timescale 1ns / 1ps

module bit_width_aware_signed_left_shift #(
    parameter IN_WIDTH = 8,
    parameter OUT_WIDTH = 8,
    parameter SHIFT_WIDTH = 8
) (
    input  logic signed [IN_WIDTH-1:0] in_data,
    input  logic signed [SHIFT_WIDTH-1:0] shift_amt,
    output logic [OUT_WIDTH-1:0] out_data
);

  logic in_data_sign;
  logic [IN_WIDTH-2:0] abs_in_data;
  logic [OUT_WIDTH-1:0] abs_out_data;

  logic shift_sign;
  logic [SHIFT_WIDTH-1:0] abs_shift_value;

  logic [OUT_WIDTH-1:0] data_right_shift;
  logic [OUT_WIDTH-1:0] data_left_shift;

  assign in_data_sign = in_data[IN_WIDTH-1];
  assign abs_in_data = in_data_sign ? ~in_data + 1 : in_data;

  assign shift_sign = shift_amt[SHIFT_WIDTH-1];
  assign abs_shift_value = (shift_sign) ? (~shift_amt + 1) : shift_amt;

  bit_width_aware_right_shift #(
    .IN_WIDTH(IN_WIDTH),
    .OUT_WIDTH(OUT_WIDTH),
    .SHIFT_WIDTH(SHIFT_WIDTH)
  ) bit_width_aware_right_shift_inst (
    .in_data(abs_in_data),
    .shift_amt(abs_shift_value),
    .out_data(data_right_shift)
  );

  bit_width_aware_left_shift #(
    .IN_WIDTH(IN_WIDTH),
    .OUT_WIDTH(OUT_WIDTH),
    .SHIFT_WIDTH(SHIFT_WIDTH)
  ) bit_width_aware_left_shift_inst (
    .in_data(abs_in_data),
    .shift_amt(abs_shift_value),
    .out_data(data_left_shift)
  );

  assign abs_out_data = (shift_sign) ? data_right_shift : data_left_shift;
  assign out_data = in_data_sign ? -abs_out_data : abs_out_data;
endmodule