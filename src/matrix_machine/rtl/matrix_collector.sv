`timescale 1ns / 1ps

/*
Module      : Matrix Input Collect Module
Timing      : Sequential, Takes MLEN//Collect_Dim cycles to prepared the output matrix in unpacked array format.
Description : This module accumulate the matrix by accepting [MLEN, Collect_Dim] 
             : data in each cycle and output the matrix in unpacked array format.
             : The output matrix is ready when the input is valid and the output is ready.
             : The input data is collected until the number of cycles reaches MLEN // Collect_Dim.
Status      : Pass Simple Test
*/


module matrix_collector #(
    parameter int DATA_WIDTH = 32,
    parameter int MLEN       = 64,
    parameter int Collect_Dim = 8
)(
    input  logic                                clk,
    input  logic                                rst_n,
    input  logic                                clear,

    // Input port
    input  logic [Collect_Dim * DATA_WIDTH - 1 : 0]   in_data,
    input  logic                                in_valid,
    output logic                                in_ready,

    // Output port
    output logic [MLEN * DATA_WIDTH - 1 : 0]          out_matrix,
    output logic                                out_valid,
    input  logic                                out_ready
);

    localparam int NUM_CYCLES = MLEN / Collect_Dim;

    // Internal storage
    logic [$clog2(NUM_CYCLES + 1)-1:0] cycle_count;

    logic collecting;
    assign collecting = (cycle_count < NUM_CYCLES);
    assign in_ready   = collecting && (!out_valid || out_ready);

    // Flatten and register output matrix
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n || clear) begin
            cycle_count <= 'b0;
            out_valid   <= 1'b0;
        end else begin
            if (in_valid && in_ready) begin
                // Write incoming data into buffer
                for (int i = 0; i < Collect_Dim; i++) begin
                    out_matrix[(cycle_count * Collect_Dim + i) * DATA_WIDTH +: DATA_WIDTH] <= in_data[i*DATA_WIDTH +: DATA_WIDTH];
                end
                // If last cycle, prepare output matrix
                if (cycle_count == NUM_CYCLES - 1) begin
                    out_valid <= 1'b1;
                    cycle_count <= 'b0;
                end else begin
                    cycle_count <= cycle_count + 1;
                end
            end

            // Accepting output
            if (out_valid && out_ready) begin
                out_valid <= 1'b0;
            end
        end
    end

endmodule
