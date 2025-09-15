`timescale 1ns / 1ps

/*
Module      : Floating Point Vector Shift Unit
Timing      : Sequential Logic
Description : Shifts the input vector by a specified amount.
*/


module fp_vec_shift #(
    parameter int VLEN   = 32,
    parameter int BITWIDTH = 16,
    parameter bool RIGHT_SHIFT = 1, // 1 for right shift, 0 for left shift
    localparam int SHIFT_WIDTH = $clog2(VLEN)
)(
    input   logic clk,
    input   logic rst,
    input   logic v_in_valid,
    input   logic [VLEN-1:0][BITWIDTH-1:0]  v_in,
    input   logic [SHIFT_WIDTH-1:0]         shift_amount,
    output  logic v_out_valid,
    output  logic [VLEN-1:0][BITWIDTH-1:0]  v_out
);

generate
    if (!RIGHT_SHIFT) begin : left_shift_logic
        // Left shift logic
        always_ff @(posedge clk) begin
            if (rst) begin
                v_out       <= '0;
                v_out_valid <= 1'b0;
            end else begin
                if (shift_amount < VLEN) begin
                    v_out <= {{shift_amount{ {BITWIDTH{1'b0}} }}, v_in[VLEN-1:shift_amount]};
                end else begin
                    v_out <= '0; // If shift amount exceeds VLEN, output zero vector
                end
                v_out_valid <= v_in_valid;
            end
        end
    end else begin : right_shift_logic
        // Right shift logic
        always_ff @(posedge clk) begin
            if (rst) begin
                v_out       <= '0;
                v_out_valid <= 1'b0;
            end else begin
                if (shift_amount < VLEN) begin
                    v_out <= {v_in[VLEN-1:shift_amount], {shift_amount{ {BITWIDTH{1'b0}} }}};
                end else begin
                    v_out <= '0; // If shift amount exceeds VLEN, output zero vector
                end
                v_out_valid <= v_in_valid;
            end
        end
    end
endgenerate

endmodule
