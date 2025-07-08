`timescale 1ns / 1ps

module bit_width_aware_left_shift #(
    parameter IN_WIDTH = 8,
    parameter OUT_WIDTH = 8,
    parameter SHIFT_WIDTH = 8
) (
    input  logic [IN_WIDTH-1:0] in_data,
    input  logic [SHIFT_WIDTH-1:0] shift_amt,
    output logic [OUT_WIDTH-1:0] out_data
);

  localparam logic [OUT_WIDTH-1:0] MAX_VAL = (2 ** (OUT_WIDTH)) - 1;
  logic [OUT_WIDTH - 1:0] shift_data_list [OUT_WIDTH -1 : 0];
  logic [$clog2(IN_WIDTH+1)-1:0] leading_zero_count;

  for (genvar i = 0; i < OUT_WIDTH; i++) begin
    assign shift_data_list[i] = in_data << i;
  end

  clz_int #(
    .width_i(IN_WIDTH)
  ) clz_inst (
    .i_num(in_data),
    .o_lz(leading_zero_count)
  );
  
  always_comb begin
    if (in_data == 0) begin
      out_data = 0;
    end else begin
      if (IN_WIDTH + shift_amt - leading_zero_count > OUT_WIDTH) begin
        out_data = MAX_VAL;
      end else begin
        out_data = shift_data_list[shift_amt];
      end
    end
  end
endmodule