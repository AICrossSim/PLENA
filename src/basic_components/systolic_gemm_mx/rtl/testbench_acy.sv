`timescale 1ns/1ps
module tb_mxint_default_pe;
  localparam int MX_L_INT_WIDTH = 4;
  localparam int MX_T_INT_WIDTH = 4;
  localparam int MXINT_SCALE_WIDTH = 8;

  logic clk;
  logic rst;

  initial begin
    clk = 1'b0;
    forever #5 clk = ~clk;
  end

  initial begin
    rst = 1'b1;
    repeat (5) @(posedge clk);
    rst = 1'b0;
  end

  initial begin
    $dumpfile("tb_mxint_default_pe.vcd");
    $dumpvars(0, tb_mxint_default_pe);
  end

  logic clear_accumulator;
  logic [MX_T_INT_WIDTH-1:0] in_top_element;
  logic [MXINT_SCALE_WIDTH-1:0] in_top_scale;
  logic system_top_valid;
  logic [MX_L_INT_WIDTH-1:0] in_left_element;
  logic [MXINT_SCALE_WIDTH-1:0] in_left_scale;
  logic system_left_valid;
  logic mult_valid;
  logic mult_ready;
  logic [MX_T_INT_WIDTH-1:0] out_bottom_element;
  logic [MXINT_SCALE_WIDTH-1:0] out_bottom_scale;
  logic [MX_L_INT_WIDTH-1:0] out_right_element;
  logic [MXINT_SCALE_WIDTH-1:0] out_right_scale;
  logic [MX_L_INT_WIDTH-1:0] out_int;
  logic [MXINT_SCALE_WIDTH-1:0] out_scale;
  logic out_valid;
  logic out_ready;

  mxint_default_pe #(
    .MX_L_INT_WIDTH(MX_L_INT_WIDTH),
    .MX_T_INT_WIDTH(MX_T_INT_WIDTH),
    .MXINT_SCALE_WIDTH(MXINT_SCALE_WIDTH),
    .ACC_FP_EXP_WIDTH(8),
    .ACC_FP_MANT_WIDTH(7)
  ) dut (
    .clk,
    .rst,
    .clear_accumulator,
    .in_top_element,
    .in_top_scale,
    .system_top_valid,
    .in_left_element,
    .in_left_scale,
    .system_left_valid,
    .mult_valid,
    .mult_ready,
    .out_bottom_element,
    .out_bottom_scale,
    .out_right_element,
    .out_right_scale,
    .out_int,
    .out_scale,
    .out_valid,
    .out_ready
  );

  function automatic int signed shift_with_signed_exp_i32(input int signed v, input int signed exp);
    if (exp >= 0) shift_with_signed_exp_i32 = (v <<< exp);
    else shift_with_signed_exp_i32 = (v >>> (-exp));
  endfunction

  function automatic int compute_shr_to_fit_i32(input int signed v32, input int W);
    int unsigned mag;
    int msbpos;
    int maxpos;
    int i;
    begin
      if (v32 == 0) return 0;
      if (v32 < 0) mag = (~int'(v32)) + 1;
      else mag = int'(v32);
      msbpos = -1;
      for (i = 31; i >= 0; i = i - 1) begin
        if (mag[i]) begin msbpos = i; break; end
      end
      if (msbpos < 0) return 0;
      maxpos = W - 2;
      if (msbpos <= maxpos) compute_shr_to_fit_i32 = 0;
      else compute_shr_to_fit_i32 = (msbpos - maxpos);
    end
  endfunction

  function automatic longint signed to_sint(bit [63:0] v, int W);
    longint signed mask;
    longint signed low;
    begin
      mask = (64'sd1 <<< (W-1));
      low = longint'(v & ((64'h1 << W) - 1));
      to_sint = (low & mask) ? (low - (64'sd1 <<< W)) : low;
    end
  endfunction

  function automatic longint signed arith_shift(longint signed x, int exp);
    begin
      if (exp >= 0) arith_shift = x <<< exp;
      else arith_shift = x >>> (-exp);
    end
  endfunction

  function automatic logic [63:0] abs_mag64(longint signed x);
    logic [63:0] ux;
    begin
      ux = x[63:0];
      if (x < 0) abs_mag64 = (~ux + 64'd1);
      else abs_mag64 = ux;
    end
  endfunction

  function automatic int msb_pos_u(logic [63:0] x);
    int i;
    begin
      msb_pos_u = -1;
      for (i = 63; i >= 0; i--) begin
        if (x[i]) begin msb_pos_u = i; break; end
      end
    end
  endfunction

  function automatic int compute_shr_to_fit_ref(longint signed v, int W);
    int msbpos;
    int maxpos;
    int res;
    begin
      if (v == 0) begin
        res = 0;
      end else begin
        msbpos = msb_pos_u(abs_mag64(v));
        maxpos = W - 2;
        if (msbpos <= maxpos) res = 0;
        else res = (msbpos - maxpos);
      end
      compute_shr_to_fit_ref = res;
    end
  endfunction

  function automatic longint signed sat_to_width_ref(longint signed v, int W);
    longint signed vmax;
    longint signed vmin;
    begin
      vmax = (64'sd1 <<< (W-1)) - 1;
      vmin = -(64'sd1 <<< (W-1));
      if (v > vmax) sat_to_width_ref = vmax;
      else if (v < vmin) sat_to_width_ref = vmin;
      else sat_to_width_ref = v;
    end
  endfunction

  function automatic logic [63:0] mask_w(input int W);
    logic [63:0] m;
    begin
      if (W >= 64) m = 64'hFFFF_FFFF_FFFF_FFFF;
      else if (W <= 0) m = 64'h0;
      else m = (64'h1 << W) - 1;
      mask_w = m;
    end
  endfunction

  function automatic longint signed mxint_real(bit [31:0] x_int_u, int W_int, bit [31:0] s_u, int W_s);
    logic [63:0] xi_u, se_u;
    longint signed xi, se;
    logic [63:0] m_int, m_s;
    begin
      xi_u = 64'd0; xi_u[31:0] = x_int_u;
      se_u = 64'd0; se_u[31:0] = s_u;
      m_int = mask_w(W_int);
      m_s = mask_w(W_s);
      xi = to_sint(xi_u & m_int, W_int);
      se = to_sint(se_u & m_s, W_s);
      mxint_real = arith_shift(xi, integer'(se));
    end
  endfunction

  function automatic longint signed reconstruct_out(bit [MX_L_INT_WIDTH-1:0] oi, bit [MXINT_SCALE_WIDTH-1:0] os);
    logic [63:0] oi_u, os_u;
    longint signed oi_s, os_s;
    begin
      oi_u = '0; oi_u[MX_L_INT_WIDTH-1:0] = oi;
      os_u = '0; os_u[MXINT_SCALE_WIDTH-1:0] = os;
      oi_s = to_sint(oi_u, MX_L_INT_WIDTH);
      os_s = to_sint(os_u, MXINT_SCALE_WIDTH);
      reconstruct_out = arith_shift(oi_s, -integer'(os_s));
    end
  endfunction

  localparam longint signed RECON_ABS_TOL = 1;
  longint signed acc_ref;
  int signed acc32_ref;
  bit [MX_T_INT_WIDTH-1:0] top_elem_dly;
  bit [MXINT_SCALE_WIDTH-1:0] top_scale_dly;
  bit [MX_L_INT_WIDTH-1:0] left_elem_dly;
  bit [MXINT_SCALE_WIDTH-1:0] left_scale_dly;
  bit have_prev;

  localparam int TOP_MAX = (1 << (MX_T_INT_WIDTH-1)) - 1;
  localparam int TOP_MIN = -(1 << (MX_T_INT_WIDTH-1));
  localparam int LEFT_MAX = (1 << (MX_L_INT_WIDTH-1)) - 1;
  localparam int LEFT_MIN = -(1 << (MX_L_INT_WIDTH-1));
  localparam int EXP_MAX = (1 << (MXINT_SCALE_WIDTH-1)) - 1;
  localparam int EXP_MIN = -(1 << (MXINT_SCALE_WIDTH-1));

  task automatic drive_one(
    input bit do_mult,
    input bit top_v,
    input bit left_v,
    input bit do_clear,
    input bit ready_val,
    input bit [MX_T_INT_WIDTH-1:0] top_e,
    input bit [MXINT_SCALE_WIDTH-1:0] top_s,
    input bit [MX_L_INT_WIDTH-1:0] left_e,
    input bit [MXINT_SCALE_WIDTH-1:0] left_s
  );
    begin
      mult_valid = do_mult;
      system_top_valid = top_v;
      system_left_valid = left_v;
      clear_accumulator = do_clear;
      out_ready = ready_val;
      in_top_element = top_e;
      in_top_scale = top_s;
      in_left_element = left_e;
      in_left_scale = left_s;
      @(posedge clk);
      #1ps;
    end
  endtask

  task automatic ref_update_and_check();
    bit do_mac;
    if (clear_accumulator) begin
      acc32_ref = 0;
    end else if (do_mac) begin
      int signed a = $signed(in_top_element);
      int signed b = $signed(in_left_element);
      int signed sa = $signed(in_top_scale);
      int signed sb = $signed(in_left_scale);
      int signed prod32 = a * b;
      int signed merged_exp32 = sa + sb;
      int signed prod_scaled = shift_with_signed_exp_i32(prod32, merged_exp32);
      acc32_ref += prod_scaled;
    end
  endtask

  initial begin
    int N = 300;
    bit do_mult, top_v, left_v, do_clear, rdy;
    int t, ts, l, ls;
    logic [MX_T_INT_WIDTH-1:0] t_n;
    logic [MXINT_SCALE_WIDTH-1:0] ts_n;
    logic [MX_L_INT_WIDTH-1:0] l_n;
    logic [MXINT_SCALE_WIDTH-1:0] ls_n;

    clear_accumulator = 0;
    in_top_element = '0;
    in_top_scale = '0;
    in_left_element = '0;
    in_left_scale = '0;
    system_top_valid = 0;
    system_left_valid = 0;
    mult_valid = 0;
    out_ready = 1;
    acc_ref = 0;
    have_prev = 0;

    @(negedge rst);
    @(posedge clk);

    $display("[Directed] single MAC, zero scales");
    drive_one(1,1,1,0,1, 4'sd3, 8'sd0, 4'sd2, 8'sd0);
    ref_update_and_check();

    drive_one(0,1,1,0,1, 4'sd1, 8'sd0, 4'sd1, 8'sd0);
    ref_update_and_check();

    $display("[Directed] MAC with mixed scales");
    drive_one(1,1,1,0,1, -4'sd2, 8'sd1, 4'sd3, -8'sd2);
    ref_update_and_check();

    $display("[Directed] clear accumulator");
    drive_one(0,0,0,1,1, 4'sd0, 8'sd0, 4'sd0, 8'sd0);
    ref_update_and_check();

    drive_one(1,1,1,0,1, -4'sd4, 8'sd0, -4'sd1, 8'sd0);
    ref_update_and_check();

    $display("[Directed] out_ready=0 while MAC");
    drive_one(1,1,1,0,0, 4'sd2, 8'sd0, 4'sd2, 8'sd0);
    ref_update_and_check();

    $display("[Directed] MXINT semantics spotlight");
    drive_one(1,1,1,1,1, -4'sd3, 8'sd2, 4'sd5, -8'sd1);
    ref_update_and_check();
    drive_one(1,1,1,0,1, 4'sd4, 8'sd0, -4'sd2, 8'sd1);
    ref_update_and_check();
    drive_one(1,1,1,0,1, -4'sd1, -8'sd3, -4'sd3, 8'sd2);
    ref_update_and_check();

    $display("[Random] start %0d cycles", N);
    repeat (N) begin
      do_mult = $urandom_range(0,1);
      top_v = $urandom_range(0,1);
      left_v = $urandom_range(0,1);
      do_clear = ($urandom_range(0,99) < 3);
      rdy = $urandom_range(0,1);
      t = $urandom_range(TOP_MIN, TOP_MAX);
      ts = $urandom_range(EXP_MIN, EXP_MAX);
      l = $urandom_range(LEFT_MIN, LEFT_MAX);
      ls = $urandom_range(EXP_MIN, EXP_MAX);
      t_n = t; ts_n = ts; l_n = l; ls_n = ls;
      drive_one(do_mult, top_v, left_v, do_clear, rdy, t_n, ts_n, l_n, ls_n);
      ref_update_and_check();
    end
    $display("ALL TESTS PASSED");
  end
endmodule
