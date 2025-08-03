`timescale 1ns / 1ps

`include "configuration.svh"
`include "operation.svh"

/*
Module      : Vector ALU
Timing      : Combinatorial Logic
Description : This module includes elementwise vector computations
            : 1. Elementwise Add, 2. Elementwise Subtract, 3. Elementwise Multiply, 4. Elementwise Exponential
Status      : Under Development
*/

module fp_vector_element_alu #(
    parameter   EXP_WIDTH = 5,
    parameter   MANT_WIDTH = 10
)(
    input  logic clk,
    input  logic rst,
    input  V_ELEMENT_OP operation,

    input  logic data_in_valid,
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_a,
    input  logic [EXP_WIDTH + MANT_WIDTH : 0] data_b,


    output logic [EXP_WIDTH + MANT_WIDTH : 0] data_out,
    output logic data_out_valid,
    input  logic data_out_ready
);

    V_ELEMENT_OP recorded_operation;
    logic [EXP_WIDTH + MANT_WIDTH : 0] data_out_add, data_out_mul, data_out_exp, data_out_reci;
    logic [EXP_WIDTH + MANT_WIDTH : 0] negated_data_b;
    logic [EXP_WIDTH + MANT_WIDTH : 0] p1_data_a, p1_data_b;
    logic negated_en;


    logic p1_data_in_valid, p1_data_in_ready;
    logic mult_data_in_valid, mult_data_in_ready;
    logic mult_data_out_valid, mult_data_out_ready;
    logic add_data_in_valid, add_data_in_ready;
    logic add_data_out_valid, add_data_out_ready;
    logic exp_data_in_valid, exp_data_in_ready;
    logic exp_data_out_valid, exp_data_out_ready;
    logic reci_data_in_valid, reci_data_in_ready;
    logic reci_data_out_valid, reci_data_out_ready;

    always_ff @(posedge clk) begin
        if (rst) begin
            recorded_operation <= STALL_V_ELEMENT;
        end else begin
            if ( operation != STALL_V_ELEMENT) begin
                recorded_operation <= operation;
            end 
        end
    end

    register_slice #(
        .DATA_WIDTH((EXP_WIDTH + MANT_WIDTH + 1)*2)
    ) input_regstore_inst (
        .clk(clk),
        .rst(rst),
        .data_in        ({data_a, data_b}),
        .data_in_valid  (data_in_valid),
        .data_in_ready  (),
        .data_out       ({p1_data_a, p1_data_b}),
        .data_out_valid (p1_data_in_valid),
        .data_out_ready (p1_data_in_ready)
    );

    always_comb begin
        // Combinational module to flip the sign bit for FP subtraction
        negated_data_b = {~p1_data_b[EXP_WIDTH + MANT_WIDTH], p1_data_b[EXP_WIDTH + MANT_WIDTH - 1 : 0]};
        case (recorded_operation)
            ADD_V_ELEMENT: begin
                negated_en = 1'b0;
                add_data_in_valid = p1_data_in_valid;
                p1_data_in_ready = add_data_in_ready;
                data_out = data_out_add;
                data_out_valid = add_data_out_valid;
                add_data_out_ready = data_out_ready;
            end

            SUB_V_ELEMENT: begin
                negated_en = 1'b1;
                add_data_in_valid = p1_data_in_valid;
                p1_data_in_ready = add_data_in_ready;
                data_out = data_out_add;
                data_out_valid = add_data_out_valid;
                add_data_out_ready = data_out_ready;
            end

            MUL_V_ELEMENT: begin
                negated_en = 1'b0;
                mult_data_in_valid = p1_data_in_valid;
                p1_data_in_ready = mult_data_in_ready;
                data_out = data_out_mul;
                data_out_valid = mult_data_out_valid;
                mult_data_out_ready = data_out_ready;
            end

            EXP_V_ELEMENT: begin
                negated_en = 1'b0;
                exp_data_in_valid = p1_data_in_valid;
                p1_data_in_ready = exp_data_in_ready;
                data_out = data_out_exp;
                data_out_valid = exp_data_out_valid;
                exp_data_out_ready = data_out_ready;
            end

            RECI_V_ELEMENT: begin
                negated_en = 1'b0;
                reci_data_in_valid = p1_data_in_valid;
                p1_data_in_ready = reci_data_in_ready;
                data_out = data_out_reci; // RECI operation uses data_a as input
                data_out_valid = reci_data_out_valid;
                reci_data_out_ready = data_out_ready;
            end

            default: begin
                negated_en = 1'b0;
                data_out = '0; // Default case to avoid latches
            end

        endcase
    end

fp_cp_adder #(
    .EXP_WIDTH(EXP_WIDTH),
    .MANT_WIDTH(MANT_WIDTH)
) adder (
    .clk(clk),
    .rst(rst),
    .data_in_valid      (add_data_in_valid),
    .data_in_ready      (add_data_in_ready),
    .data_a             (p1_data_a),
    .data_b             (negated_en ? negated_data_b : p1_data_b),
    .data_out           (data_out_add),
    .data_out_valid     (add_data_out_valid),
    .data_out_ready     (add_data_out_ready)
);

fp_cp_mult #(
    .EXP_WIDTH(EXP_WIDTH),
    .MANT_WIDTH(MANT_WIDTH)
) multiplier (
    .clk(clk),
    .rst(rst),
    .data_in_valid      (mult_data_in_valid),
    .data_in_ready      (mult_data_in_ready),
    .data_a             (p1_data_a),
    .data_b             (p1_data_b),
    .data_out           (data_out_mul),
    .data_out_valid     (mult_data_out_valid),
    .data_out_ready     (mult_data_out_ready)
);

fp_fix_exp #(
    .EXP_WIDTH(EXP_WIDTH),
    .MANT_WIDTH(MANT_WIDTH)
) exp_unit (
    .clk(clk),
    .rst(rst),
    .data_in_valid      (exp_data_in_valid),
    .data_in_ready      (exp_data_in_ready),
    .data_in            (p1_data_a),
    .data_out           (data_out_exp),
    .data_out_valid     (exp_data_out_valid),
    .data_out_ready     (exp_data_out_ready)
);

fp_fix_reciprocal #(
    .EXP_WIDTH(EXP_WIDTH),
    .MANT_WIDTH(MANT_WIDTH)
) scalar_fp_reciprocal_init (
    .clk(clk),
    .rst(rst),
    .data_in_valid  (reci_data_in_valid),
    .data_in_ready  (reci_data_in_ready),
    .data_in        (p1_data_a),
    .data_out_valid (reci_data_out_valid),
    .data_out_ready (reci_data_out_ready),
    .data_out       (data_out_reci)
);


endmodule
