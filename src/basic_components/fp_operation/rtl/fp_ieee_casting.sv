`timescale 1ns / 1ps
/*
Module      : fp_ieee_casting
Timing      : Combinatorial Logic
Description : FP_IEEE_Casting
            - Performs casting between IEEE floating-point formats.
            - Only **reducing** bit width is allowed.
            - This operation is **lossy**: For instance, to cast a value like xxxx to x000, we **first truncate/floor** to xxx0, then apply **round-to-nearest-even**.
*/

module fp_ieee_casting #(
    parameter   IN_EXP_WIDTH = 5,
    parameter   IN_MANT_WIDTH = 10,
    parameter   OUT_EXP_WIDTH = 5,
    parameter   OUT_MANT_WIDTH = 8
)(
    input  logic [IN_EXP_WIDTH + IN_MANT_WIDTH : 0] data_in,  // {sign, exp, mant}
    output logic [OUT_EXP_WIDTH + OUT_MANT_WIDTH : 0] data_out
);
    initial begin
        assert (IN_EXP_WIDTH >= OUT_EXP_WIDTH)
            else $error("IN_EXP_WIDTH must be greater than or equal to OUT_EXP_WIDTH");
        assert (IN_MANT_WIDTH >= OUT_MANT_WIDTH)
            else $error("IN_MANT_WIDTH must be greater than or equal to OUT_MANT_WIDTH");
    end

    logic [OUT_EXP_WIDTH + IN_MANT_WIDTH : 0] intermediate_data;

    fp_ieee_exponent_casting #(
        .IN_EXP_WIDTH(IN_EXP_WIDTH),
        .OUT_EXP_WIDTH(OUT_EXP_WIDTH),
        .MANT_WIDTH(IN_MANT_WIDTH)
    ) fp_ieee_exponent_casting_inst (
        .data_in(data_in),
        .data_out(intermediate_data)
    );

    fp_ieee_mantissa_casting #(
        .EXP_WIDTH(OUT_EXP_WIDTH),
        .IN_MANT_WIDTH(IN_MANT_WIDTH),
        .OUT_MANT_WIDTH(OUT_MANT_WIDTH)
    ) fp_ieee_mantissa_casting_inst (
        .data_in(intermediate_data),
        .data_out(data_out)
    );
endmodule

module fp_ieee_exponent_casting #(
    parameter   IN_EXP_WIDTH = 5,
    parameter   OUT_EXP_WIDTH = 5,
    parameter   MANT_WIDTH = 10
)(
    input  logic [IN_EXP_WIDTH + MANT_WIDTH : 0] data_in,  // {sign, exp, mant}
    output logic [OUT_EXP_WIDTH + MANT_WIDTH : 0] data_out
);

    initial begin
        assert (IN_EXP_WIDTH >= OUT_EXP_WIDTH)
            else $error("IN_EXP_WIDTH must be greater than or equal to OUT_EXP_WIDTH");
    end

    localparam IN_BIAS = (1 << (IN_EXP_WIDTH - 1)) - 1;
    localparam OUT_BIAS = (1 << (OUT_EXP_WIDTH - 1)) - 1;

    localparam SHIFT_EXP = OUT_BIAS - IN_BIAS;

    // if 1 - OUT_BIAS <=in_exp - IN_BIAS <= 2**(OUT_EXP_WIDTH) - 1 - OUT_BIAS
    localparam EXP_UPPER_BOUND = 2**(OUT_EXP_WIDTH) - 1 - OUT_BIAS + IN_BIAS;
    localparam EXP_LOWER_BOUND = 1 - OUT_BIAS + IN_BIAS;

    logic [IN_EXP_WIDTH - 1:0] in_exp;
    logic [OUT_EXP_WIDTH - 1:0] out_exp;

    assign in_exp = data_in[IN_EXP_WIDTH + MANT_WIDTH - 1:MANT_WIDTH];
    assign out_exp = in_exp - SHIFT_EXP;

    always_comb begin
        if (in_exp < EXP_LOWER_BOUND) begin
            data_out = {1'b0, {OUT_EXP_WIDTH{1'b0}}, {MANT_WIDTH{1'b0}}};
        end
        else if (in_exp > EXP_UPPER_BOUND) begin
            data_out = {data_in[IN_EXP_WIDTH + MANT_WIDTH], {(OUT_EXP_WIDTH-1){1'b1}}, 1'b0, {MANT_WIDTH{1'b1}}};
        end
        else begin
            data_out = {data_in[IN_EXP_WIDTH + MANT_WIDTH], out_exp, data_in[MANT_WIDTH - 1:0]};
        end
    end

endmodule

module fp_ieee_mantissa_casting #(
    parameter   EXP_WIDTH = 5,
    parameter   IN_MANT_WIDTH = 10,
    parameter   OUT_MANT_WIDTH = 8
)(
    input  logic [EXP_WIDTH + IN_MANT_WIDTH : 0] data_in,  // {sign, exp, mant}
    output logic [EXP_WIDTH + OUT_MANT_WIDTH : 0] data_out
);
    initial begin
        assert (IN_MANT_WIDTH >= OUT_MANT_WIDTH)
            else $error("IN_MANT_WIDTH must be greater than or equal to OUT_MANT_WIDTH");
    end

    logic [IN_MANT_WIDTH - 1:0] in_mant;
    logic [OUT_MANT_WIDTH - 1:0] out_mant;

    assign in_mant = data_in[IN_MANT_WIDTH - 1:0];

    round_to_nearest_even #(
        .IN_WIDTH(IN_MANT_WIDTH),
        .OUT_WIDTH(OUT_MANT_WIDTH)
    ) round_to_nearest_even_inst (
        .data_in(in_mant),
        .data_out(out_mant)
    );
    assign data_out = {data_in[EXP_WIDTH + IN_MANT_WIDTH:IN_MANT_WIDTH], out_mant};
endmodule


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