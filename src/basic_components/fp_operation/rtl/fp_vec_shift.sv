`timescale 1ns / 1ps

/*
Module      : Floating Point Vector Shift Unit
Timing      : Sequential Logic
Description : Shifts the input vector by a specified amount.
*/


module fp_vec_shift #(
    parameter int VLEN         = 256,
    parameter int BITWIDTH     = 16,
    parameter bit RIGHT_SHIFT  = 1
)(
    input  logic                               clk,
    input  logic                               rst,   // active-high sync
    input  logic                               v_in_valid,
    input  logic [VLEN-1:0][BITWIDTH-1:0]      v_in,
    input  logic [$clog2(VLEN)-1:0]            shift_amount,  // lane shift
    output logic                               v_out_valid,
    output logic [VLEN-1:0][BITWIDTH-1:0]      v_out
);

    localparam int SHIFT_W = (VLEN <= 1) ? 1 : $clog2(VLEN);
    localparam int STAGES  = (VLEN <= 1) ? 1 : $clog2(VLEN);
    localparam logic [SHIFT_W-1:0] MAX_SHIFT = VLEN-1;

    // Pipeline state
    logic [VLEN-1:0][BITWIDTH-1:0] data_pipe   [0:STAGES];
    logic [SHIFT_W-1:0]            shift_pipe  [0:STAGES];
    logic                          valid_pipe  [0:STAGES];
    logic                          ge_vlen_pipe[0:STAGES];

    // Stage 0: input register
    always_ff @(posedge clk) begin
        if (rst) begin
            data_pipe[0]    <= '0;
            shift_pipe[0]   <= '0;
            valid_pipe[0]   <= 1'b0;
            ge_vlen_pipe[0] <= 1'b0;
        end else begin
            data_pipe[0]    <= v_in;
            shift_pipe[0]   <= shift_amount;
            valid_pipe[0]   <= v_in_valid;
            ge_vlen_pipe[0] <= (shift_amount > MAX_SHIFT);
        end
    end

    // Stages: one clock each
    genvar s;
    generate
        for (s = 0; s < STAGES; s++) begin : gen_stage
            localparam int STEP = (1 << s);
            logic [VLEN-1:0][BITWIDTH-1:0] next_data;

            // Build next_data combinationally (OK to use loops with blocking '=' here)
            if (!RIGHT_SHIFT) begin : left_shift_logic
                always_comb begin
                    if (shift_pipe[s][s]) begin
                        next_data = '0;
                        for (int i = 0; i < VLEN; i++) begin
                            if (i >= STEP)
                                next_data[i] = data_pipe[s][i - STEP];
                        end
                    end else begin
                        next_data = data_pipe[s]; // pass-through
                    end
                end
            end else begin : right_shift_logic
                always_comb begin
                    if (shift_pipe[s][s]) begin
                        next_data = '0;
                        for (int i = 0; i < VLEN; i++) begin
                            if ((i + STEP) < VLEN)
                                next_data[i] = data_pipe[s][i + STEP];
                        end
                    end else begin
                        next_data = data_pipe[s]; // pass-through
                    end
                end
            end

            // Register this stage (single nonblocking assignment; no <= inside loops)
            always_ff @(posedge clk) begin
                if (rst) begin
                    data_pipe[s+1]    <= '0;
                    shift_pipe[s+1]   <= '0;
                    valid_pipe[s+1]   <= 1'b0;
                    ge_vlen_pipe[s+1] <= 1'b0;
                end else begin
                    data_pipe[s+1]    <= next_data;
                    shift_pipe[s+1]   <= shift_pipe[s];
                    valid_pipe[s+1]   <= valid_pipe[s];
                    ge_vlen_pipe[s+1] <= ge_vlen_pipe[s];
                end
            end
        end
    endgenerate

    // Output register (guard overshifts for non-power-of-two VLEN)
    always_ff @(posedge clk) begin
        if (rst) begin
            v_out       <= '0;
            v_out_valid <= 1'b0;
        end else begin
            v_out       <= ge_vlen_pipe[STAGES] ? '0 : data_pipe[STAGES];
            v_out_valid <= valid_pipe[STAGES];
        end
    end

endmodule
