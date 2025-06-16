`timescale 1ns / 1ps

module fp_rounding #(
    parameter LAYER_DIM = 3,
    parameter EXP_WIDTH = 3,
    parameter IN_MANT_WIDTH = 8,
    parameter OUT_MANT_WIDTH = 3
) (
    input  [ IN_WIDTH - 1:0] data_in [LAYER_DIM - 1:0],
    output [OUT_WIDTH - 1:0] data_out[LAYER_DIM - 1:0]
);
  for (genvar i = 0; i < LAYER_DIM; i++) begin : parallel_round
    fp_round #(
        .EXP_WIDTH(EXP_WIDTH),
        .IN_MANT_WIDTH(IN_MANT_WIDTH),
        .OUT_MANT_WIDTH(OUT_MANT_WIDTH)
    ) fr_inst (
        .data_in (data_in[i]),
        .data_out(data_out[i])
    );
  end

endmodule
