
module bit_width_aware_right_shift #(
    parameter IN_WIDTH = 8,
    parameter OUT_WIDTH = 8,
    parameter SHIFT_WIDTH = 8
) (
    input  logic [IN_WIDTH-1:0] in_data,
    input  logic [SHIFT_WIDTH-1:0] shift_amt,
    output logic [OUT_WIDTH-1:0] out_data
);

  localparam SHIFT_DATA_WIDTH = IN_WIDTH + OUT_WIDTH - 1; // The maximum left shift value is out_width - 1

  localparam logic signed [OUT_WIDTH-1:0] MIN_VAL = -(2 ** (OUT_WIDTH - 1));
  localparam logic signed [OUT_WIDTH-1:0] MAX_VAL = (2 ** (OUT_WIDTH - 1)) - 1;

  logic [SHIFT_WIDTH - 1:0] abs_shift_value, real_shift_value;
  logic shift_sign;

  logic [SHIFT_DATA_WIDTH - 1:0] shift_data_list[SHIFT_DATA_WIDTH -1 : 0];
  logic [OUT_WIDTH - 1:0] clamped_out;

  enum {
    SHIFT_OUT_RANGE,
    SHIFT_IN_RANGE
  } mode;

  assign shift_sign = shift_amt[SHIFT_WIDTH-1];

  assign abs_shift_value = (shift_sign) ? (~shift_amt + 1) : shift_amt;
  assign real_shift_value = (abs_shift_value < SHIFT_DATA_WIDTH - 1) ? abs_shift_value : SHIFT_DATA_WIDTH - 1;

  // There is several things need to be considered
  always_comb begin
    if ((abs_shift_value >= OUT_WIDTH) && (shift_sign)) mode = SHIFT_OUT_RANGE;
    else mode = SHIFT_IN_RANGE;
  end

  for (genvar i = 0; i < SHIFT_DATA_WIDTH - 1; i++) begin
    always_comb begin
      shift_data_list[i] = (shift_value[SHIFT_WIDTH-1]) ? $signed(data_in) <<< i :
            $signed(data_in[i]) >>> j;
      end
  end

  signed_clamp #(
      .IN_WIDTH (SHIFT_DATA_WIDTH),
      .OUT_WIDTH(OUT_WIDTH)
    ) data_clamp (
        .in_data (shift_data_list[real_shift_value]),
        .out_data(clamped_out)
    );

  always_comb begin
    if (data_in == 0) data_out = 0;
    else
        case (mode)
          SHIFT_OUT_RANGE: data_out = (data_in[IN_WIDTH-1]) ? MIN_VAL : MAX_VAL;
          SHIFT_IN_RANGE: data_out = clamped_out;
          default: data_out = clamped_out;
        endcase
    end
  end
endmodule