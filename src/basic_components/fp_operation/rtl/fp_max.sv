`timescale 1ns / 1ps
/*
Module      : Floating Point Max (With Sign)
Timing      : Combinatorial Logic
Description : Compare two FP numbers with different exponents and signs.
              Returns the maximum of the two numbers.
              Output format: {sign, exp_out, mant_out}.
              No rounding.
Status      : Passed Simple Tests
*/

module fp_max #(
    parameter int EXP_WIDTH = 5,
    parameter int MANT_WIDTH = 10
)(
    input  logic clk,
    input  logic rst,
    input  logic data_in_valid,
    output logic data_in_ready,
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_a,  // {sign, exp, mant}
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_b,
    output logic data_out_valid,
    input  logic data_out_ready,
    output logic [EXP_WIDTH + MANT_WIDTH : 0] data_out
);

    // Bit field declarations
    logic sign_a, sign_b, sign_res;
    logic [EXP_WIDTH-1:0] exp_a, exp_b;
    logic [MANT_WIDTH-1:0] mant_a, mant_b;
    logic [EXP_WIDTH + MANT_WIDTH : 0] max_data;

    // Extract sign, exponent, mantissa
    assign sign_a = data_a[EXP_WIDTH + MANT_WIDTH];
    assign exp_a  = data_a[EXP_WIDTH + MANT_WIDTH - 1 : MANT_WIDTH];
    assign mant_a = data_a[MANT_WIDTH-1:0];

    assign sign_b = data_b[EXP_WIDTH + MANT_WIDTH];
    assign exp_b  = data_b[EXP_WIDTH + MANT_WIDTH -1 : MANT_WIDTH];
    assign mant_b = data_b[MANT_WIDTH-1:0];

    // Compare signs and exponents
    always_comb begin
        if (sign_a == sign_b) begin
            if (exp_a > exp_b) begin
                max_data = data_a;
            end else if (exp_a < exp_b) begin
                max_data = data_b;
            end else begin
                if (mant_a > mant_b) begin
                    max_data = data_a;
                end else begin
                    max_data = data_b;
                end
            end
        end else begin
            if (sign_a == 1'b0) begin
                max_data = data_a;
            end else begin
                max_data = data_b;
            end
        end
    end

    skid_buffer #(
        .DATA_WIDTH(EXP_WIDTH + MANT_WIDTH + 1)
    ) buffer_max (
        .clk(clk),
        .rst(rst),
        .data_in(max_data),
        .data_in_valid(data_in_valid),
        .data_in_ready(data_in_ready),
        .data_out(data_out),
        .data_out_valid(data_out_valid),
        .data_out_ready(data_out_ready)
    );


endmodule