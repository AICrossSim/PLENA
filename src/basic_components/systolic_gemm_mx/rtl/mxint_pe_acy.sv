module mxint_default_pe #(
    parameter int MX_L_INT_WIDTH      = 4,
    parameter int MX_T_INT_WIDTH      = 4,
    parameter int MXINT_SCALE_WIDTH   = 8,
    parameter int ACC_FP_EXP_WIDTH    = 8,
    parameter int ACC_FP_MANT_WIDTH   = 7
)(
    input  logic clk,
    input  logic rst,
    input  logic clear_accumulator,

    input  logic [MX_T_INT_WIDTH - 1 : 0]      in_top_element,
    input  logic [MXINT_SCALE_WIDTH - 1 : 0]   in_top_scale,
    input  logic                               system_top_valid,

    input  logic [MX_L_INT_WIDTH - 1 : 0]      in_left_element,
    input  logic [MXINT_SCALE_WIDTH - 1 : 0]   in_left_scale,
    input  logic                               system_left_valid,

    input  logic  mult_valid,
    output logic  mult_ready,

    output logic [MX_T_INT_WIDTH - 1 : 0]      out_bottom_element,
    output logic [MXINT_SCALE_WIDTH - 1 : 0]   out_bottom_scale,

    output logic [MX_L_INT_WIDTH - 1 : 0]      out_right_element,
    output logic [MXINT_SCALE_WIDTH - 1 : 0]   out_right_scale,

    output logic [MX_L_INT_WIDTH - 1 : 0]      out_int,
    output logic [MXINT_SCALE_WIDTH - 1 : 0]   out_scale,
    output logic                               out_valid,
    input  logic                               out_ready
);

    localparam int PROD_INT_WIDTH = MX_T_INT_WIDTH + MX_L_INT_WIDTH;
    localparam int ACC_INT_WIDTH  = 32;

    wire signed [MX_T_INT_WIDTH-1:0]    top_int_s  = in_top_element;
    wire signed [MX_L_INT_WIDTH-1:0]    left_int_s = in_left_element;

    wire signed [MXINT_SCALE_WIDTH-1:0] top_exp_s  = in_top_scale;
    wire signed [MXINT_SCALE_WIDTH-1:0] left_exp_s = in_left_scale;

    always_ff @(posedge clk) begin
        if (rst) begin
            out_bottom_element <= '0;
            out_bottom_scale   <= '0;
            out_right_element  <= '0;
            out_right_scale    <= '0;
        end else begin
            out_bottom_element <= in_top_element;
            out_bottom_scale   <= in_top_scale;
            out_right_element  <= in_left_element;
            out_right_scale    <= in_left_scale;
        end
    end

    (* use_dsp = "yes" *) wire signed [PROD_INT_WIDTH-1:0] prod_int = top_int_s * left_int_s;
    wire signed [MXINT_SCALE_WIDTH:0] merged_exp = top_exp_s + left_exp_s;

    function automatic signed [ACC_INT_WIDTH-1:0] shift_with_signed_exp;
        input signed [PROD_INT_WIDTH-1:0] val;
        input signed [MXINT_SCALE_WIDTH:0] exp_s;
        reg   signed [ACC_INT_WIDTH-1:0] ext_val;
        begin
            ext_val = {{(ACC_INT_WIDTH-PROD_INT_WIDTH){val[PROD_INT_WIDTH-1]}}, val};
            if (exp_s >= 0)
                shift_with_signed_exp = ext_val <<< exp_s;
            else
                shift_with_signed_exp = ext_val >>> (-exp_s);
        end
    endfunction

    wire signed [ACC_INT_WIDTH-1:0] prod_scaled = shift_with_signed_exp(prod_int, merged_exp);

    logic signed [ACC_INT_WIDTH-1:0] acc_q, acc_d;

    always_comb begin
        if (clear_accumulator) acc_d = '0;
        else if (mult_valid && system_top_valid && system_left_valid)
            acc_d = acc_q + prod_scaled;
        else
            acc_d = acc_q;
    end

    always_ff @(posedge clk) begin
        if (rst) acc_q <= '0;
        else     acc_q <= acc_d;
    end

    assign mult_ready = 1'b1;

    function automatic [ACC_INT_WIDTH-1:0] abs_signed;
        input signed [ACC_INT_WIDTH-1:0] v;
        begin
            abs_signed = v[ACC_INT_WIDTH-1] ? (~v + 1'b1) : v;
        end
    endfunction

    function automatic int msb_pos_abs;
        input [ACC_INT_WIDTH-1:0] v_abs;
        int i;
        begin
            msb_pos_abs = 0;
            for (i = ACC_INT_WIDTH-1; i >= 0; i=i-1) begin
                if (v_abs[i]) begin
                    msb_pos_abs = i;
                    break;
                end
            end
        end
    endfunction

    function automatic signed [31:0] sat_to_width;
        input signed [ACC_INT_WIDTH-1:0] v_in;
        input int W;
        reg signed [31:0] vmax, vmin;
        reg signed [31:0] vin32;
        begin
            vmax = (32'sd1 <<< (W-1)) - 1;
            vmin = - (32'sd1 <<< (W-1));
            vin32 = v_in[31:0];
            if (vin32 > vmax) sat_to_width = vmax;
            else if (vin32 < vmin) sat_to_width = vmin;
            else sat_to_width = vin32;
        end
    endfunction

    function automatic int compute_shr_to_fit;
        input signed [ACC_INT_WIDTH-1:0] v_in;
        input int W;
        reg [ACC_INT_WIDTH-1:0] v_abs;
        int msbpos, maxpos;
        begin
            v_abs  = abs_signed(v_in);
            msbpos = msb_pos_abs(v_abs);
            maxpos = W - 2;
            if (v_in == '0) compute_shr_to_fit = 0;
            else if (msbpos <= maxpos) compute_shr_to_fit = 0;
            else compute_shr_to_fit = (msbpos - maxpos);
        end
    endfunction

logic signed [ACC_INT_WIDTH-1:0] acc_for_out;
logic [MX_L_INT_WIDTH-1:0]       out_int_r;
logic signed [MXINT_SCALE_WIDTH-1:0] out_scale_r;
logic out_valid_r;
int   shr_amt;
logic signed [ACC_INT_WIDTH-1:0] acc_shifted;
logic signed [31:0]              sat_val;

always_ff @(posedge clk) begin
  if (rst) begin
    out_int_r   <= '0;
    out_scale_r <= '0;
    out_valid_r <= 1'b0;
  end else begin
    if (mult_valid && system_top_valid && system_left_valid) begin
      acc_for_out = (mult_valid && system_top_valid && system_left_valid) ? (acc_q + prod_scaled) : acc_q;
      shr_amt = compute_shr_to_fit(acc_for_out, MX_L_INT_WIDTH);
      acc_shifted = (shr_amt > 0) ? (acc_for_out >>> shr_amt) : acc_for_out;
      sat_val     = sat_to_width(acc_shifted, MX_L_INT_WIDTH);
      out_int_r   <= sat_val[MX_L_INT_WIDTH-1:0];
      out_scale_r <= -$signed(shr_amt);
      out_valid_r <= 1'b1;
    end else if (out_ready) begin
      out_valid_r <= 1'b0;
    end
  end
end

assign out_int   = out_int_r;
assign out_scale = out_scale_r;
assign out_valid = out_valid_r;

endmodule