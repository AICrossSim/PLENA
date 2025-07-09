`timescale 1ns / 1ps
/*
Module      : round_to_nearest_even
Timing      : Combinatorial Logic
Description : Round to nearest even
            - Rounds the input data to the nearest even number.
*/
module round_to_nearest_even #(
    parameter IN_WIDTH = 8,
    parameter OUT_WIDTH = 3
) (
    input  logic [ IN_WIDTH - 1:0] data_in,
    output logic [OUT_WIDTH - 1:0] data_out
);
  initial begin
    assert (IN_WIDTH >= OUT_WIDTH)
      else $error("IN_WIDTH must be greater than or equal to OUT_WIDTH");
  end

  logic [2:0] lsb_below;
  logic carry_in;

  logic [OUT_WIDTH:0] rounded_out_data;
  // get the x.xx .xx means extra bit
  always_comb begin
    lsb_below[2] = data_in[IN_WIDTH-OUT_WIDTH];
    lsb_below[1] = (IN_WIDTH-1 >= OUT_WIDTH) ? data_in[IN_WIDTH-OUT_WIDTH-1]     : 0;
    lsb_below[0] = (IN_WIDTH-2 >= OUT_WIDTH) ? data_in[IN_WIDTH-OUT_WIDTH-2]     : 0;
  end

  always_comb begin
      casez (lsb_below)
        // positives
        3'b?00:  carry_in = 1'b0;
        3'b?01:  carry_in = 1'b0;
        3'b010:  carry_in = 1'b0;
        3'b110:  carry_in = 1'b1;
        3'b?11:  carry_in = 1'b1;
        default: carry_in = 1'b0;
      endcase
  end

  always_comb begin
    rounded_out_data = data_in[IN_WIDTH-1:IN_WIDTH - OUT_WIDTH] + carry_in;
    if (rounded_out_data >= 1 << (OUT_WIDTH))
      data_out = {(OUT_WIDTH){1'b1}};
    else data_out = rounded_out_data[OUT_WIDTH-1:0];
  end
endmodule